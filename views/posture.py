import flet as ft
from components.ui import card
import threading
import time
import os
import tempfile
import statistics
from utils import alert_manager, score_store
from utils import lang as lang_store

BG_BASE   = "#F0F9F8"
BG_CARD   = "#F4F6F8"
BG_CARD2  = "#EAECEF"
ACCENT    = "#7AC3B8"
ACCENT_LT = "#D6F5EF"
DANGER    = "#FF5C5C"
WARNING   = "#FFB347"
TEXT_PRI  = "#1A1D23"
TEXT_SEC  = "#5A6375"
TEXT_MUT  = "#9DA8B7"
BORDER    = "#E2E6EC"

_MODEL_PATHS = [
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "pose_landmarker.task"),
    os.path.join(os.getcwd(), "pose_landmarker.task"),
    os.path.join(tempfile.gettempdir(), "pose_landmarker.task"),
]

def _find_model():
    for p in _MODEL_PATHS:
        if os.path.exists(p):
            return p
    return None

_FONT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "assets", "fonts", "DOSSaemmul.ttf"
)
_pil_font_cache: dict = {}

def _put_text(frame, text: str, pos: tuple, font_size: int, color_bgr: tuple):
    """cv2.putText 대체: 비ASCII(한글 등) 포함 시 PIL로 렌더링."""
    if all(ord(c) < 128 for c in text):
        import cv2 as _c
        _c.putText(frame, text, pos,
                   _c.FONT_HERSHEY_SIMPLEX, font_size / 26,
                   color_bgr, 1, _c.LINE_AA)
        return frame
    try:
        from PIL import Image, ImageDraw, ImageFont
        import numpy as np, cv2 as _c
        if font_size not in _pil_font_cache:
            try:
                _pil_font_cache[font_size] = ImageFont.truetype(_FONT_PATH, font_size)
            except Exception:
                _pil_font_cache[font_size] = ImageFont.load_default()
        pil = Image.fromarray(_c.cvtColor(frame, _c.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil)
        r, g, b = color_bgr[2], color_bgr[1], color_bgr[0]
        draw.text(pos, text, font=_pil_font_cache[font_size], fill=(r, g, b))
        result = _c.cvtColor(np.array(pil), _c.COLOR_RGB2BGR)
        frame[:] = result
    except Exception:
        pass
    return frame


POSTURE_ROUNDED = "rounded_back"
POSTURE_SLOUCH  = "slouch"
POSTURE_TILT    = "shoulder_tilt"
POSTURE_OK      = "good"

_calib = {
    "done":     False,
    "ear_y":    None,
    "face_w":   None,
    "tilt_raw": None,
}


def reset_calibration():
    _calib.update(done=False, ear_y=None, face_w=None, tilt_raw=None)


def _vis(lm) -> float:
    return getattr(lm, "visibility", 1.0) or 0.0


def _extract_features(landmarks):
    l_ear = landmarks[7]; r_ear = landmarks[8]
    l_sh  = landmarks[11]; r_sh = landmarks[12]

    ear_vis = min(_vis(l_ear), _vis(r_ear))
    sh_vis  = min(_vis(l_sh),  _vis(r_sh))

    face_w = abs(l_ear.x - r_ear.x)
    if face_w < 0.02 or ear_vis < 0.3:
        return None

    ear_mid_y = (l_ear.y + r_ear.y) / 2

    feat = {
        "face_w":  face_w,
        "ear_y":   ear_mid_y,
        "tilt_raw": None,
        "sh_vis":  sh_vis,
    }

    if sh_vis > 0.4:
        feat["tilt_raw"]  = abs(l_sh.y - r_sh.y) / face_w
        feat["tilt_side"] = "Right" if l_sh.y > r_sh.y else "Left"

    return feat


def _calc_score(feat: dict) -> tuple:
    if not _calib["done"]:
        return 100, [lang_store.t("waiting_calib")], POSTURE_OK, {}, {}

    score  = 100
    issues = []
    ded    = {POSTURE_ROUNDED: 0, POSTURE_SLOUCH: 0, POSTURE_TILT: 0}

    base_ear_y  = _calib["ear_y"]
    base_face_w = _calib["face_w"]
    base_tilt   = _calib["tilt_raw"]

    zoom      = (feat["face_w"] - base_face_w) / base_face_w
    ear_drop  = feat["ear_y"] - base_ear_y

    dbg = {
        "zoom":     round(zoom,     3),
        "ear_drop": round(ear_drop, 3),
        "face_w":   round(feat["face_w"], 3),
        "base_fw":  round(base_face_w,    3),
    }

    SLOUCH_EAR_MARGIN = 0.06
    if ear_drop > SLOUCH_EAR_MARGIN:
        excess = ear_drop - SLOUCH_EAR_MARGIN
        d = min(int(excess * 350), 45)
        score -= d
        ded[POSTURE_SLOUCH] += d
        issues.append(lang_store.t("issue_slouch"))

    ROUNDED_MARGIN = 0.10
    if zoom > ROUNDED_MARGIN and ded[POSTURE_SLOUCH] == 0:
        excess = zoom - ROUNDED_MARGIN
        d = min(int(excess * 280), 40)
        score -= d
        ded[POSTURE_ROUNDED] += d
        issues.append(lang_store.t("issue_rounded"))

    TILT_MARGIN = 0.12
    if base_tilt is not None and feat.get("tilt_raw") is not None:
        delta_tilt = feat["tilt_raw"] - base_tilt
        if delta_tilt > TILT_MARGIN:
            excess = delta_tilt - TILT_MARGIN
            d = min(int(excess * 180), 35)
            score -= d
            ded[POSTURE_TILT] += d
            side = feat.get("tilt_side", "One")
            key = f"issue_tilt_{side.lower()}" if side.lower() in ("left", "right") else "issue_tilt_one"
            issues.append(lang_store.t(key))

    score = max(0, min(100, score))
    posture_type = POSTURE_OK
    if any(v > 0 for v in ded.values()):
        posture_type = max(ded, key=ded.get)
    if not issues:
        issues.append(lang_store.t("issue_good"))

    dbg["ded"] = dict(ded)
    return score, issues, posture_type, ded, dbg


class PostureView:
    def __init__(self, page: ft.Page):
        self.page        = page
        self.monitoring  = False
        self._thread     = None
        self._calib_done = False

        self.score_ref      = ft.Ref()
        self.status_ref     = ft.Ref()
        self.ring_ref       = ft.Ref()
        self.cam_dot_ref    = ft.Ref()
        self.cam_label_ref  = ft.Ref()
        self.cam_badge_ref  = ft.Ref()
        self.issue_col_ref  = ft.Ref()
        self.fps_ref        = ft.Ref()
        self.toggle_btn_ref = ft.Ref()
        self.calib_card_ref = ft.Ref()

        lang_store.add_listener(self._on_lang_change)

    def _run_calibration(self, landmarker, cap, mp, win_name, start_time):
        import cv2
        COUNTDOWN = 3
        COLLECT   = 3

        phase     = "countdown"
        phase_start = time.time()

        samples_ear_y  = []
        samples_face_w = []
        samples_tilt   = []

        self._set_status(lang_store.t("status_sit_up"))

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            h, w  = frame.shape[:2]

            now     = time.time()
            elapsed = now - phase_start

            rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            ts_ms  = int((now - start_time) * 1000)
            try:
                result = landmarker.detect_for_video(mp_img, ts_ms)
            except Exception:
                result = None

            feat = None
            if result and result.pose_landmarks:
                feat = _extract_features(result.pose_landmarks[0])
                if feat:
                    pts = [(int(l.x * w), int(l.y * h))
                           for l in result.pose_landmarks[0]]
                    SKEL = [(11,12),(11,13),(13,15),(12,14),(14,16)]
                    for a, b in SKEL:
                        if a < len(pts) and b < len(pts):
                            cv2.line(frame, pts[a], pts[b], (0,201,167), 2, cv2.LINE_AA)
                    for px, py in pts[:13]:
                        cv2.circle(frame, (px, py), 4, (0,201,167), -1, cv2.LINE_AA)

            overlay = frame.copy()
            cv2.rectangle(overlay, (0,0), (w, h), (244,246,248), -1)
            cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

            if phase == "countdown":
                remaining = int(COUNTDOWN - elapsed) + 1
                txt_sit   = lang_store.t("cv2_sit_up")
                txt_calib = lang_store.t("cv2_calib_in")
                sit_x  = max(14, w//2 - len(txt_sit) * 10)
                cal_x  = max(14, w//2 - len(txt_calib) * 7)
                _put_text(frame, txt_sit,   (sit_x, h//2 - 60), 28, (0,201,167))
                _put_text(frame, txt_calib, (cal_x, h//2),      20, (90,99,117))
                cv2.putText(frame, str(remaining),
                            (w//2 - 22, h//2 + 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 3.0, (0,201,167), 4, cv2.LINE_AA)

                if elapsed >= COUNTDOWN:
                    phase       = "collect"
                    phase_start = time.time()

            elif phase == "collect":
                remaining = COLLECT - elapsed
                bar_w = int((elapsed / COLLECT) * (w - 60))
                txt_hold = lang_store.t("cv2_hold_still")
                hold_x   = max(14, w//2 - len(txt_hold) * 8)
                _put_text(frame, txt_hold, (hold_x, h//2 - 20), 22, (0,201,167))
                cv2.rectangle(frame, (30, h//2 + 20), (w-30, h//2 + 44), (220,224,230), -1)
                cv2.rectangle(frame, (30, h//2 + 20), (30 + bar_w, h//2 + 44), (0,201,167), -1)

                if not feat:
                    txt_nf  = lang_store.t("cv2_no_face")
                    nf_x    = max(14, w//2 - len(txt_nf) * 7)
                    _put_text(frame, txt_nf, (nf_x, h//2 + 80), 20, (92,92,255))

                if feat:
                    samples_ear_y.append(feat["ear_y"])
                    samples_face_w.append(feat["face_w"])
                    if feat.get("tilt_raw") is not None:
                        samples_tilt.append(feat["tilt_raw"])

                if elapsed >= COLLECT:
                    phase = "done"
                    break

            cv2.imshow(win_name, frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                return False

        if len(samples_face_w) < 5:
            self._set_status("❌ " + lang_store.t("status_calib_fail"))
            return False

        _calib["ear_y"]    = statistics.median(samples_ear_y)
        _calib["face_w"]   = statistics.median(samples_face_w)
        _calib["tilt_raw"] = statistics.median(samples_tilt) if len(samples_tilt) >= 5 else None
        _calib["done"]        = True

        self._set_calib_done(True)
        self._set_status(lang_store.t("status_analyzing"))
        return True

    def _camera_worker(self):
        try:
            import cv2
            import mediapipe as mp
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python.vision import (
                PoseLandmarker, PoseLandmarkerOptions, RunningMode
            )
        except ImportError as e:
            self._set_status(f"❌ Library error: {e}")
            self.monitoring = False
            return

        model_path = _find_model()
        if not model_path:
            self._set_status("❌ pose_landmarker.task file not found")
            self.monitoring = False
            return

        self._set_status("🔄 Loading model...")
        try:
            options = PoseLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=model_path),
                running_mode=RunningMode.VIDEO,
                min_pose_detection_confidence=0.6,
                min_pose_presence_confidence=0.6,
                min_tracking_confidence=0.6,
            )
            landmarker = PoseLandmarker.create_from_options(options)
        except Exception as e:
            self._set_status(f"❌ Model load failed: {e}")
            self.monitoring = False
            return

        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        if not cap.isOpened():
            self._set_status("❌ Cannot open camera")
            self.monitoring = False
            landmarker.close()
            return

        self._set_cam_on(True)
        alert_manager.set_monitoring(True)

        import cv2 as _cv2
        win_name   = "ZZOOK - Posture Analysis (Q: quit)"
        start_time = time.time()
        _cv2.namedWindow(win_name, _cv2.WINDOW_NORMAL)
        _cv2.resizeWindow(win_name, 800, 600)
        _cv2.setWindowProperty(win_name, _cv2.WND_PROP_TOPMOST, 1)
        _cv2.waitKey(1)  # 첫 프레임 표시 후 topmost 해제
        _cv2.setWindowProperty(win_name, _cv2.WND_PROP_TOPMOST, 0)

        reset_calibration()
        ok = self._run_calibration(landmarker, cap, mp, win_name, start_time)
        if not ok or not self.monitoring:
            cap.release()
            landmarker.close()
            _cv2.destroyAllWindows()
            alert_manager.set_monitoring(False)
            self._set_cam_on(False)
            self._set_status(lang_store.t("click_to_begin"))
            self._reset_score_ui()
            return

        SKEL_CONNS = [(11,12),(11,13),(13,15),(12,14),(14,16)]
        EMA_ALPHA  = 0.2

        fps_timer  = time.time()
        fps_count  = 0
        score      = 100
        ema_score  = 100.0
        issues     = ["Great posture! Keep it up :)"]

        try:
            while self.monitoring:
                ret, frame = cap.read()
                if not ret:
                    break

                frame = _cv2.flip(frame, 1)
                h, w  = frame.shape[:2]
                rgb   = _cv2.cvtColor(frame, _cv2.COLOR_BGR2RGB)
                mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

                ts_ms = int((time.time() - start_time) * 1000)
                try:
                    result = landmarker.detect_for_video(mp_img, ts_ms)
                except Exception:
                    result = None

                posture_type = POSTURE_OK
                ded          = {}
                dbg          = {}
                if result and result.pose_landmarks:
                    lm   = result.pose_landmarks[0]
                    feat = _extract_features(lm)
                    if feat:
                        raw_score, issues, posture_type, ded, dbg = _calc_score(feat)
                        ema_score = EMA_ALPHA * raw_score + (1 - EMA_ALPHA) * ema_score
                        score     = round(ema_score)
                        alert_manager.set_score(score)
                        alert_manager.set_posture_type(posture_type)

                        pts = [(int(l.x * w), int(l.y * h)) for l in lm]
                        for a, b in SKEL_CONNS:
                            if a < len(pts) and b < len(pts):
                                _cv2.line(frame, pts[a], pts[b], (0,201,167), 2, _cv2.LINE_AA)
                        for px, py in pts[:13]:
                            _cv2.circle(frame, (px, py), 4, (0,201,167), -1, _cv2.LINE_AA)

                color_bgr = (0,201,167) if score>=70 else (71,179,255) if score>=50 else (92,92,255)
                _cv2.rectangle(frame, (0,0), (w,76), (244,246,248), -1)
                _cv2.putText(frame, f"Score: {score}",
                             (14, 38), _cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                             color_bgr, 2, _cv2.LINE_AA)
                _put_text(frame, issues[0] if issues else "",
                          (14, 56), 16, (90, 99, 117))

                fps_count += 1
                elapsed = time.time() - fps_timer
                if elapsed >= 1.0:
                    fps = fps_count / elapsed
                    fps_count = 0
                    fps_timer = time.time()
                    self._update_score_ui(score, issues, round(fps))

                _cv2.imshow(win_name, frame)
                key = _cv2.waitKey(1) & 0xFF
                if key == ord('q') or _cv2.getWindowProperty(win_name, _cv2.WND_PROP_VISIBLE) < 1:
                    self.monitoring = False
                    break

        finally:
            self.monitoring = False
            cap.release()
            landmarker.close()
            _cv2.destroyAllWindows()
            alert_manager.set_monitoring(False)
            self._set_cam_on(False)
            self._set_calib_done(False)
            self._set_status(lang_store.t("click_to_begin"))
            self._reset_score_ui()
            self._reset_btn_state()
            try:
                self.page.update()
            except Exception:
                pass

    def _update_score_ui(self, score: int, issues: list, fps: int):
        score_store.record_posture(score)

        async def _do():
            color = ACCENT if score >= 70 else (WARNING if score >= 50 else DANGER)
            try:
                if self.score_ref.current:
                    self.score_ref.current.value = str(score)
                    self.score_ref.current.color = color
                    self.score_ref.current.update()
                if self.ring_ref.current:
                    self.ring_ref.current.value = score / 100
                    self.ring_ref.current.color = color
                    self.ring_ref.current.update()
                if self.status_ref.current:
                    self.status_ref.current.value = issues[0] if issues else ""
                    self.status_ref.current.color = color
                    self.status_ref.current.update()
                if self.fps_ref.current:
                    self.fps_ref.current.value = f"{fps} FPS"
                    self.fps_ref.current.update()
                if self.issue_col_ref.current:
                    self.issue_col_ref.current.controls = [
                        ft.Text(f"• {i}", size=13, color=DANGER, font_family="DOSSaemmul")
                        for i in issues[1:]
                    ]
                    self.issue_col_ref.current.update()
            except Exception:
                pass

        self.page.run_task(_do)

    def _reset_score_ui(self):
        async def _do():
            try:
                if self.score_ref.current:
                    self.score_ref.current.value = "--"
                    self.score_ref.current.color = ACCENT
                    self.score_ref.current.update()
                if self.ring_ref.current:
                    self.ring_ref.current.value = 0
                    self.ring_ref.current.color = ACCENT
                    self.ring_ref.current.update()
                if self.fps_ref.current:
                    self.fps_ref.current.value = ""
                    self.fps_ref.current.update()
                if self.issue_col_ref.current:
                    self.issue_col_ref.current.controls = []
                    self.issue_col_ref.current.update()
            except Exception:
                pass
        self.page.run_task(_do)

    def _reset_btn_state(self):
        """카메라 창이 닫혔을 때 버튼을 'Start Monitoring' 상태로 복원."""
        async def _do():
            try:
                btn = self.toggle_btn_ref.current
                if not btn:
                    return
                row: ft.Row = btn.content
                # _toggle uses "" (play) / "" (stop)
                row.controls[0].value = ""
                row.controls[1].value = lang_store.t("start_monitoring")
                btn.bgcolor = ACCENT
                btn.update()
            except Exception:
                pass
        self.page.run_task(_do)

    def _set_cam_on(self, on: bool):
        async def _do():
            try:
                if self.cam_dot_ref.current:
                    self.cam_dot_ref.current.bgcolor = ACCENT if on else DANGER
                    self.cam_dot_ref.current.update()
                if self.cam_label_ref.current:
                    self.cam_label_ref.current.value = lang_store.t("cam_on") if on else lang_store.t("cam_off")
                    self.cam_label_ref.current.color = ACCENT if on else DANGER
                    self.cam_label_ref.current.update()
                if self.cam_badge_ref.current:
                    self.cam_badge_ref.current.bgcolor = ACCENT_LT if on else "#FFF0F0"
                    self.cam_badge_ref.current.update()
            except Exception:
                pass
        self.page.run_task(_do)

    def _set_status(self, msg: str):
        async def _do():
            try:
                if self.status_ref.current:
                    self.status_ref.current.value = msg
                    self.status_ref.current.update()
            except Exception:
                pass
        self.page.run_task(_do)

    def _set_calib_done(self, done: bool):
        try:
            if self.calib_card_ref.current:
                self.calib_card_ref.current.bgcolor = ACCENT_LT if done else BG_CARD2
                self.calib_card_ref.current.border  = ft.border.all(
                    1, ACCENT if done else BORDER)
                col: ft.Column = self.calib_card_ref.current.content
                icon_row: ft.Row = col.controls[0]
                icon_row.controls[0].name  = ft.Icons.CHECK_CIRCLE if done else ft.Icons.RADIO_BUTTON_UNCHECKED
                icon_row.controls[0].color = ACCENT if done else TEXT_MUT
                icon_row.controls[1].value = lang_store.t("baseline_set") if done else lang_store.t("baseline_not_set")
                icon_row.controls[1].color = ACCENT if done else TEXT_MUT
                self.calib_card_ref.current.update()
        except Exception:
            pass

    def _toggle(self, e):
        # \uc774\ubbf8 \ubaa8\ub2c8\ud130\ub9c1 \uc911\uc774\uba74 \uc911\ubcf5 \uc2dc\uc791 \ubc29\uc9c0
        if not self.monitoring and self._thread and self._thread.is_alive():
            return
        self.monitoring = not self.monitoring
        btn: ft.Container = e.control
        row: ft.Row = btn.content
        if self.monitoring:
            row.controls[0].value = "\ue047"
            row.controls[1].value = lang_store.t("stop_monitoring")
            btn.bgcolor = DANGER
            btn.update()
            self._thread = threading.Thread(target=self._camera_worker, daemon=True)
            self._thread.start()
        else:
            row.controls[0].value = "\ue037"
            row.controls[1].value = lang_store.t("start_monitoring")
            btn.bgcolor = ACCENT
            btn.update()

    def _on_lang_change(self):
        """언어 변경 시 현재 monitoring 상태를 보존하며 UI 텍스트만 갱신."""
        async def _do():
            try:
                btn = self.toggle_btn_ref.current
                if btn:
                    row: ft.Row = btn.content
                    if self.monitoring:
                        row.controls[1].value = lang_store.t("stop_monitoring")
                        btn.bgcolor = DANGER
                    else:
                        row.controls[1].value = lang_store.t("start_monitoring")
                        btn.bgcolor = ACCENT
                    btn.update()
                if self.cam_label_ref.current:
                    self.cam_label_ref.current.value = (
                        lang_store.t("cam_on") if self.monitoring else lang_store.t("cam_off")
                    )
                    self.cam_label_ref.current.update()
                if self.status_ref.current and not self.monitoring:
                    self.status_ref.current.value = lang_store.t("click_to_begin")
                    self.status_ref.current.update()
            except Exception:
                pass
        self.page.run_task(_do)

    def _score_ring(self) -> ft.Container:
        return ft.Container(
            width=150, height=150,
            content=ft.Stack(
                controls=[
                    ft.ProgressRing(
                        ref=self.ring_ref,
                        value=0, width=150, height=150,
                        stroke_width=12, color=ACCENT, bgcolor=BORDER,
                    ),
                    ft.Container(
                        width=150, height=150,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Column(
                            controls=[
                                ft.Text(ref=self.score_ref, value="--",
                                        size=36, weight=ft.FontWeight.W_500,
                                        color=ACCENT, font_family="DOSSaemmul",
                                        text_align=ft.TextAlign.CENTER),
                                ft.Text(lang_store.t("posture_score_label"), size=13, color=TEXT_MUT,
                                        font_family="DOSSaemmul",
                                        text_align=ft.TextAlign.CENTER),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=2,
                        ),
                    ),
                ],
            ),
        )

    def build(self) -> ft.Container:
        model_path = _find_model()

        calib_card = ft.Container(
            ref=self.calib_card_ref,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED,
                                    size=16, color=TEXT_MUT),
                            ft.Text(lang_store.t("baseline_not_set"), size=14,
                                    color=TEXT_MUT, font_family="DOSSaemmul"),
                        ],
                        spacing=8,
                    ),
                    ft.Text(
                        lang_store.t("calib_guide"),
                        size=13, color=TEXT_PRI, font_family="DOSSaemmul",
                    ),
                ],
                spacing=6,
            ),
            bgcolor=ACCENT_LT,
            border_radius=10,
            border=ft.border.all(1, ACCENT + "88"),
            padding=ft.padding.only(left=14, top=10, right=14, bottom=10),
        )

        preview_box = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.ACCESSIBILITY, size=52, color=BORDER),
                    ft.Text(lang_store.t("press_start"),
                            size=16, color=TEXT_MUT, font_family="DOSSaemmul",
                            text_align=ft.TextAlign.CENTER),
                    ft.Container(height=8),
                    ft.Row(
                        controls=[
                            ft.Container(
                                ref=self.cam_badge_ref,
                                content=ft.Row(
                                    controls=[
                                        ft.Container(ref=self.cam_dot_ref,
                                                     width=6, height=6, bgcolor=DANGER,
                                                     border_radius=3),
                                        ft.Text(ref=self.cam_label_ref,
                                                value=lang_store.t("cam_off"), size=12,
                                                color=DANGER, font_family="DOSSaemmul"),
                                    ],
                                    spacing=5,
                                ),
                                bgcolor="#FFF0F0", border_radius=6,
                                padding=ft.padding.only(left=10, top=5, right=10, bottom=5),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Text(ref=self.fps_ref, value="",
                            size=13, color=TEXT_MUT, font_family="DOSSaemmul"),
                    ft.Container(height=4),
                    ft.Container(
                        ref=self.toggle_btn_ref,
                        content=ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.Icons.STOP if self.monitoring else ft.Icons.PLAY_ARROW,
                                    size=18, color="#F0F9F8",
                                ),
                                ft.Text(
                                    lang_store.t("stop_monitoring") if self.monitoring
                                    else lang_store.t("start_monitoring"),
                                    size=16, weight=ft.FontWeight.W_400,
                                    color="#F0F9F8", font_family="DOSSaemmul",
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=8,
                        ),
                        bgcolor=DANGER if self.monitoring else ACCENT,
                        border_radius=12,
                        width=220,
                        padding=ft.padding.only(left=20, top=12, right=20, bottom=12),
                        on_click=self._toggle,
                        shadow=ft.BoxShadow(blur_radius=12, color=ACCENT + "55",
                                            offset=ft.Offset(0, 4)),
                    ),
                    ft.Container(height=10),
                    calib_card,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            expand=True,
            bgcolor=BG_CARD, border_radius=16,
            border=ft.border.all(1, BORDER),
            alignment=ft.Alignment(0, 0),
            padding=20,
        )

        model_warning = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.WARNING, size=16, color=WARNING),
                    ft.Text(
                        "pose_landmarker.task not found!\n"
                        "Terminal: curl -o pose_landmarker.task "
                        "\"https://storage.googleapis.com/mediapipe-models/"
                        "pose_landmarker/pose_landmarker_lite/float16/latest/"
                        "pose_landmarker_lite.task\"",
                        size=13, color=WARNING, font_family="DOSSaemmul",
                    ),
                ],
                spacing=8,
            ),
            bgcolor=WARNING + "15", border_radius=8, padding=12,
            border=ft.border.all(1, WARNING + "50"),
            visible=model_path is None,
        )

        issue_col = ft.Column(ref=self.issue_col_ref, controls=[], spacing=4)

        right_panel = ft.Column(
            controls=[
                card(
                    ft.Column(
                        controls=[
                            ft.Text(lang_store.t("live_score"), size=16, weight=ft.FontWeight.W_400,
                                    color=TEXT_PRI, font_family="DOSSaemmul"),
                            ft.Container(expand=True),
                            ft.Container(content=self._score_ring(),
                                         alignment=ft.Alignment(0, 0)),
                            ft.Container(height=10),
                            ft.Text(ref=self.status_ref,
                                    value=lang_store.t("click_to_begin"),
                                    size=14, color=TEXT_MUT,
                                    font_family="DOSSaemmul",
                                    text_align=ft.TextAlign.CENTER),
                            ft.Container(height=4),
                            issue_col,
                            ft.Container(expand=True),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        expand=True,
                    ),
                    expand=True,
                ),
            ],
            width=240, spacing=0,
        )

        main_area = ft.Column(
            controls=[
                model_warning,
                ft.Container(height=4, visible=model_path is None),
                preview_box,
            ],
            expand=True, spacing=0,
        )

        BODY_H = 580

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(lang_store.t("posture_title"), size=26, weight=ft.FontWeight.W_400,
                                    color=TEXT_PRI, font_family="DOSSaemmul"),
                            ft.Text(lang_store.t("posture_sub"),
                                    size=15, color=TEXT_SEC, font_family="DOSSaemmul"),
                        ],
                        spacing=2,
                    ),
                    ft.Container(height=12),
                    ft.Row(
                        controls=[main_area, ft.Container(width=20), right_panel],
                        height=BODY_H,
                        vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                    ),
                ],
                spacing=0,
                expand=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
            padding=ft.padding.only(left=28, top=18, right=28, bottom=18),
            bgcolor=BG_BASE,
        )
