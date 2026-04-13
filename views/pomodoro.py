import flet as ft
import threading
import time
from components.ui import card, accent_btn, ghost_btn

BG_DARK = "#080B10"
BG_CARD = "#0D1117"
ACCENT = "#00E5CC"
ACCENT2 = "#FF6B6B"
PURPLE = "#A78BFA"
TEXT_PRIMARY = "#E8EDF3"
TEXT_MUTED = "#4A5568"
BORDER = "#1A2332"

MODES = {
    "focus":  {"label": "집중",  "minutes": 25, "color": ACCENT},
    "short":  {"label": "짧은 휴식", "minutes": 5, "color": PURPLE},
    "long":   {"label": "긴 휴식",  "minutes": 15, "color": ACCENT2},
}


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
        self.history = [
            ("집중", "09:00", "09:25", "완료"),
            ("짧은 휴식", "09:25", "09:30", "완료"),
            ("집중", "09:30", "09:55", "완료"),
        ]

        # Refs
        self.time_ref = ft.Ref()
        self.ring_ref = ft.Ref()
        self.mode_label_ref = ft.Ref()
        self.btn_row_ref = ft.Ref()
        self.session_dots_ref = ft.Ref()
        self.history_col_ref = ft.Ref()

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
            self._thread = threading.Thread(target=self._tick, daemon=True)
            self._thread.start()
        else:
            self.running = False
            self.paused = True
        self._update_btn_state()

    def _reset(self, e):
        self.running = False
        self.paused = False
        self.remaining = self.total
        self._update_display()
        self._update_btn_state()

    def _tick(self):
        while self.running and self.remaining > 0:
            time.sleep(1)
            if self.running:
                self.remaining -= 1
                self._update_display()
        if self.remaining <= 0:
            self.running = False
            self.sessions_done += 1
            self._on_complete()

    def _on_complete(self):
        self.page.dialog = ft.AlertDialog(
            bgcolor=BG_CARD,
            shape=ft.RoundedRectangleBorder(radius=16),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text("🎉", size=40, text_align=ft.TextAlign.CENTER),
                        ft.Text("세션 완료!", size=20, weight=ft.FontWeight.W_800,
                                color=ACCENT, font_family="Pretendard",
                                text_align=ft.TextAlign.CENTER),
                        ft.Text(f"{MODES[self.mode]['label']} 세션을 완료했어요.",
                                size=13, color=TEXT_MUTED, font_family="Pretendard",
                                text_align=ft.TextAlign.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                padding=20,
            ),
            actions=[
                ft.TextButton("다음 세션", style=ft.ButtonStyle(color=ACCENT),
                              on_click=lambda _: self._close_dialog()),
            ],
        )
        self.page.dialog.open = True
        self.page.update()

    def _close_dialog(self):
        self.page.dialog.open = False
        self.page.update()

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

    def _update_btn_state(self):
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
            content=ft.Text(cfg["label"], size=13, weight=ft.FontWeight.W_600,
                            color=cfg["color"] if is_active else TEXT_MUTED,
                            font_family="Pretendard"),
            bgcolor="#071A17" if is_active else "transparent",
            border_radius=8,
            padding=ft.padding.only(left=16, top=8, right=16, bottom=8),
            on_click=on_click,
            border=ft.border.all(1, cfg["color"] if is_active else "transparent"),
        )

    def _session_dots(self) -> ft.Row:
        dots = []
        for i in range(4):
            done = i < self.sessions_done
            dots.append(
                ft.Container(
                    width=12, height=12,
                    bgcolor=ACCENT if done else "#1A2332",
                    border_radius=6,
                    border=ft.border.all(1, ACCENT if done else "#2A3A4C"),
                )
            )
        return ft.Row(controls=dots, spacing=8,
                      alignment=ft.MainAxisAlignment.CENTER)

    def _history_rows(self) -> list:
        rows = []
        for mode_l, start, end, status in self.history:
            rows.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                width=8, height=8,
                                bgcolor=ACCENT if "집중" in mode_l else PURPLE,
                                border_radius=4,
                            ),
                            ft.Text(mode_l, size=13, color=TEXT_PRIMARY,
                                    font_family="Pretendard", expand=True),
                            ft.Text(f"{start} - {end}", size=11, color=TEXT_MUTED,
                                    font_family="JetBrains"),
                            ft.Container(
                                content=ft.Text("완료", size=10, color=ACCENT,
                                                font_family="Pretendard"),
                                bgcolor="#071A17",
                                border_radius=6,
                                padding=ft.padding.only(left=8, top=3, right=8, bottom=3),
                            ),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor="#0D1117",
                    border_radius=10,
                    padding=ft.padding.only(left=14, top=10, right=14, bottom=10),
                    border=ft.border.all(1, "#1A2332"),
                )
            )
        return rows

    def build(self) -> ft.Container:
        cfg = MODES[self.mode]

        timer_area = card(
            ft.Column(
                controls=[
                    # Mode tabs
                    ft.Container(
                        content=ft.Row(
                            controls=[self._mode_tab(m) for m in MODES],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=8,
                        ),
                        bgcolor="#0A0F16",
                        border_radius=12,
                        padding=6,
                        border=ft.border.all(1, BORDER),
                    ),
                    ft.Container(height=28),
                    # Timer ring
                    ft.Container(
                        content=ft.Stack(
                            controls=[
                                ft.Container(
                                    content=ft.ProgressRing(
                                        ref=self.ring_ref,
                                        value=1.0,
                                        width=220, height=220,
                                        stroke_width=16,
                                        color=cfg["color"],
                                        bgcolor="#1A2332",
                                    ),
                                    alignment=ft.Alignment(0, 0),
                                ),
                                ft.Container(
                                    content=ft.Column(
                                        controls=[
                                            ft.Text(
                                                ref=self.time_ref,
                                                value=self._fmt(self.remaining),
                                                size=56, weight=ft.FontWeight.W_900,
                                                color=TEXT_PRIMARY,
                                                font_family="JetBrains",
                                                text_align=ft.TextAlign.CENTER,
                                            ),
                                            ft.Text(
                                                ref=self.mode_label_ref,
                                                value=cfg["label"],
                                                size=14, color=TEXT_MUTED,
                                                font_family="Pretendard",
                                                text_align=ft.TextAlign.CENTER,
                                            ),
                                        ],
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        spacing=4,
                                    ),
                                    width=220, height=220,
                                    alignment=ft.Alignment(0, 0),
                                ),
                            ],
                            width=220, height=220,
                        ),
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Container(height=20),
                    # Session dots
                    self._session_dots(),
                    ft.Text("오늘의 세션 진행",
                            size=11, color=TEXT_MUTED,
                            font_family="Pretendard",
                            text_align=ft.TextAlign.CENTER),
                    ft.Container(height=20),
                    # Controls
                    ft.Row(
                        ref=self.btn_row_ref,
                        controls=[
                            # Reset
                            ft.Container(
                                content=ft.Text("\ue042", font_family="Material Icons",
                                               size=22, color=TEXT_MUTED),
                                width=48, height=48,
                                border_radius=24,
                                border=ft.border.all(1, BORDER),
                                alignment=ft.Alignment(0, 0),
                                on_click=self._reset,
                            ),
                            # Play/Pause
                            ft.Container(
                                content=ft.Text("\ue037", font_family="Material Icons",
                                               size=28, color="#080B10"),
                                width=72, height=72,
                                border_radius=36,
                                bgcolor=cfg["color"],
                                alignment=ft.Alignment(0, 0),
                                on_click=self._start_stop,
                                shadow=ft.BoxShadow(
                                    blur_radius=20, color=cfg["color"] + "40",
                                    offset=ft.Offset(0, 4),
                                ),
                            ),
                            # Skip
                            ft.Container(
                                content=ft.Text("\ue044", font_family="Material Icons",
                                               size=22, color=TEXT_MUTED),
                                width=48, height=48,
                                border_radius=24,
                                border=ft.border.all(1, BORDER),
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
            padding=32,
        )

        # Settings sidebar
        settings = card(
            ft.Column(
                controls=[
                    ft.Text("설정", size=15, weight=ft.FontWeight.W_700,
                            color=TEXT_PRIMARY, font_family="Pretendard"),
                    ft.Container(height=16),
                    *[
                        ft.Column(
                            controls=[
                                ft.Text(label, size=12, color=TEXT_MUTED,
                                        font_family="Pretendard"),
                                ft.Slider(
                                    min=1, max=60, value=val,
                                    active_color=ACCENT,
                                    inactive_color="#1A2332",
                                    thumb_color=ACCENT,
                                    label="{value}분",
                                ),
                            ],
                            spacing=4,
                        )
                        for label, val in [("집중 시간", 25), ("짧은 휴식", 5), ("긴 휴식", 15)]
                    ],
                    ft.Container(height=8),
                    ft.Divider(color=BORDER, height=1),
                    ft.Container(height=8),
                    ft.Row(
                        controls=[
                            ft.Text("알림음", size=12, color=TEXT_MUTED,
                                    font_family="Pretendard", expand=True),
                            ft.Switch(value=True, active_color=ACCENT, scale=0.8),
                        ],
                    ),
                    ft.Row(
                        controls=[
                            ft.Text("자동 시작", size=12, color=TEXT_MUTED,
                                    font_family="Pretendard", expand=True),
                            ft.Switch(value=False, active_color=ACCENT, scale=0.8),
                        ],
                    ),
                ],
                spacing=12,
            ),
            padding=20,
        )

        history_card = card(
            ft.Column(
                controls=[
                    ft.Text("오늘의 기록", size=15, weight=ft.FontWeight.W_700,
                            color=TEXT_PRIMARY, font_family="Pretendard"),
                    ft.Container(height=12),
                    *self._history_rows(),
                ],
                spacing=8,
            ),
            padding=20,
        )

        right_col = ft.Column(
            controls=[settings, ft.Container(height=12), history_card],
            width=280,
            spacing=0,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("뽀모도로 타이머", size=26, weight=ft.FontWeight.W_900,
                                            color=TEXT_PRIMARY, font_family="Pretendard"),
                                    ft.Text("집중과 휴식의 리듬을 만들어보세요",
                                            size=13, color=TEXT_MUTED, font_family="Pretendard"),
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
            bgcolor="#080B10",
        )
