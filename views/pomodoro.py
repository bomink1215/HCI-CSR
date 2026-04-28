import flet as ft
import threading
import time
from components.ui import card, accent_btn, ghost_btn, mascot_widget

BG_BASE   = "#FFFFFF"
BG_CARD   = "#F4F6F8"
BG_CARD2  = "#EAECEF"
ACCENT    = "#00C9A7"
ACCENT_LT = "#D6F5EF"
ACCENT_DK = "#009E83"
DANGER    = "#FF5C5C"
WARNING   = "#FFB347"
PURPLE    = "#9B8FFF"
TEXT_PRI  = "#1A1D23"
TEXT_SEC  = "#5A6375"
TEXT_MUT  = "#9DA8B7"
BORDER    = "#E2E6EC"

MODES = {
    "focus":  {"label": "집중",     "minutes": 25, "color": ACCENT},
    "short":  {"label": "짧은 휴식", "minutes": 5,  "color": PURPLE},
    "long":   {"label": "긴 휴식",   "minutes": 15, "color": WARNING},
}

# 자동 전환 순서: 집중 → 짧은휴식 → 집중 → 짧은휴식 → ... → 4번마다 긴 휴식
SESSION_SEQUENCE = ["focus", "short", "focus", "short", "focus", "short", "focus", "long"]


def _beep(freq: int = 880, duration: float = 0.3, times: int = 2):
    """간단한 비프음 (크로스플랫폼)"""
    try:
        import math, wave, tempfile, os
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(tmp.name, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            for _ in range(times):
                data = b""
                for i in range(n_samples):
                    val = int(32767 * 0.5 * math.sin(2 * math.pi * freq * i / sample_rate))
                    data += val.to_bytes(2, 'little', signed=True)
                wf.writeframes(data)
        # 플랫폼별 재생
        import sys, subprocess
        if sys.platform == "win32":
            import winsound
            winsound.PlaySound(tmp.name, winsound.SND_FILENAME | winsound.SND_ASYNC)
        elif sys.platform == "darwin":
            subprocess.Popen(["afplay", tmp.name])
        else:
            subprocess.Popen(["aplay", "-q", tmp.name])
        time.sleep(duration * times + 0.1)
        os.unlink(tmp.name)
    except Exception:
        try:
            import sys
            if sys.platform == "win32":
                import winsound
                for _ in range(times):
                    winsound.Beep(freq, int(duration * 1000))
        except Exception:
            pass


class PomodoroView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.mode = "focus"
        self.running = False
        self.paused = False
        self.remaining = 25 * 60
        self.total = 25 * 60
        self._thread = None
        self.sessions_done = 0
        self.seq_idx = 0          # SESSION_SEQUENCE 인덱스
        self.auto_start = False
        self.sound_on = True
        self.history = [
            ("집중", "09:00", "09:25", "완료"),
            ("짧은 휴식", "09:25", "09:30", "완료"),
            ("집중", "09:30", "09:55", "완료"),
        ]

        self.time_ref      = ft.Ref()
        self.ring_ref      = ft.Ref()
        self.mode_label_ref = ft.Ref()
        self.btn_row_ref   = ft.Ref()
        self.session_dots_ref = ft.Ref()
        self.history_col_ref  = ft.Ref()
        self.play_icon_ref = ft.Ref()

    def _fmt(self, secs: int) -> str:
        return f"{secs // 60:02d}:{secs % 60:02d}"

    def _set_mode(self, mode: str, e=None):
        self.mode = mode
        cfg = MODES[mode]
        self.remaining = cfg["minutes"] * 60
        self.total = self.remaining
        self.running = False
        self.paused = False
        self._update_display()

    def _start_stop(self, e):
        if not self.running:
            self.running = True
            self.paused = False
            if self.play_icon_ref.current:
                self.play_icon_ref.current.value = "\ue047"  # pause icon
                self.play_icon_ref.current.update()
            self._thread = threading.Thread(target=self._tick, daemon=True)
            self._thread.start()
        else:
            self.running = False
            self.paused = True
            if self.play_icon_ref.current:
                self.play_icon_ref.current.value = "\ue037"  # play icon
                self.play_icon_ref.current.update()

    def _reset(self, e):
        self.running = False
        self.paused = False
        self.remaining = self.total
        if self.play_icon_ref.current:
            self.play_icon_ref.current.value = "\ue037"
            self.play_icon_ref.current.update()
        self._update_display()

    def _tick(self):
        while self.running and self.remaining > 0:
            time.sleep(1)
            if self.running:
                self.remaining -= 1
                self._update_display()
        if self.remaining <= 0 and self.running:
            self.running = False
            self.sessions_done += 1
            if self.sound_on:
                threading.Thread(target=_beep, args=(880, 0.25, 3), daemon=True).start()
            self._on_complete()

    def _on_complete(self):
        # 다음 세션 결정
        self.seq_idx = (self.seq_idx + 1) % len(SESSION_SEQUENCE)
        next_mode = SESSION_SEQUENCE[self.seq_idx]
        next_label = MODES[next_mode]["label"]

        # 기록 추가
        now_str = time.strftime("%H:%M")
        cfg = MODES[self.mode]
        self.history.append((cfg["label"], "—", now_str, "완료"))

        if self.auto_start:
            self._set_mode(next_mode)
            self.running = True
            self.paused = False
            self._thread = threading.Thread(target=self._tick, daemon=True)
            self._thread.start()
        else:
            self._show_done_dialog(next_label, next_mode)

    def _show_done_dialog(self, next_label: str, next_mode: str):
        def go_next(_):
            self.page.dialog.open = False
            self.page.update()
            self._set_mode(next_mode)

        self.page.dialog = ft.AlertDialog(
            bgcolor=BG_CARD,
            shape=ft.RoundedRectangleBorder(radius=16),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        mascot_widget(56),
                        ft.Text("세션 완료! 🎉", size=18, weight=ft.FontWeight.W_400,
                                color=ACCENT, font_family="DOSSaemmul",
                                text_align=ft.TextAlign.CENTER),
                        ft.Text(f"다음: {next_label} 세션",
                                size=13, color=TEXT_SEC, font_family="DOSSaemmul",
                                text_align=ft.TextAlign.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                padding=ft.padding.only(left=20, top=16, right=20, bottom=8),
            ),
            actions=[
                ft.TextButton("다음 세션 시작", style=ft.ButtonStyle(color=ACCENT),
                              on_click=go_next),
            ],
        )
        self.page.dialog.open = True
        try:
            self.page.update()
        except Exception:
            pass

    def _update_display(self):
        if self.time_ref.current:
            self.time_ref.current.value = self._fmt(self.remaining)
        if self.ring_ref.current:
            self.ring_ref.current.value = self.remaining / self.total if self.total else 0
            self.ring_ref.current.color = MODES[self.mode]["color"]
        try:
            self.page.update()
        except Exception:
            pass

    def _mode_tab(self, mode: str) -> ft.Container:
        cfg = MODES[mode]
        is_active = mode == self.mode

        def on_click(_):
            self._set_mode(mode)

        return ft.Container(
            content=ft.Text(cfg["label"], size=12, weight=ft.FontWeight.W_400,
                            color=cfg["color"] if is_active else TEXT_MUT,
                            font_family="DOSSaemmul"),
            bgcolor=ACCENT_LT if is_active else "transparent",
            border_radius=8,
            padding=ft.padding.only(left=14, top=7, right=14, bottom=7),
            on_click=on_click,
            border=ft.border.all(1, ACCENT if is_active else "transparent"),
        )

    def _session_dots(self) -> ft.Row:
        dots = []
        for i in range(8):
            done = i < self.sessions_done
            is_current = i == self.sessions_done
            dots.append(
                ft.Container(
                    width=10, height=10,
                    bgcolor=ACCENT if done else (ACCENT_LT if is_current else BORDER),
                    border_radius=5,
                    border=ft.border.all(1.5, ACCENT if (done or is_current) else BORDER),
                )
            )
        return ft.Row(controls=dots, spacing=6, alignment=ft.MainAxisAlignment.CENTER)

    def _history_rows(self) -> list:
        rows = []
        for mode_l, start, end, status in self.history[-5:]:
            rows.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                width=8, height=8,
                                bgcolor=ACCENT if "집중" in mode_l else PURPLE,
                                border_radius=4,
                            ),
                            ft.Text(mode_l, size=13, color=TEXT_PRI,
                                    font_family="DOSSaemmul", expand=True),
                            ft.Text(f"{start} → {end}", size=11, color=TEXT_MUT,
                                    font_family="DOSSaemmul"),
                            ft.Container(
                                content=ft.Text("완료", size=10, color=ACCENT,
                                                font_family="DOSSaemmul"),
                                bgcolor=ACCENT_LT,
                                border_radius=6,
                                padding=ft.padding.only(left=8, top=3, right=8, bottom=3),
                            ),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=BG_CARD,
                    border_radius=10,
                    padding=ft.padding.only(left=14, top=10, right=14, bottom=10),
                    border=ft.border.all(1, BORDER),
                )
            )
        return rows

    def build(self) -> ft.Container:
        cfg = MODES[self.mode]

        timer_area = card(
            ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            controls=[self._mode_tab(m) for m in MODES],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=8,
                        ),
                        bgcolor=BG_CARD2,
                        border_radius=10,
                        padding=6,
                        border=ft.border.all(1, BORDER),
                    ),
                    ft.Container(height=24),
                    ft.Container(
                        width=200, height=200,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Stack(
                            controls=[
                                ft.ProgressRing(
                                    ref=self.ring_ref,
                                    value=1.0,
                                    width=200, height=200,
                                    stroke_width=14,
                                    color=cfg["color"],
                                    bgcolor=BORDER,
                                ),
                                ft.Container(
                                    width=200, height=200,
                                    alignment=ft.Alignment(0, 0),
                                    content=ft.Column(
                                        controls=[
                                            ft.Text(
                                                ref=self.time_ref,
                                                value=self._fmt(self.remaining),
                                                size=50, weight=ft.FontWeight.W_500,
                                                color=TEXT_PRI,
                                                font_family="DOSSaemmul",
                                                text_align=ft.TextAlign.CENTER,
                                            ),
                                            ft.Text(
                                                ref=self.mode_label_ref,
                                                value=cfg["label"],
                                                size=13, color=TEXT_MUT,
                                                font_family="DOSSaemmul",
                                                text_align=ft.TextAlign.CENTER,
                                            ),
                                        ],
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        spacing=4,
                                    ),
                                ),
                            ],
                        ),
                    ),
                    ft.Container(height=18),
                    self._session_dots(),
                    ft.Text("세션 진행 (8회 사이클)",
                            size=11, color=TEXT_MUT,
                            font_family="DOSSaemmul",
                            text_align=ft.TextAlign.CENTER),
                    ft.Container(height=20),
                    ft.Row(
                        ref=self.btn_row_ref,
                        controls=[
                            ft.Container(
                                content=ft.Text("\ue042", font_family="Material Icons",
                                               size=20, color=TEXT_MUT),
                                width=46, height=46,
                                border_radius=23,
                                border=ft.border.all(1.5, BORDER),
                                alignment=ft.Alignment(0, 0),
                                on_click=self._reset,
                            ),
                            ft.Container(
                                content=ft.Text(ref=self.play_icon_ref,
                                               value="\ue037",
                                               font_family="Material Icons",
                                               size=26, color="#FFFFFF"),
                                width=68, height=68,
                                border_radius=34,
                                bgcolor=cfg["color"],
                                alignment=ft.Alignment(0, 0),
                                on_click=self._start_stop,
                                shadow=ft.BoxShadow(
                                    blur_radius=18, color=cfg["color"] + "55",
                                    offset=ft.Offset(0, 4),
                                ),
                            ),
                            ft.Container(
                                content=ft.Text("\ue044", font_family="Material Icons",
                                               size=20, color=TEXT_MUT),
                                width=46, height=46,
                                border_radius=23,
                                border=ft.border.all(1.5, BORDER),
                                alignment=ft.Alignment(0, 0),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=16,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
            padding=28,
        )

        # 설정 사이드바
        def toggle_sound(e):
            self.sound_on = e.control.value

        def toggle_auto(e):
            self.auto_start = e.control.value

        settings = card(
            ft.Column(
                controls=[
                    ft.Text("설정", size=14, weight=ft.FontWeight.W_400,
                            color=TEXT_PRI, font_family="DOSSaemmul"),
                    ft.Container(height=12),
                    *[
                        ft.Column(
                            controls=[
                                ft.Text(label, size=12, color=TEXT_SEC,
                                        font_family="DOSSaemmul"),
                                ft.Slider(
                                    min=1, max=60, value=val,
                                    active_color=ACCENT,
                                    inactive_color=BORDER,
                                    thumb_color=ACCENT,
                                    label="{value}분",
                                ),
                            ],
                            spacing=2,
                        )
                        for label, val in [("집중 시간", 25), ("짧은 휴식", 5), ("긴 휴식", 15)]
                    ],
                    ft.Container(height=4),
                    ft.Divider(color=BORDER, height=1),
                    ft.Container(height=4),
                    ft.Row(
                        controls=[
                            ft.Text("알림음", size=12, color=TEXT_SEC,
                                    font_family="DOSSaemmul", expand=True),
                            ft.Switch(value=True, active_color=ACCENT, scale=0.8,
                                      on_change=toggle_sound),
                        ],
                    ),
                    ft.Row(
                        controls=[
                            ft.Text("자동 전환", size=12, color=TEXT_SEC,
                                    font_family="DOSSaemmul", expand=True),
                            ft.Switch(value=False, active_color=ACCENT, scale=0.8,
                                      on_change=toggle_auto),
                        ],
                    ),
                ],
                spacing=10,
            ),
            padding=18,
        )

        history_card = card(
            ft.Column(
                ref=self.history_col_ref,
                controls=[
                    ft.Text("오늘의 기록", size=14, weight=ft.FontWeight.W_400,
                            color=TEXT_PRI, font_family="DOSSaemmul"),
                    ft.Container(height=10),
                    *self._history_rows(),
                ],
                spacing=8,
            ),
            padding=18,
        )

        right_col = ft.Column(
            controls=[settings, ft.Container(height=12), history_card],
            width=270,
            spacing=0,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("뽀모도로 타이머", size=26, weight=ft.FontWeight.W_400,
                                            color=TEXT_PRI, font_family="DOSSaemmul"),
                                    ft.Text("집중과 휴식의 리듬을 만들어보세요",
                                            size=13, color=TEXT_SEC, font_family="DOSSaemmul"),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                    ),
                    ft.Container(height=16),
                    ft.Row(
                        controls=[
                            ft.Container(content=timer_area, expand=True),
                            ft.Container(width=16),
                            right_col,
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        expand=True,
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            expand=True,
            padding=ft.padding.only(left=28, top=24, right=28, bottom=24),
            bgcolor=BG_BASE,
        )
