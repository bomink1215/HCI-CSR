import flet as ft
import asyncio
import subprocess
import sys
import threading
import time
from components.ui import card, mascot_widget


def _notify(title: str, message: str):
    """OS 알림 (플랫폼별 최적 방식)"""
    if sys.platform == "darwin":
        # macOS: 네이티브 알림센터
        try:
            script = (
                f'display notification "{message}" '
                f'with title "{title}" '
                f'sound name "Glass"'
            )
            subprocess.Popen(["osascript", "-e", script])
        except Exception:
            pass
    elif sys.platform == "win32":
        # Windows: 별도 프로세스로 tkinter 팝업 → Tcl_AsyncDelete 방지
        _notify_subprocess(title, message)
    else:
        # Linux: 스레드로 tkinter 팝업
        threading.Thread(target=_notify_tkinter, args=(title, message), daemon=True).start()


def _notify_subprocess(title: str, message: str):
    """Windows 전용 — subprocess로 tkinter 팝업 실행"""
    try:
        script = r"""
import sys
import tkinter as tk

title   = sys.argv[1]
message = sys.argv[2]

ACCENT = "#00C9A7"
W, H   = 300, 90

root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-alpha", 0.0)
root.configure(bg="#FFFFFF")

sw = root.winfo_screenwidth()
sh = root.winfo_screenheight()
x       = sw - W - 16
y_final = sh - H - 56
y_start = sh + H

root.geometry(f"{W}x{H}+{x}+{y_start}")

outer = tk.Frame(root, bg=ACCENT, padx=2, pady=2)
outer.pack(fill="both", expand=True)
inner = tk.Frame(outer, bg="#1A1D23", padx=12, pady=10)
inner.pack(fill="both", expand=True)

tk.Label(inner, text=title, bg="#1A1D23", fg=ACCENT,
         font=("Segoe UI", 10, "bold")).pack(anchor="w")
tk.Label(inner, text=message, bg="#1A1D23", fg="#FFFFFF",
         font=("Segoe UI", 9), wraplength=260,
         justify="left").pack(anchor="w", pady=(4, 0))

def slide_in(step=0):
    if step > 20:
        root.after(4000, slide_out)
        return
    t    = step / 20
    ease = 1 - (1 - t) ** 3
    root.geometry(f"{W}x{H}+{x}+{int(y_start + (y_final - y_start) * ease)}")
    root.attributes("-alpha", min(1.0, ease * 1.5))
    root.after(15, lambda: slide_in(step + 1))

def slide_out(step=0):
    if step > 15:
        root.destroy()
        return
    t = step / 15
    try:
        root.geometry(f"{W}x{H}+{x}+{int(y_final + (sh - y_final) * t ** 2)}")
        root.attributes("-alpha", max(0.0, 1.0 - t))
        root.after(12, lambda: slide_out(step + 1))
    except Exception:
        pass

slide_in()
root.mainloop()
"""
        subprocess.Popen(
            [sys.executable, "-c", script, title, message],
            creationflags=0x08000000,  # CREATE_NO_WINDOW
        )
    except Exception:
        pass


def _notify_tkinter(title: str, message: str):
    """macOS / Linux 전용 — 스레드에서 tkinter 팝업 실행"""
    try:
        import tkinter as tk

        ACCENT = "#00C9A7"
        W, H   = 300, 90

        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.0)
        root.configure(bg="#FFFFFF")

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x       = sw - W - 16
        y_final = sh - H - 56
        y_start = sh + H

        root.geometry(f"{W}x{H}+{x}+{y_start}")

        outer = tk.Frame(root, bg=ACCENT, padx=2, pady=2)
        outer.pack(fill="both", expand=True)
        inner = tk.Frame(outer, bg="#1A1D23", padx=12, pady=10)
        inner.pack(fill="both", expand=True)

        tk.Label(inner, text=title, bg="#1A1D23", fg=ACCENT,
                 font=("Helvetica", 10, "bold")).pack(anchor="w")
        tk.Label(inner, text=message, bg="#1A1D23", fg="#FFFFFF",
                 font=("Helvetica", 9), wraplength=260,
                 justify="left").pack(anchor="w", pady=(4, 0))

        def slide_in(step=0):
            if step > 20:
                root.after(4000, slide_out)
                return
            t    = step / 20
            ease = 1 - (1 - t) ** 3
            root.geometry(f"{W}x{H}+{x}+{int(y_start + (y_final - y_start) * ease)}")
            root.attributes("-alpha", min(1.0, ease * 1.5))
            root.after(15, lambda: slide_in(step + 1))

        def slide_out(step=0):
            if step > 15:
                root.destroy()
                return
            t = step / 15
            try:
                root.geometry(f"{W}x{H}+{x}+{int(y_final + (sh - y_final) * t ** 2)}")
                root.attributes("-alpha", max(0.0, 1.0 - t))
                root.after(12, lambda: slide_out(step + 1))
            except Exception:
                pass

        slide_in()
        root.mainloop()
    except Exception:
        pass

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

MODE_COLORS  = {"focus": ACCENT,  "rest": PURPLE}
MODE_LABELS  = {"focus": "집중",   "rest": "휴식"}


def _beep(freq: int = 880, duration: float = 0.3, times: int = 2):
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
        self.focus_minutes = 25
        self.rest_minutes  = 5
        self.running = False
        self.paused  = False
        self.remaining = 25 * 60
        self.total     = 25 * 60
        self._thread   = None
        self.sessions_done = 0   # 완료된 집중 세션 수
        self.cycle_count   = 4   # 목표 사이클 수
        self.auto_start = False
        self.sound_on   = True
        self.history = []
        self.session_start_str = ""  # 세션 시작 시각 기록용

        self.time_ref        = ft.Ref()
        self.ring_ref        = ft.Ref()
        self.mode_label_ref  = ft.Ref()
        self.play_icon_ref   = ft.Ref()
        self.play_btn_ref    = ft.Ref()
        self.history_col_ref = ft.Ref()
        self.tab_refs        = {"focus": ft.Ref(), "rest": ft.Ref()}
        self.tab_text_refs   = {"focus": ft.Ref(), "rest": ft.Ref()}
        self.on_tick = None   # DashboardView.update_pomodoro 콜백 연결용

        self.test_mode        = False
        self.focus_label_ref  = ft.Ref()
        self.rest_label_ref   = ft.Ref()
        self.cycle_label_ref  = ft.Ref()
        self.cycle_text_ref   = ft.Ref()
        self.session_dots_ref = ft.Ref()
        self.test_btn_ref     = ft.Ref()

    # ── helpers ──────────────────────────────────────────────────────────
    def _fmt(self, secs: int) -> str:
        return f"{secs // 60:02d}:{secs % 60:02d}"

    # ── mode switching ───────────────────────────────────────────────────
    def _set_mode(self, mode: str, e=None):
        self.mode = mode
        if self.test_mode:
            secs = 10
        else:
            mins = self.focus_minutes if mode == "focus" else self.rest_minutes
            secs = mins * 60
        self.remaining = secs
        self.total = secs
        self.running = False
        self.paused  = False
        # reset play icon
        if self.play_icon_ref.current:
            self.play_icon_ref.current.icon = ft.Icons.PLAY_ARROW
            self.play_icon_ref.current.update()
        # update play button color
        if self.play_btn_ref.current:
            self.play_btn_ref.current.bgcolor = MODE_COLORS[mode]
            self.play_btn_ref.current.update()
        self._update_tabs()
        self._update_display()

    def _update_tabs(self):
        for m in ("focus", "rest"):
            is_active = m == self.mode
            if self.tab_refs[m].current:
                self.tab_refs[m].current.bgcolor = ACCENT_LT if is_active else "transparent"
                self.tab_refs[m].current.border  = ft.border.all(1, ACCENT if is_active else "transparent")
                self.tab_refs[m].current.update()
            if self.tab_text_refs[m].current:
                self.tab_text_refs[m].current.color = MODE_COLORS[m] if is_active else TEXT_MUT
                self.tab_text_refs[m].current.update()

    # ── playback control ─────────────────────────────────────────────────
    def _fire_tick(self):
        if self.on_tick:
            try:
                self.on_tick(self.remaining, self.total, self.mode, self.running)
            except Exception:
                pass

    def _start_stop(self, e):
        if not self.running:
            self.running = True
            self.paused  = False
            # 처음 시작할 때만 시작 시각 기록 (일시정지 후 재개는 덮어쓰지 않음)
            if not self.paused or not self.session_start_str:
                self.session_start_str = time.strftime("%H:%M")
            if self.play_icon_ref.current:
                self.play_icon_ref.current.icon = ft.Icons.PAUSE
                self.play_icon_ref.current.update()
            self._fire_tick()
            self.page.run_task(self._tick_async)
        else:
            self.running = False
            self.paused  = True
            if self.play_icon_ref.current:
                self.play_icon_ref.current.icon = ft.Icons.PLAY_ARROW
                self.play_icon_ref.current.update()
            self._fire_tick()

    def _skip_next(self, e):
        """현재 세션을 건너뛰고 다음 세션으로 이동"""
        self.running = False
        self.paused  = False
        next_mode = "rest" if self.mode == "focus" else "focus"
        self._set_mode(next_mode)

    def _reset(self, e):
        self.running  = False
        self.paused   = False
        if self.test_mode:
            secs = 10
        else:
            mins = self.focus_minutes if self.mode == "focus" else self.rest_minutes
            secs = mins * 60
        self.remaining = secs
        self.total     = secs
        if self.play_icon_ref.current:
            self.play_icon_ref.current.icon = ft.Icons.PLAY_ARROW
            self.play_icon_ref.current.update()
        self._update_display()

    # ── tick (async, wall-clock based → no drift, real-time UI update) ──
    async def _tick_async(self):
        start_wall      = time.time()
        start_remaining = self.remaining
        last_shown      = self.remaining

        while self.running and self.remaining > 0:
            await asyncio.sleep(0.25)
            if not self.running:
                break
            elapsed       = time.time() - start_wall
            new_remaining = max(0, start_remaining - int(elapsed))
            if new_remaining != last_shown:
                self.remaining = new_remaining
                last_shown     = new_remaining
                self._update_display()

        if self.remaining <= 0 and self.running:
            self.running = False
            if self.sound_on:
                threading.Thread(target=_beep, args=(880, 0.25, 3), daemon=True).start()
            self._on_complete()

    # ── session completion ───────────────────────────────────────────────
    def _on_complete(self):
        now_str = time.strftime("%H:%M")
        start_str = self.session_start_str or "—"
        self.history.append((MODE_LABELS[self.mode], start_str, now_str, "완료"))
        self._update_history()

        # 집중 세션 완료 시에만 카운트
        if self.mode == "focus":
            self.sessions_done += 1
            self._update_dots()

        # 목표 사이클 달성 확인
        if self.mode == "focus" and self.sessions_done >= self.cycle_count:
            threading.Thread(
                target=_notify,
                args=("FocusMate ✅", f"{self.cycle_count}회 사이클 목표 달성! 오늘도 수고하셨어요."),
                daemon=True,
            ).start()
            self._show_all_done_dialog()
            return

        # 세션 전환 OS 알림
        if self.mode == "focus":
            threading.Thread(
                target=_notify,
                args=("FocusMate 💪", "집중 세션 완료! 휴식 시간이에요."),
                daemon=True,
            ).start()
        else:
            threading.Thread(
                target=_notify,
                args=("FocusMate ⏰", "휴식 종료! 다음 집중 세션을 시작할게요."),
                daemon=True,
            ).start()

        next_mode  = "rest" if self.mode == "focus" else "focus"
        next_label = MODE_LABELS[next_mode]

        if self.mode == "focus":
            # 집중 → 휴식: 항상 자동 전환
            self._set_mode(next_mode)
            self.session_start_str = time.strftime("%H:%M")
            self.running = True
            self.paused  = False
            if self.play_icon_ref.current:
                self.play_icon_ref.current.icon = ft.Icons.PAUSE
                self.play_icon_ref.current.update()
            self.page.run_task(self._tick_async)
        elif self.auto_start:
            # 휴식 → 집중: 자동 전환 켜져 있을 때만
            self._set_mode(next_mode)
            self.session_start_str = time.strftime("%H:%M")
            self.running = True
            self.paused  = False
            if self.play_icon_ref.current:
                self.play_icon_ref.current.icon = ft.Icons.PAUSE
                self.play_icon_ref.current.update()
            self.page.run_task(self._tick_async)
        else:
            # 휴식 → 집중: 다이얼로그
            self._show_done_dialog(next_label, next_mode)

    def _show_all_done_dialog(self):
        def restart(_):
            self.page.dialog.open = False
            self.page.update()
            self.sessions_done = 0
            self._update_dots()
            self._set_mode("focus")

        self.page.dialog = ft.AlertDialog(
            bgcolor=BG_CARD,
            shape=ft.RoundedRectangleBorder(radius=16),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        mascot_widget(56),
                        ft.Text("목표 달성! 🎉", size=18, weight=ft.FontWeight.W_400,
                                color=ACCENT, font_family="DOSSaemmul",
                                text_align=ft.TextAlign.CENTER),
                        ft.Text(f"{self.cycle_count}회 사이클을 완료했어요!",
                                size=13, color=TEXT_SEC, font_family="DOSSaemmul",
                                text_align=ft.TextAlign.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                padding=ft.padding.only(left=20, top=16, right=20, bottom=8),
            ),
            actions=[
                ft.TextButton("다시 시작", style=ft.ButtonStyle(color=ACCENT),
                              on_click=restart),
            ],
        )
        self.page.dialog.open = True
        try:
            self.page.update()
        except Exception:
            pass

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

    # ── display update ───────────────────────────────────────────────────
    def _update_display(self):
        try:
            if self.time_ref.current:
                self.time_ref.current.value = self._fmt(self.remaining)
                self.time_ref.current.update()
            if self.ring_ref.current:
                self.ring_ref.current.value = self.remaining / self.total if self.total else 0
                self.ring_ref.current.color = MODE_COLORS[self.mode]
                self.ring_ref.current.update()
            if self.mode_label_ref.current:
                self.mode_label_ref.current.value = MODE_LABELS[self.mode]
                self.mode_label_ref.current.update()
        except Exception:
            pass
        if self.on_tick:
            try:
                self.on_tick(self.remaining, self.total, self.mode, self.running)
            except Exception:
                pass

    # ── dots & history ───────────────────────────────────────────────────
    def _dot_controls(self) -> list:
        dots = []
        for i in range(self.cycle_count):
            done       = i < self.sessions_done
            is_current = i == self.sessions_done and self.sessions_done < self.cycle_count
            dots.append(ft.Container(
                width=10, height=10,
                bgcolor=ACCENT if done else (ACCENT_LT if is_current else BORDER),
                border_radius=5,
                border=ft.border.all(1.5, ACCENT if (done or is_current) else BORDER),
            ))
        return dots

    def _update_dots(self):
        if self.session_dots_ref.current:
            self.session_dots_ref.current.controls = self._dot_controls()
            self.session_dots_ref.current.update()
        if self.cycle_text_ref.current:
            self.cycle_text_ref.current.value = f"집중 진행 ({self.sessions_done}/{self.cycle_count}회)"
            self.cycle_text_ref.current.update()

    def _update_history(self):
        if self.history_col_ref.current:
            self.history_col_ref.current.controls = [
                ft.Text("오늘의 기록", size=14, weight=ft.FontWeight.W_400,
                        color=TEXT_PRI, font_family="DOSSaemmul"),
                ft.Container(height=10),
                *self._history_rows(),
            ]
            try:
                self.history_col_ref.current.update()
            except Exception:
                pass

    def _history_rows(self) -> list:
        rows = []
        for mode_l, start, end, _ in self.history[-5:]:
            color = ACCENT if mode_l == "집중" else PURPLE
            rows.append(ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(width=8, height=8, bgcolor=color, border_radius=4),
                        ft.Text(mode_l, size=13, color=TEXT_PRI,
                                font_family="DOSSaemmul", expand=True),
                        ft.Text(f"{start} → {end}", size=11, color=TEXT_MUT,
                                font_family="DOSSaemmul"),
                        ft.Container(
                            content=ft.Text("완료", size=10, color=ACCENT,
                                            font_family="DOSSaemmul"),
                            bgcolor=ACCENT_LT, border_radius=6,
                            padding=ft.padding.only(left=8, top=3, right=8, bottom=3),
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=BG_CARD, border_radius=10,
                padding=ft.padding.only(left=14, top=10, right=14, bottom=10),
                border=ft.border.all(1, BORDER),
            ))
        return rows

    # ── build ────────────────────────────────────────────────────────────
    def build(self) -> ft.Container:

        def _mode_tab(mode: str) -> ft.Container:
            is_active = mode == self.mode
            return ft.Container(
                ref=self.tab_refs[mode],
                content=ft.Text(
                    ref=self.tab_text_refs[mode],
                    value=MODE_LABELS[mode],
                    size=12, weight=ft.FontWeight.W_400,
                    color=MODE_COLORS[mode] if is_active else TEXT_MUT,
                    font_family="DOSSaemmul",
                ),
                bgcolor=ACCENT_LT if is_active else "transparent",
                border_radius=8,
                padding=ft.padding.only(left=14, top=7, right=14, bottom=7),
                on_click=lambda _, m=mode: self._set_mode(m),
                border=ft.border.all(1, ACCENT if is_active else "transparent"),
            )

        timer_area = card(
            ft.Column(
                controls=[
                    # 탭
                    ft.Container(
                        content=ft.Row(
                            controls=[_mode_tab("focus"), _mode_tab("rest")],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=8,
                        ),
                        bgcolor=BG_CARD2, border_radius=10,
                        padding=6, border=ft.border.all(1, BORDER),
                    ),
                    ft.Container(height=24),
                    # 링 타이머
                    ft.Container(
                        width=200, height=200,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Stack(controls=[
                            ft.ProgressRing(
                                ref=self.ring_ref,
                                value=1.0, width=200, height=200,
                                stroke_width=14, color=ACCENT, bgcolor=BORDER,
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
                                            color=TEXT_PRI, font_family="DOSSaemmul",
                                            text_align=ft.TextAlign.CENTER,
                                        ),
                                        ft.Text(
                                            ref=self.mode_label_ref,
                                            value=MODE_LABELS[self.mode],
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
                        ]),
                    ),
                    ft.Container(height=18),
                    ft.Row(
                        ref=self.session_dots_ref,
                        controls=self._dot_controls(),
                        spacing=6,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Text(
                        ref=self.cycle_text_ref,
                        value=f"집중 진행 ({self.sessions_done}/{self.cycle_count}회)",
                        size=11, color=TEXT_MUT,
                        font_family="DOSSaemmul",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=20),
                    # 버튼 행
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Icon(ft.Icons.REPLAY, size=20, color=TEXT_MUT),
                                width=46, height=46, border_radius=23,
                                border=ft.border.all(1.5, BORDER),
                                alignment=ft.Alignment(0, 0),
                                on_click=self._reset,
                            ),
                            ft.Container(
                                ref=self.play_btn_ref,
                                content=ft.Icon(
                                    ref=self.play_icon_ref,
                                    icon=ft.Icons.PLAY_ARROW,
                                    size=26, color="#FFFFFF",
                                ),
                                width=68, height=68, border_radius=34,
                                bgcolor=ACCENT,
                                alignment=ft.Alignment(0, 0),
                                on_click=self._start_stop,
                                shadow=ft.BoxShadow(
                                    blur_radius=18, color=ACCENT + "55",
                                    offset=ft.Offset(0, 4),
                                ),
                            ),
                            ft.Container(
                                content=ft.Icon(ft.Icons.SKIP_NEXT, size=20, color=TEXT_MUT),
                                width=46, height=46, border_radius=23,
                                border=ft.border.all(1.5, BORDER),
                                alignment=ft.Alignment(0, 0),
                                on_click=self._skip_next,
                                tooltip="다음 세션으로",
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

        # ── 설정 ─────────────────────────────────────────────────────────
        def on_focus_change(e):
            self.focus_minutes = int(round(e.control.value / 5) * 5)
            if self.focus_label_ref.current:
                self.focus_label_ref.current.value = f"집중 시간  {self.focus_minutes}분"
                self.focus_label_ref.current.update()
            if self.mode == "focus" and not self.running:
                self.remaining = self.focus_minutes * 60
                self.total     = self.remaining
                self._update_display()

        def on_rest_change(e):
            self.rest_minutes = int(round(e.control.value / 5) * 5)
            if self.rest_label_ref.current:
                self.rest_label_ref.current.value = f"휴식 시간  {self.rest_minutes}분"
                self.rest_label_ref.current.update()
            if self.mode == "rest" and not self.running:
                self.remaining = self.rest_minutes * 60
                self.total     = self.remaining
                self._update_display()

        def on_cycle_change(e):
            self.cycle_count = int(round(e.control.value))
            if self.cycle_label_ref.current:
                self.cycle_label_ref.current.value = f"목표 사이클  {self.cycle_count}회"
                self.cycle_label_ref.current.update()
            # 이미 완료한 세션이 새 목표보다 많으면 리셋
            if self.sessions_done > self.cycle_count:
                self.sessions_done = 0
            self._update_dots()

        def toggle_test_mode(e):
            self.test_mode = not self.test_mode
            self.running   = False
            self.paused    = False

            if self.test_mode:
                # 원래 설정 저장 후 테스트 값으로 교체
                self._saved_cycle_count = self.cycle_count
                self.cycle_count = 2
            else:
                # 원래 설정 복원
                self.cycle_count = getattr(self, "_saved_cycle_count", self.cycle_count)

            # 세션 카운트 리셋
            self.sessions_done = 0
            self._update_dots()

            if self.test_btn_ref.current:
                self.test_btn_ref.current.bgcolor = DANGER if self.test_mode else BG_CARD2
                self.test_btn_ref.current.border  = ft.border.all(1.5, DANGER if self.test_mode else BORDER)
                lbl: ft.Text = self.test_btn_ref.current.content
                lbl.value = "🧪 테스트 모드 ON  (10초 × 2회)" if self.test_mode else "🧪 테스트 모드"
                lbl.color = "#FFFFFF" if self.test_mode else TEXT_MUT
                self.test_btn_ref.current.update()

            # 현재 세션 즉시 리셋
            secs = 10 if self.test_mode else (
                self.focus_minutes if self.mode == "focus" else self.rest_minutes) * 60
            self.remaining = secs
            self.total     = secs
            if self.play_icon_ref.current:
                self.play_icon_ref.current.icon = ft.Icons.PLAY_ARROW
                self.play_icon_ref.current.update()
            self._set_mode("focus")

        def toggle_sound(e):
            self.sound_on = e.control.value

        def toggle_auto(e):
            self.auto_start = e.control.value

        settings = card(
            ft.Column(
                controls=[
                    ft.Text("설정", size=14, weight=ft.FontWeight.W_400,
                            color=TEXT_PRI, font_family="DOSSaemmul"),
                    ft.Container(height=8),
                    # 집중 시간 슬라이더
                    ft.Column(controls=[
                        ft.Text(ref=self.focus_label_ref,
                                value=f"집중 시간  {self.focus_minutes}분",
                                size=12, color=TEXT_SEC, font_family="DOSSaemmul"),
                        ft.Slider(
                            min=5, max=60, value=self.focus_minutes,
                            divisions=11,
                            active_color=ACCENT, inactive_color=BORDER, thumb_color=ACCENT,
                            on_change=on_focus_change,
                        ),
                    ], spacing=2),
                    # 휴식 시간 슬라이더
                    ft.Column(controls=[
                        ft.Text(ref=self.rest_label_ref,
                                value=f"휴식 시간  {self.rest_minutes}분",
                                size=12, color=TEXT_SEC, font_family="DOSSaemmul"),
                        ft.Slider(
                            min=5, max=30, value=self.rest_minutes,
                            divisions=5,
                            active_color=PURPLE, inactive_color=BORDER, thumb_color=PURPLE,
                            on_change=on_rest_change,
                        ),
                    ], spacing=2),
                    # 목표 사이클 슬라이더
                    ft.Column(controls=[
                        ft.Text(ref=self.cycle_label_ref,
                                value=f"목표 사이클  {self.cycle_count}회",
                                size=12, color=TEXT_SEC, font_family="DOSSaemmul"),
                        ft.Slider(
                            min=1, max=8, value=self.cycle_count,
                            divisions=7,
                            active_color=WARNING, inactive_color=BORDER, thumb_color=WARNING,
                            on_change=on_cycle_change,
                        ),
                    ], spacing=2),
                    ft.Container(height=4),
                    ft.Divider(color=BORDER, height=1),
                    ft.Container(height=4),
                    # 테스트 모드 버튼
                    ft.Container(
                        ref=self.test_btn_ref,
                        content=ft.Text("🧪 테스트 모드", size=12,
                                        color=TEXT_MUT, font_family="DOSSaemmul",
                                        text_align=ft.TextAlign.CENTER),
                        bgcolor=BG_CARD2,
                        border_radius=8,
                        border=ft.border.all(1.5, BORDER),
                        padding=ft.padding.symmetric(vertical=8),
                        alignment=ft.Alignment(0, 0),
                        on_click=toggle_test_mode,
                        tooltip="집중/휴식을 각 10초로 설정",
                        expand=True,
                    ),
                    ft.Divider(color=BORDER, height=1),
                    ft.Container(height=4),
                    ft.Row(controls=[
                        ft.Text("알림음", size=12, color=TEXT_SEC,
                                font_family="DOSSaemmul", expand=True),
                        ft.Switch(value=True, active_color=ACCENT, scale=0.8,
                                  on_change=toggle_sound),
                    ]),
                    ft.Row(controls=[
                        ft.Text("자동 전환", size=12, color=TEXT_SEC,
                                font_family="DOSSaemmul", expand=True),
                        ft.Switch(value=False, active_color=ACCENT, scale=0.8,
                                  on_change=toggle_auto),
                    ]),
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
            width=270, spacing=0,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(controls=[
                        ft.Column(
                            controls=[
                                ft.Text("뽀모도로 타이머", size=26, weight=ft.FontWeight.W_400,
                                        color=TEXT_PRI, font_family="DOSSaemmul"),
                                ft.Text("집중과 휴식의 리듬을 만들어보세요",
                                        size=13, color=TEXT_SEC, font_family="DOSSaemmul"),
                            ],
                            spacing=2, expand=True,
                        ),
                    ]),
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
