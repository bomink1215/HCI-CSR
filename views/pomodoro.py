import flet as ft
from utils import lang as lang_store
import asyncio
import subprocess
import sys
import threading
import time
from components.ui import card, mascot_widget
from utils import firebase, session, score_store


def _notify(title: str, message: str):
    """OS notification (platform-specific best method)"""
    if sys.platform == "darwin":
        try:
            script = (
                f'display notification "{message}" '
                f'with title "{title}"'
            )
            subprocess.Popen(["osascript", "-e", script])
        except Exception:
            pass
    elif sys.platform == "win32":
        _notify_subprocess(title, message)
    else:
        threading.Thread(target=_notify_tkinter, args=(title, message), daemon=True).start()


def _notify_subprocess(title: str, message: str):
    """Windows only — run tkinter popup via subprocess"""
    try:
        script = r"""
import sys
import tkinter as tk

title   = sys.argv[1]
message = sys.argv[2]

ACCENT    = "#7AC3B8"
W, H   = 300, 90

root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-alpha", 0.0)
root.configure(bg="#F0F9F8")

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
tk.Label(inner, text=message, bg="#1A1D23", fg="#F0F9F8",
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
            creationflags=0x08000000,
        )
    except Exception:
        pass


def _notify_tkinter(title: str, message: str):
    """macOS / Linux — run tkinter popup in thread"""
    try:
        import tkinter as tk

        ACCENT    = "#7AC3B8"
        W, H   = 300, 90

        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.0)
        root.configure(bg="#F0F9F8")

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
        tk.Label(inner, text=message, bg="#1A1D23", fg="#F0F9F8",
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

BG_BASE   = "#F0F9F8"
BG_CARD   = "#F4F6F8"
BG_CARD2  = "#EAECEF"
ACCENT    = "#7AC3B8"
ACCENT_LT = "#D6F5EF"
ACCENT_DK = "#009E83"
DANGER    = "#FF5C5C"
WARNING   = "#FFB347"
PINK    = "#F3A2BE"
TEXT_PRI  = "#1A1D23"
TEXT_SEC  = "#5A6375"
TEXT_MUT  = "#9DA8B7"
BORDER    = "#E2E6EC"

MODE_COLORS  = {"focus": ACCENT,   "rest": PINK}
MODE_LABELS  = {"focus": "focus_session",  "rest": "break_session"}  # lang keys


def _completion_sound():
    """C-E-G 상행 아르페지오 + 벨 배음 — 완료 느낌 차임."""
    try:
        import math, wave, tempfile, os
        sample_rate = 44100
        # C5=523 Hz, E5=659 Hz, G5=784 Hz  (마지막 노트 길게)
        notes = [(523, 0.13), (659, 0.13), (784, 0.32)]
        data = b""
        for freq, dur in notes:
            n = int(sample_rate * dur)
            for i in range(n):
                t = i / sample_rate
                env = math.exp(-5 * t / dur)          # 자연 감쇠
                v = env * (
                    0.60 * math.sin(2 * math.pi * freq * t)
                    + 0.22 * math.sin(2 * math.pi * freq * 2 * t)
                    + 0.12 * math.sin(2 * math.pi * freq * 3 * t)
                    + 0.06 * math.sin(2 * math.pi * freq * 4 * t)
                )
                data += int(32767 * 0.52 * v).to_bytes(2, "little", signed=True)

        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(tmp.name, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(data)

        if sys.platform == "darwin":
            subprocess.Popen(["afplay", tmp.name])
        elif sys.platform == "win32":
            import winsound
            winsound.PlaySound(tmp.name, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            subprocess.Popen(["aplay", "-q", tmp.name])

        time.sleep(sum(d for _, d in notes) + 0.15)
        os.unlink(tmp.name)
    except Exception:
        try:
            if sys.platform == "win32":
                import winsound
                for f in (523, 659, 784):
                    winsound.Beep(f, 130)
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
        self.sessions_done = 0
        self.cycle_count   = 4
        self.auto_start = True
        self.sound_on   = True
        self.history = list(score_store.get_today_history())  # 저장된 오늘 로그 복원
        self.session_start_str = ""

        self.time_ref        = ft.Ref()
        self.ring_ref        = ft.Ref()
        self.mode_label_ref  = ft.Ref()
        self.play_icon_ref   = ft.Ref()
        self.play_btn_ref    = ft.Ref()
        self.history_col_ref = ft.Ref()
        self.tab_refs        = {"focus": ft.Ref(), "rest": ft.Ref()}
        self.tab_text_refs   = {"focus": ft.Ref(), "rest": ft.Ref()}
        self.on_tick = None
        self.on_sessions_update = None

        self.test_mode        = False
        self.focus_label_ref  = ft.Ref()
        self.rest_label_ref   = ft.Ref()
        self.cycle_label_ref  = ft.Ref()
        self.cycle_text_ref   = ft.Ref()
        self.session_dots_ref = ft.Ref()
        self.test_btn_ref     = ft.Ref()

        # 언어 변경 시 Today's Log 레이블 갱신
        lang_store.add_listener(self._on_lang_change)

    def _on_lang_change(self):
        try:
            self._update_history()
            self._update_dots()
        except Exception:
            pass

    def _fmt(self, secs: int) -> str:
        return f"{secs // 60:02d}:{secs % 60:02d}"

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
        if self.play_icon_ref.current:
            self.play_icon_ref.current.icon = ft.Icons.PLAY_ARROW
            self.play_icon_ref.current.update()
        if self.play_btn_ref.current:
            self.play_btn_ref.current.bgcolor = MODE_COLORS[mode]
            self.play_btn_ref.current.update()
        self._update_tabs()
        self._update_display()

    def _update_tabs(self):
        _BG = {"focus": ACCENT_LT, "rest": "#EDE9FF"}
        for m in ("focus", "rest"):
            is_active = m == self.mode
            color = MODE_COLORS[m]
            if self.tab_refs[m].current:
                self.tab_refs[m].current.bgcolor = _BG[m] if is_active else "transparent"
                self.tab_refs[m].current.border  = ft.border.all(1, color if is_active else "transparent")
                self.tab_refs[m].current.update()
            if self.tab_text_refs[m].current:
                self.tab_text_refs[m].current.color = color if is_active else TEXT_MUT
                self.tab_text_refs[m].current.update()

    def _fire_tick(self):
        if self.on_tick:
            try:
                self.on_tick(self.remaining, self.total, self.mode, self.running)
            except Exception:
                pass

    def _start_stop(self, e):
        if not self.running:
            # remaining=0인 완료 상태에서 누르면 현재 모드로 리셋 후 시작
            if self.remaining <= 0:
                secs = 10 if self.test_mode else (
                    self.focus_minutes if self.mode == "focus" else self.rest_minutes
                ) * 60
                self.remaining = secs
                self.total     = secs
                self._update_display()
            self.running = True
            self.paused  = False
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
                threading.Thread(target=_completion_sound, daemon=True).start()
            self._on_complete()

    def _on_complete(self):
        # 대시보드 버튼을 즉시 PLAY로 업데이트 (running이 이미 False인 상태)
        self._fire_tick()

        now_str   = time.strftime("%H:%M")
        start_str = self.session_start_str or "—"
        entry = (MODE_LABELS[self.mode], start_str, now_str, "done")
        self.history.append(entry)
        score_store.add_history_entry(*entry)   # 로그아웃해도 오늘치 유지
        self._update_history()

        if self.mode == "focus":
            self.sessions_done += 1
            self._update_dots()
            if self.on_sessions_update:
                try:
                    self.on_sessions_update(self.sessions_done, self.cycle_count)
                except Exception:
                    pass
            # Firestore에 stats 업데이트
            # 테스트 모드: 세션당 1분으로 기록 (랭킹 반영 테스트 가능)
            focus_mins = self.focus_minutes if not self.test_mode else 1
            score_store.add_focus_minutes(focus_mins)
            def _update_stats():
                from datetime import date as _date
                user = session.get_user()
                if user and user.get("uid") and user.get("id_token"):
                    uid, token = user["uid"], user["id_token"]
                    # 누적 stats 업데이트
                    result = firebase.update_stats(uid, token, focus_mins, 1)
                    if "error" not in (result or {}):
                        score_store.mark_synced(focus_mins)
                    # 오늘 집중 시간 + 세션 수 즉시 동기화 (랭킹 실시간 반영)
                    today_min = score_store.get_today_focus_minutes()
                    today_sess = score_store.get_today_focus_sessions()
                    firebase.update_today_focus(uid, token, today_min,
                                                _date.today().isoformat(),
                                                today_sessions=today_sess)
            threading.Thread(target=_update_stats, daemon=True).start()

        if self.mode == "focus" and self.sessions_done >= self.cycle_count:
            threading.Thread(
                target=_notify,
                args=(
                    lang_store.t("pomo_goal_title"),
                    lang_store.t("pomo_goal_msg").format(n=self.cycle_count),
                ),
                daemon=True,
            ).start()
            self._show_all_done_dialog()
            return

        if self.mode == "focus":
            threading.Thread(
                target=_notify,
                args=(lang_store.t("pomo_focus_done_title"), lang_store.t("pomo_focus_done_msg")),
                daemon=True,
            ).start()
        else:
            threading.Thread(
                target=_notify,
                args=(lang_store.t("pomo_break_done_title"), lang_store.t("pomo_break_done_msg")),
                daemon=True,
            ).start()

        next_mode  = "rest" if self.mode == "focus" else "focus"
        next_label = lang_store.t(MODE_LABELS[next_mode])

        if self.mode == "focus":
            self._set_mode(next_mode)
            self.session_start_str = time.strftime("%H:%M")
            self.running = True
            self.paused  = False
            if self.play_icon_ref.current:
                self.play_icon_ref.current.icon = ft.Icons.PAUSE
                self.play_icon_ref.current.update()
            self._fire_tick()  # 대시보드에 running=True 상태 즉시 전달
            self.page.run_task(self._tick_async)
        elif self.auto_start:
            self._set_mode(next_mode)
            self.session_start_str = time.strftime("%H:%M")
            self.running = True
            self.paused  = False
            if self.play_icon_ref.current:
                self.play_icon_ref.current.icon = ft.Icons.PAUSE
                self.play_icon_ref.current.update()
            self._fire_tick()  # 대시보드에 running=True 상태 즉시 전달
            self.page.run_task(self._tick_async)
        else:
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
                        ft.Text(lang_store.t("goal_achieved"), size=18, weight=ft.FontWeight.W_400,
                                color=ACCENT, font_family="DOSSaemmul",
                                text_align=ft.TextAlign.CENTER),
                        ft.Text(lang_store.t("cycles_complete_fmt").format(n=self.cycle_count),
                                size=15, color=TEXT_SEC, font_family="DOSSaemmul",
                                text_align=ft.TextAlign.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                padding=ft.padding.only(left=20, top=16, right=20, bottom=8),
            ),
            actions=[
                ft.TextButton(lang_store.t("start_again"), style=ft.ButtonStyle(color=ACCENT),
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
                        ft.Text(lang_store.t("session_complete_dlg"), size=18, weight=ft.FontWeight.W_400,
                                color=ACCENT, font_family="DOSSaemmul",
                                text_align=ft.TextAlign.CENTER),
                        ft.Text(lang_store.t("next_session_fmt").format(label=next_label),
                                size=15, color=TEXT_SEC, font_family="DOSSaemmul",
                                text_align=ft.TextAlign.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                padding=ft.padding.only(left=20, top=16, right=20, bottom=8),
            ),
            actions=[
                ft.TextButton(lang_store.t("start_next_session"), style=ft.ButtonStyle(color=ACCENT),
                              on_click=go_next),
            ],
        )
        self.page.dialog.open = True
        try:
            self.page.update()
        except Exception:
            pass

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
                self.mode_label_ref.current.value = lang_store.t(MODE_LABELS[self.mode])
                self.mode_label_ref.current.update()
        except Exception:
            pass
        if self.on_tick:
            try:
                self.on_tick(self.remaining, self.total, self.mode, self.running)
            except Exception:
                pass

    def _dot_controls(self) -> list:
        mode_color = MODE_COLORS[self.mode]
        mode_lt    = ACCENT_LT if self.mode == "focus" else "#EDE9FF"
        dots = []
        for i in range(self.cycle_count):
            done       = i < self.sessions_done
            is_current = i == self.sessions_done and self.sessions_done < self.cycle_count
            dots.append(ft.Container(
                width=10, height=10,
                bgcolor=ACCENT if done else (mode_lt if is_current else BORDER),
                border_radius=5,
                border=ft.border.all(1.5,
                    ACCENT if done else (mode_color if is_current else BORDER)),
            ))
        return dots

    def _update_dots(self):
        if self.session_dots_ref.current:
            self.session_dots_ref.current.controls = self._dot_controls()
            self.session_dots_ref.current.update()
        if self.cycle_text_ref.current:
            self.cycle_text_ref.current.value = lang_store.t("focus_progress_fmt").format(done=self.sessions_done, goal=self.cycle_count)
            self.cycle_text_ref.current.update()

    def _update_history(self):
        if self.history_col_ref.current:
            self.history_col_ref.current.controls = [
                ft.Text(lang_store.t("today_log"), size=16, weight=ft.FontWeight.W_400,
                        color=TEXT_PRI, font_family="DOSSaemmul"),
                ft.Container(height=10),
                *self._history_rows(),
            ]
            try:
                self.history_col_ref.current.update()
            except Exception:
                pass

    def _history_rows(self) -> list:
        # 구 번역 문자열 → 표준 키로 정규화
        _TO_KEY = {
            "focus_session":  "focus_session",
            "break_session":  "break_session",
            "집중 세션":       "focus_session",
            "휴식 세션":       "break_session",
            "Focus Session":  "focus_session",
            "Break Session":  "break_session",
            "Focus":          "focus_session",
            "집중":            "focus_session",
        }
        _focus_keys = {"focus_session", "Focus Session", "집중 세션", "Focus", "집중"}
        rows = []
        for mode_l, start, end, _ in self.history:
            is_focus = mode_l in _focus_keys
            color = ACCENT if is_focus else PINK
            key   = _TO_KEY.get(mode_l, mode_l)
            label = lang_store.t(key) if key in ("focus_session", "break_session") else mode_l
            rows.append(ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(width=8, height=8, bgcolor=color, border_radius=4),
                        ft.Text(label, size=15, color=TEXT_PRI,
                                font_family="DOSSaemmul", expand=True),
                        ft.Text(f"{start} → {end}", size=13, color=TEXT_MUT,
                                font_family="DOSSaemmul"),
                        ft.Container(
                            content=ft.Text(lang_store.t("stat_done"), size=12, color=ACCENT,
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

    def build(self) -> ft.Container:

        _TAB_BG = {"focus": ACCENT_LT, "rest": "#EDE9FF"}

        def _mode_tab(mode: str) -> ft.Container:
            is_active = mode == self.mode
            color = MODE_COLORS[mode]
            return ft.Container(
                ref=self.tab_refs[mode],
                content=ft.Text(
                    ref=self.tab_text_refs[mode],
                    value=lang_store.t(MODE_LABELS[mode]),
                    size=14, weight=ft.FontWeight.W_400,
                    color=color if is_active else TEXT_MUT,
                    font_family="DOSSaemmul",
                ),
                bgcolor=_TAB_BG[mode] if is_active else "transparent",
                border_radius=8,
                padding=ft.padding.only(left=14, top=7, right=14, bottom=7),
                on_click=lambda _, m=mode: self._set_mode(m),
                border=ft.border.all(1, color if is_active else "transparent"),
            )

        RING = 155

        timer_area = card(
            ft.Column(
                controls=[
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Row(
                            controls=[_mode_tab("focus"), _mode_tab("rest")],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=8,
                        ),
                        bgcolor=BG_CARD2, border_radius=10,
                        padding=6, border=ft.border.all(1, BORDER),
                    ),
                    ft.Container(height=14),
                    ft.Container(
                        width=RING, height=RING,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Stack(controls=[
                            ft.ProgressRing(
                                ref=self.ring_ref,
                                value=1.0, width=RING, height=RING,
                                stroke_width=10, color=ACCENT, bgcolor=BORDER,
                            ),
                            ft.Container(
                                width=RING, height=RING,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Column(
                                    controls=[
                                        ft.Text(
                                            ref=self.time_ref,
                                            value=self._fmt(self.remaining),
                                            size=38, weight=ft.FontWeight.W_500,
                                            color=TEXT_PRI, font_family="DOSSaemmul",
                                            text_align=ft.TextAlign.CENTER,
                                        ),
                                        ft.Text(
                                            ref=self.mode_label_ref,
                                            value=lang_store.t(MODE_LABELS[self.mode]),
                                            size=13, color=TEXT_MUT,
                                            font_family="DOSSaemmul",
                                            text_align=ft.TextAlign.CENTER,
                                        ),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    spacing=2,
                                ),
                            ),
                        ]),
                    ),
                    ft.Container(height=10),
                    ft.Row(
                        ref=self.session_dots_ref,
                        controls=self._dot_controls(),
                        spacing=6,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Text(
                        ref=self.cycle_text_ref,
                        value=lang_store.t("focus_progress_fmt").format(done=self.sessions_done, goal=self.cycle_count),
                        size=13, color=TEXT_MUT,
                        font_family="DOSSaemmul",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=12),
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
                                    size=26, color="#F0F9F8",
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
                                tooltip="Skip to next session",
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=16,
                    ),
                    ft.Container(expand=True),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
                expand=True,
            ),
            padding=18,
            expand=2,
        )

        # ── Settings ──────────────────────────────────────────────────
        def on_focus_change(e):
            self.focus_minutes = int(round(e.control.value / 5) * 5)
            if self.focus_label_ref.current:
                self.focus_label_ref.current.value = lang_store.t("focus_time_fmt").format(n=self.focus_minutes)
                self.focus_label_ref.current.update()
            if self.mode == "focus" and not self.running:
                self.remaining = self.focus_minutes * 60
                self.total     = self.remaining
                self._update_display()
            score_store.set_focus_goal(self.cycle_count, self.focus_minutes)

        def on_rest_change(e):
            self.rest_minutes = int(round(e.control.value / 5) * 5)
            if self.rest_label_ref.current:
                self.rest_label_ref.current.value = lang_store.t("break_time_fmt").format(n=self.rest_minutes)
                self.rest_label_ref.current.update()
            if self.mode == "rest" and not self.running:
                self.remaining = self.rest_minutes * 60
                self.total     = self.remaining
                self._update_display()

        def on_cycle_change(e):
            self.cycle_count = int(round(e.control.value))
            if self.cycle_label_ref.current:
                self.cycle_label_ref.current.value = lang_store.t("goal_cycles_fmt").format(n=self.cycle_count)
                self.cycle_label_ref.current.update()
            if self.sessions_done > self.cycle_count:
                self.sessions_done = 0
            self._update_dots()
            if self.on_sessions_update:
                try:
                    self.on_sessions_update(self.sessions_done, self.cycle_count)
                except Exception:
                    pass
            score_store.set_focus_goal(self.cycle_count, self.focus_minutes)

        def toggle_test_mode(e):
            self.test_mode = not self.test_mode
            self.running   = False
            self.paused    = False

            if self.test_mode:
                self._saved_cycle_count = self.cycle_count
                self.cycle_count = 2
            else:
                self.cycle_count = getattr(self, "_saved_cycle_count", self.cycle_count)

            self.sessions_done = 0
            self._update_dots()

            if self.test_btn_ref.current:
                self.test_btn_ref.current.bgcolor = DANGER if self.test_mode else BG_CARD2
                self.test_btn_ref.current.border  = ft.border.all(1.5, DANGER if self.test_mode else BORDER)
                lbl: ft.Text = self.test_btn_ref.current.content
                lbl.value = lang_store.t("test_mode_on") if self.test_mode else lang_store.t("test_mode")
                lbl.color = "#F0F9F8" if self.test_mode else TEXT_MUT
                self.test_btn_ref.current.update()

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
                    ft.Text(lang_store.t("settings"), size=16, weight=ft.FontWeight.W_400,
                            color=TEXT_PRI, font_family="DOSSaemmul"),
                    ft.Container(height=8),
                    ft.Column(controls=[
                        ft.Text(ref=self.focus_label_ref,
                                value=lang_store.t("focus_time_fmt").format(n=self.focus_minutes),
                                size=14, color=TEXT_SEC, font_family="DOSSaemmul"),
                        ft.Slider(
                            min=5, max=60, value=self.focus_minutes,
                            divisions=11,
                            active_color=ACCENT, inactive_color=BORDER, thumb_color=ACCENT,
                            on_change=on_focus_change,
                        ),
                    ], spacing=2),
                    ft.Column(controls=[
                        ft.Text(ref=self.rest_label_ref,
                                value=lang_store.t("break_time_fmt").format(n=self.rest_minutes),
                                size=14, color=TEXT_SEC, font_family="DOSSaemmul"),
                        ft.Slider(
                            min=5, max=30, value=self.rest_minutes,
                            divisions=5,
                            active_color=PINK, inactive_color=BORDER, thumb_color=PINK,
                            on_change=on_rest_change,
                        ),
                    ], spacing=2),
                    ft.Column(controls=[
                        ft.Text(ref=self.cycle_label_ref,
                                value=lang_store.t("goal_cycles_fmt").format(n=self.cycle_count),
                                size=14, color=TEXT_SEC, font_family="DOSSaemmul"),
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
                    ft.Container(
                        ref=self.test_btn_ref,
                        content=ft.Text(lang_store.t("test_mode"), size=14,
                                        color=TEXT_MUT, font_family="DOSSaemmul",
                                        text_align=ft.TextAlign.CENTER),
                        bgcolor=BG_CARD2,
                        border_radius=8,
                        border=ft.border.all(1.5, BORDER),
                        padding=ft.padding.symmetric(vertical=8),
                        alignment=ft.Alignment(0, 0),
                        on_click=toggle_test_mode,
                        tooltip="Set focus/break to 10s each",
                        expand=True,
                    ),
                    ft.Divider(color=BORDER, height=1),
                    ft.Container(height=4),
                    ft.Row(controls=[
                        ft.Text(lang_store.t("sound_alerts"), size=14, color=TEXT_SEC,
                                font_family="DOSSaemmul", expand=True),
                        ft.Switch(value=True, active_color=ACCENT, scale=0.8,
                                  on_change=toggle_sound),
                    ]),
                    ft.Row(controls=[
                        ft.Text(lang_store.t("auto_start"), size=14, color=TEXT_SEC,
                                font_family="DOSSaemmul", expand=True),
                        ft.Switch(value=True, active_color=ACCENT, scale=0.8,
                                  on_change=toggle_auto),
                    ]),
                    ft.Container(expand=True),
                ],
                spacing=10,
                expand=True,
            ),
            padding=18,
            expand=True,
        )

        history_card = card(
            ft.Column(
                ref=self.history_col_ref,
                controls=[
                    ft.Text(lang_store.t("today_log"), size=16, weight=ft.FontWeight.W_400,
                            color=TEXT_PRI, font_family="DOSSaemmul"),
                    ft.Container(height=10),
                    *self._history_rows(),
                ],
                spacing=8,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            padding=18,
            expand=1,
        )

        right_col = ft.Column(
            controls=[settings],
            width=250, spacing=0,
        )

        left_col = ft.Column(
            controls=[timer_area, ft.Container(height=10), history_card],
            expand=True, spacing=0,
        )

        BODY_H = 580

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(lang_store.t("pomo_title"), size=26, weight=ft.FontWeight.W_400,
                                    color=TEXT_PRI, font_family="DOSSaemmul"),
                            ft.Text(lang_store.t("pomo_sub"),
                                    size=15, color=TEXT_SEC, font_family="DOSSaemmul"),
                        ],
                        spacing=2,
                    ),
                    ft.Container(height=12),
                    ft.Row(
                        controls=[
                            left_col,
                            ft.Container(width=16),
                            right_col,
                        ],
                        height=BODY_H,
                        vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                    ),
                ],
                spacing=0,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
            padding=ft.padding.only(left=28, top=20, right=28, bottom=20),
            bgcolor=BG_BASE,
        )
