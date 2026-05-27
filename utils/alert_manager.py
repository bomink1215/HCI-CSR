import threading
import time
import os

_lock          = threading.Lock()
_last_score    = [100]
_monitoring    = [False]
_snoozed_until = [0.0]
_posture_type  = ["good"]   # ★ 현재 자세 유형 저장

ALERT_THRESHOLD = 80
ALERT_INTERVAL  = 60
CHECK_INTERVAL  = 5
BAD_COUNT_LIMIT = 3

# ── 자세 유형 상수 (posture.py와 동일) ──────────────────────────
POSTURE_TURTLE  = "turtle_neck"
POSTURE_ROUNDED = "rounded_back"
POSTURE_TILT    = "shoulder_tilt"
POSTURE_OK      = "good"

# ── 유형별 이미지 경로 설정 ──────────────────────────────────────
# assets/ 폴더 안에 아래 파일을 넣어두세요.
# 파일이 없으면 이미지 없이 텍스트만 표시됩니다.
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

POSTURE_IMAGES: dict[str, str] = {
    POSTURE_TURTLE:  os.path.join(_BASE_DIR, "assets", "alert_turtle_neck.png"),
    POSTURE_ROUNDED: os.path.join(_BASE_DIR, "assets", "alert_rounded_back.png"),
    POSTURE_TILT:    os.path.join(_BASE_DIR, "assets", "alert_shoulder_tilt.png"),
}

# ── 유형별 UI 설정 ───────────────────────────────────────────────
POSTURE_META: dict[str, dict] = {
    POSTURE_TURTLE: {
        "accent":  "#FF5C5C",
        "emoji":   "🐢",
        "headline": "Turtle Neck Detected!",
        "detail":  "Pull your chin in and bring\nyour ears above your shoulders.",
    },
    POSTURE_ROUNDED: {
        "accent":  "#FFB347",
        "emoji":   "🪑",
        "headline": "Hunched Back Detected!",
        "detail":  "Straighten your back and gently\npull your shoulders back.",
    },
    POSTURE_TILT: {
        "accent":  "#9B8FFF",
        "emoji":   "⚖️",
        "headline": "Shoulder Imbalance Detected!",
        "detail":  "Level your shoulders and\nsit in a balanced position.",
    },
}


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

def set_posture_type(ptype: str):
    """posture.py 카메라 워커에서 매 프레임 호출"""
    with _lock:
        _posture_type[0] = ptype

def get_posture_type() -> str:
    with _lock:
        return _posture_type[0]


# ── 팝업 ─────────────────────────────────────────────────────────
def _show_popup(score: int, posture_type: str):
    try:
        import tkinter as tk
        from PIL import Image, ImageTk   # Pillow 필요: pip install Pillow

        meta   = POSTURE_META.get(posture_type, POSTURE_META[POSTURE_TURTLE])
        accent = meta["accent"]

        # 이미지 로드 (없으면 None)
        img_path = POSTURE_IMAGES.get(posture_type, "")
        pil_img  = None
        if img_path and os.path.exists(img_path):
            try:
                pil_img = Image.open(img_path)
            except Exception:
                pil_img = None

        # 이미지 유무에 따라 팝업 높이 결정
        IMG_W, IMG_H = 320, 160   # 이미지 표시 크기
        W = 340
        H = (IMG_H + 130) if pil_img else 190

        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.0)
        root.configure(bg="#FFFFFF")

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x       = sw - W - 20
        y_final = sh - H - 20 - 48
        y_start = sh + H

        root.geometry(f"{W}x{H}+{x}+{y_start}")

        # ── 바깥 테두리 프레임 ──────────────────────────────────────
        outer = tk.Frame(root, bg="#FFFFFF", padx=0, pady=0)
        outer.pack(fill="both", expand=True)

        inner = tk.Frame(outer, bg="#FFFFFF")
        inner.pack(fill="both", expand=True)

        # 왼쪽 컬러 바
        
        content = tk.Frame(inner, bg="#FFFFFF", padx=12, pady=6)
        content.pack(side="left", fill="both", expand=True)

        # ── 이미지 영역 ─────────────────────────────────────────────
        if pil_img:
            pil_img = pil_img.resize((IMG_W, IMG_H), Image.LANCZOS)
            tk_img  = ImageTk.PhotoImage(pil_img)
            img_lbl = tk.Label(content, image=tk_img, bg="#FFFFFF",
                               bd=0, relief="flat")
            img_lbl.image = tk_img   # 참조 유지
            img_lbl.pack(anchor="w", pady=(0, 4))

        # ── 앱 이름 ─────────────────────────────────────────────────
        tk.Label(content, text="FocusMate", bg="#FFFFFF",
                 fg="#9DA8B7", font=("Segoe UI", 8)).pack(anchor="w")

        # ── 헤드라인 행 ─────────────────────────────────────────────
        top_row = tk.Frame(content, bg="#FFFFFF")
        top_row.pack(anchor="w", pady=(1, 0))
        tk.Label(top_row, text=meta["emoji"], bg="#FFFFFF",
                 font=("Segoe UI Emoji", 15)).pack(side="left", padx=(0, 6))
        tk.Label(top_row, text=meta["headline"], bg="#FFFFFF",
                 fg="#1A1D23", font=("Segoe UI", 12, "bold")).pack(side="left")

        # ── 점수 배지 ───────────────────────────────────────────────
        tk.Label(content, text=f"  Posture Score: {score}  ",
                 bg=accent, fg="#FFFFFF",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(3, 0))


        # ── 버튼 행 ─────────────────────────────────────────────────
        btn_row = tk.Frame(content, bg="#FFFFFF")
        btn_row.pack(anchor="w")

        def on_fix():
            slide_out()

        def on_snooze():
            snooze(300)
            slide_out()

        tk.Button(btn_row, text="✓  Fix Now",
                  bg=accent, fg="#FFFFFF",
                  font=("Segoe UI", 9, "bold"),
                  relief="flat", bd=0, padx=12, pady=5,
                  cursor="hand2", activebackground=accent,
                  command=on_fix).pack(side="left", padx=(0, 8))

        tk.Button(btn_row, text="🕐  Remind in 5 min",
                  bg="#F4F6F8", fg="#5A6375",
                  font=("Segoe UI", 9),
                  relief="flat", bd=0, padx=12, pady=5,
                  cursor="hand2", activebackground="#F4F6F8",
                  command=on_snooze).pack(side="left")

        # ── 닫기 버튼 ───────────────────────────────────────────────
        close_lbl = tk.Label(inner, text="✕", bg="#FFFFFF",
                             fg="#9DA8B7", font=("Segoe UI", 10),
                             cursor="hand2")
        close_lbl.place(relx=1.0, x=-10, y=8, anchor="ne")
        close_lbl.bind("<Button-1>", lambda e: slide_out())

        # ── 슬라이드 애니메이션 ─────────────────────────────────────
        def slide_in(step=0):
            if step > 20:
                root.after(8000, slide_out)
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
                root.geometry(f"{W}x{H}+{x}+{int(y_final + (sh - y_final) * t**2)}")
                root.attributes("-alpha", max(0.0, 1.0 - t))
                root.after(12, lambda: slide_out(step + 1))
            except Exception:
                pass

        slide_in()
        root.mainloop()

    except ImportError:
        # Pillow 없으면 이미지 없이 기본 팝업으로 폴백
        _show_popup_no_image(score, posture_type)
    except Exception:
        import traceback
        log_path = os.path.join(_BASE_DIR, "popup_error.log")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(traceback.format_exc())
        _send_powershell_toast(score)


def _show_popup_no_image(score: int, posture_type: str):
    """Pillow 없을 때 — 이미지 제외하고 텍스트만 표시"""
    try:
        import tkinter as tk

        meta   = POSTURE_META.get(posture_type, POSTURE_META[POSTURE_TURTLE])
        accent = meta["accent"]
        W, H   = 340, 190

        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.0)
        root.configure(bg="#FFFFFF")

        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x       = sw - W - 20
        y_final = sh - H - 20 - 48
        y_start = sh + H
        root.geometry(f"{W}x{H}+{x}+{y_start}")

        outer = tk.Frame(root, bg="#FFFFFF", padx=0, pady=0)
        outer.pack(fill="both", expand=True)
        inner = tk.Frame(outer, bg="#FFFFFF")
        inner.pack(fill="both", expand=True)
        
        content = tk.Frame(inner, bg="#FFFFFF", padx=14, pady=12)
        content.pack(side="left", fill="both", expand=True)

        tk.Label(content, text="FocusMate", bg="#FFFFFF",
                 fg="#9DA8B7", font=("Segoe UI", 8)).pack(anchor="w")

        top_row = tk.Frame(content, bg="#FFFFFF")
        top_row.pack(anchor="w", pady=(1, 0))
        tk.Label(top_row, text=meta["emoji"], bg="#FFFFFF",
                 font=("Segoe UI Emoji", 16)).pack(side="left", padx=(0, 8))
        tk.Label(top_row, text=meta["headline"], bg="#FFFFFF",
                 fg="#1A1D23", font=("Segoe UI", 13, "bold")).pack(side="left")

        tk.Label(content, text=f"  Posture Score: {score}  ",
                 bg=accent, fg="#FFFFFF",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(6, 0))


        btn_row = tk.Frame(content, bg="#FFFFFF")
        btn_row.pack(anchor="w")

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

        tk.Button(btn_row, text="✓  Fix Now",
                  bg=accent, fg="#FFFFFF",
                  font=("Segoe UI", 9, "bold"),
                  relief="flat", bd=0, padx=12, pady=5,
                  cursor="hand2", activebackground=accent,
                  command=slide_out).pack(side="left", padx=(0, 8))

        tk.Button(btn_row, text="🕐  Remind in 5 min",
                  bg="#F4F6F8", fg="#5A6375",
                  font=("Segoe UI", 9),
                  relief="flat", bd=0, padx=12, pady=5,
                  cursor="hand2", activebackground="#F4F6F8",
                  command=lambda: (snooze(300), slide_out())).pack(side="left")

        close_lbl = tk.Label(inner, text="✕", bg="#FFFFFF",
                             fg="#9DA8B7", font=("Segoe UI", 10), cursor="hand2")
        close_lbl.place(relx=1.0, x=-10, y=8, anchor="ne")
        close_lbl.bind("<Button-1>", lambda e: slide_out())

        def slide_in(step=0):
            if step > 20:
                root.after(8000, slide_out)
                return
            t    = step / 20
            ease = 1 - (1 - t) ** 3
            root.geometry(f"{W}x{H}+{x}+{int(y_start + (y_final - y_start) * ease)}")
            root.attributes("-alpha", min(1.0, ease * 1.5))
            root.after(15, lambda: slide_in(step + 1))

        slide_in()
        root.mainloop()
    except Exception:
        _send_powershell_toast(score)


def _send_powershell_toast(score: int):
    try:
        import subprocess, sys
        if sys.platform != "win32":
            return
        title = "FocusMate — Posture Alert"
        msg   = f"Posture score: {score} / Please fix your posture!"
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
            ptype = get_posture_type()   # ★ 현재 자세 유형 읽기
            now   = time.time()
            if score < ALERT_THRESHOLD:
                bad_count += 1
            else:
                bad_count = 0
            snoozed = now < _snoozed_until[0]
            cooled  = (now - last_alert) >= ALERT_INTERVAL
            if bad_count >= BAD_COUNT_LIMIT and not snoozed and cooled \
                    and ptype != POSTURE_OK:   # 정상 자세일 때는 알림 없음
                last_alert = now
                bad_count  = 0
                threading.Thread(
                    target=_show_popup,
                    args=(score, ptype),
                    daemon=True,
                ).start()

    threading.Thread(target=_loop, daemon=True).start()
