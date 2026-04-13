import threading
import time

_lock          = threading.Lock()
_last_score    = [100]
_monitoring    = [False]
_snoozed_until = [0.0]

ALERT_THRESHOLD = 80
ALERT_INTERVAL  = 60
CHECK_INTERVAL  = 5
BAD_COUNT_LIMIT = 3


def set_score(score: int):
    with _lock:
        _last_score[0] = score

def get_score() -> int:
    with _lock:
        return _last_score[0]

def set_monitoring(active: bool):
    with _lock:
        _monitoring[0] = active

def is_monitoring() -> bool:
    with _lock:
        return _monitoring[0]

def snooze(seconds: int = 300):
    with _lock:
        _snoozed_until[0] = time.time() + seconds


def _show_popup(score: int):
    try:
        import tkinter as tk

        if score < 60:
            accent, emoji, headline, detail = "#FF5C5C", "🚨", "거북목 위험!", "머리를 뒤로 당기고 등을 펴주세요"
        elif score < 70:
            accent, emoji, headline, detail = "#FFB347", "⚠️", "자세가 나빠졌어요", "잠깐 스트레칭 후 자세를 교정해보세요"
        else:
            accent, emoji, headline, detail = "#00C9A7", "💡", "자세를 확인해주세요", "조금만 신경 쓰면 훨씬 좋아질 거예요"

        W, H = 340, 180

        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.0)
        root.configure(bg="#FFFFFF")

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x = sw - W - 20
        y_final = sh - H - 20 - 48
        y_start = sh + H

        root.geometry(f"{W}x{H}+{x}+{y_start}")

        outer = tk.Frame(root, bg=accent, padx=2, pady=2)
        outer.pack(fill="both", expand=True)

        inner = tk.Frame(outer, bg="#FFFFFF")
        inner.pack(fill="both", expand=True)

        tk.Frame(inner, bg=accent, width=5).pack(side="left", fill="y")

        content = tk.Frame(inner, bg="#FFFFFF", padx=14, pady=12)
        content.pack(side="left", fill="both", expand=True)

        tk.Label(content, text="FocusMate", bg="#FFFFFF",
                 fg="#9DA8B7", font=("Segoe UI", 8)).pack(anchor="w")

        top_row = tk.Frame(content, bg="#FFFFFF")
        top_row.pack(anchor="w", pady=(2, 0))
        tk.Label(top_row, text=emoji, bg="#FFFFFF",
                 font=("Segoe UI Emoji", 16)).pack(side="left", padx=(0, 8))
        tk.Label(top_row, text=headline, bg="#FFFFFF",
                 fg="#1A1D23", font=("Segoe UI", 13, "bold")).pack(side="left")

        tk.Label(content, text=f"  자세 점수: {score}점  ",
                 bg=accent, fg="#FFFFFF",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(6, 0))

        tk.Label(content, text=detail, bg="#FFFFFF",
                 fg="#5A6375", font=("Segoe UI", 9),
                 wraplength=240, justify="left").pack(anchor="w", pady=(6, 10))

        btn_row = tk.Frame(content, bg="#FFFFFF")
        btn_row.pack(anchor="w")

        def on_fix():
            slide_out()

        def on_snooze():
            snooze(300)
            slide_out()

        tk.Button(btn_row, text="✓  교정하기",
                  bg=accent, fg="#FFFFFF",
                  font=("Segoe UI", 9, "bold"),
                  relief="flat", bd=0, padx=12, pady=5,
                  cursor="hand2", activebackground=accent,
                  command=on_fix).pack(side="left", padx=(0, 8))

        tk.Button(btn_row, text="🕐  5분 후 알림",
                  bg="#F4F6F8", fg="#5A6375",
                  font=("Segoe UI", 9),
                  relief="flat", bd=0, padx=12, pady=5,
                  cursor="hand2", activebackground="#F4F6F8",
                  command=on_snooze).pack(side="left")

        close = tk.Label(inner, text="✕", bg="#FFFFFF",
                         fg="#9DA8B7", font=("Segoe UI", 10),
                         cursor="hand2")
        close.place(relx=1.0, x=-10, y=8, anchor="ne")
        close.bind("<Button-1>", lambda e: slide_out())

        def slide_in(step=0):
            if step > 20:
                root.after(8000, slide_out)
                return
            t = step / 20
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
                root.geometry(f"{W}x{H}+{x}+{int(y_final + (sh - y_final) * t**2)}")
                root.attributes("-alpha", max(0.0, 1.0 - t))
                root.after(12, lambda: slide_out(step + 1))
            except Exception:
                pass

        slide_in()
        root.mainloop()

    except Exception:
        _send_powershell_toast(score)


def _send_powershell_toast(score: int):
    try:
        import subprocess, sys
        if sys.platform != "win32":
            return
        title = "FocusMate — 자세 경고"
        msg   = f"자세 점수 {score}점 / 자세를 교정해주세요!"
        ps = (
            "Add-Type -AssemblyName System.Windows.Forms;"
            "$n=[System.Windows.Forms.NotifyIcon]::new();"
            "$n.Icon=[System.Drawing.SystemIcons]::Warning;"
            "$n.Visible=$true;"
            f"$n.ShowBalloonTip(7000,'{title}','{msg}',"
            "[System.Windows.Forms.ToolTipIcon]::Warning);"
            "Start-Sleep 8;$n.Dispose()"
        )
        subprocess.Popen(
            ["powershell", "-WindowStyle", "Hidden", "-Command", ps],
            creationflags=0x08000000,
        )
    except Exception:
        pass


def start_alert_daemon():
    def _loop():
        bad_count  = 0
        last_alert = 0.0
        while True:
            time.sleep(CHECK_INTERVAL)
            if not is_monitoring():
                bad_count = 0
                continue
            score = get_score()
            now   = time.time()
            if score < ALERT_THRESHOLD:
                bad_count += 1
            else:
                bad_count = 0
            snoozed = now < _snoozed_until[0]
            cooled  = (now - last_alert) >= ALERT_INTERVAL
            if bad_count >= BAD_COUNT_LIMIT and not snoozed and cooled:
                last_alert = now
                bad_count  = 0
                threading.Thread(target=_show_popup, args=(score,), daemon=True).start()

    threading.Thread(target=_loop, daemon=True).start()
