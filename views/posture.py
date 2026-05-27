import flet as ft
from components.ui import card
import threading
import time
import os
import tempfile
import statistics
from utils import alert_manager

BG_BASE   = "#FFFFFF"
BG_CARD   = "#F4F6F8"
BG_CARD2  = "#EAECEF"
ACCENT    = "#00C9A7"
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

POSTURE_ROUNDED = "rounded_back"    # 등 굽음 (거북목 통합)
POSTURE_SLOUCH  = "slouch"          # 허리 자세 (골반 빠짐)
POSTURE_TILT    = "shoulder_tilt"   # 어깨 불균형
POSTURE_OK      = "good"

# ── 캘리브레이션 상태 (모듈 레벨 공유) ──────────────────────────
_calib = {
    "done":     False,
    "ear_y":    None,   # 기준 귀 Y 중간값 (허리 자세 기준)
    "face_w":   None,   # 기준 귀간격 (등 굽음 — 얼굴 카메라 거리)
    "tilt_raw": None,   # 기준 어깨 기울기 / face_w (None이면 어깨 안 보임)
}


def reset_calibration():
    _calib.update(done=False, ear_y=None, face_w=None, tilt_raw=None)


def _vis(lm) -> float:
    return getattr(lm, "visibility", 1.0) or 0.0


def _extract_features(landmarks):
    """
    랜드마크에서 자세 특징값을 추출.
    Returns dict or None (감지 실패 시).

    ── 지표 설계 ─────────────────────────────────────────────────
    face_w   : 귀 사이 X 거리 (카메라 거리 반영 — 가까울수록 큼)
    ear_y    : 귀 Y 중간값   (몸이 아래로 내려가면 커짐)
    tilt_raw : 좌우 어깨 Y 차이 / face_w

    ── 자세별 신호 패턴 ──────────────────────────────────────────
    [등 굽음]  몸이 앞으로 기울어짐 → face_w 증가 (얼굴이 가까워짐)
    [허리 자세] 몸이 아래+뒤로 내려감 → ear_y 증가 + face_w 감소
               (골반이 의자 끝으로 빠지면서 몸이 내려가고 뒤로 기댐)
    [어깨]    좌우 어깨 Y 차이 증가
    """
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
        feat["tilt_side"] = "왼쪽" if l_sh.y > r_sh.y else "오른쪽"

    return feat


def _calc_score(feat: dict) -> tuple:
    """
    캘리브레이션 기준값 대비 편차로 점수·자세 유형 계산.

    Returns (score: int, issues: list[str], posture_type: str, ded: dict, dbg: dict)
    """
    if not _calib["done"]:
        return 100, ["캘리브레이션 대기 중..."], POSTURE_OK, {}, {}

    score  = 100
    issues = []
    ded    = {POSTURE_ROUNDED: 0, POSTURE_SLOUCH: 0, POSTURE_TILT: 0}

    base_ear_y  = _calib["ear_y"]
    base_face_w = _calib["face_w"]
    base_tilt   = _calib["tilt_raw"]

    zoom      = (feat["face_w"] - base_face_w) / base_face_w   # 양수=가까워짐
    ear_drop  = feat["ear_y"] - base_ear_y                     # 양수=아래로 내려감

    dbg = {
        "zoom":     round(zoom,     3),
        "ear_drop": round(ear_drop, 3),
        "face_w":   round(feat["face_w"], 3),
        "base_fw":  round(base_face_w,    3),
    }

    # ── 1. 허리 자세 (골반 빠짐) — 우선 판단 ────────────────────
    # 몸이 아래로 내려가면 귀 Y가 기준보다 증가.
    # ear_drop 단독으로 판단 (zoom 조건 제거 — 몸이 내려가도 얼굴이
    # 카메라에 가까워질 수 있어서 zoom이 항상 음수가 아님).
    SLOUCH_EAR_MARGIN = 0.06   # 귀가 기준보다 6% 아래로 내려가면 감점
    if ear_drop > SLOUCH_EAR_MARGIN:
        excess = ear_drop - SLOUCH_EAR_MARGIN
        d = min(int(excess * 350), 45)
        score -= d
        ded[POSTURE_SLOUCH] += d
        issues.append("허리 자세가 무너졌어요 — 엉덩이를 의자 깊숙이 밀어넣어 주세요")

    # ── 2. 등 굽음 (앞으로 기울기) ───────────────────────────────
    # 얼굴이 가까워짐(zoom 증가). 단 허리 자세가 이미 감지된 경우 스킵
    # (몸이 내려갈 때 face_w도 약간 커질 수 있어서 중복 방지)
    ROUNDED_MARGIN = 0.10
    if zoom > ROUNDED_MARGIN and ded[POSTURE_SLOUCH] == 0:
        excess = zoom - ROUNDED_MARGIN
        d = min(int(excess * 280), 40)
        score -= d
        ded[POSTURE_ROUNDED] += d
        issues.append("등이 굽었어요 — 등을 펴고 어깨를 뒤로 당겨주세요")

    # ── 3. 어깨 불균형 ────────────────────────────────────────────
    TILT_MARGIN = 0.12
    if base_tilt is not None and feat.get("tilt_raw") is not None:
        delta_tilt = feat["tilt_raw"] - base_tilt
        if delta_tilt > TILT_MARGIN:
            excess = delta_tilt - TILT_MARGIN
            d = min(int(excess * 180), 35)
            score -= d
            ded[POSTURE_TILT] += d
            side = feat.get("tilt_side", "한쪽")
            issues.append(f"어깨가 기울었어요 — {side} 어깨를 올려주세요")

    score = max(0, min(100, score))
    posture_type = POSTURE_OK
    if any(v > 0 for v in ded.values()):
        posture_type = max(ded, key=ded.get)
    if not issues:
        issues.append("자세 좋아요! 계속 유지하세요 👍")

    dbg["ded"] = dict(ded)
    return score, issues, posture_type, ded, dbg


class PostureView:
    def __init__(self, page: ft.Page):
        self.page        = page
        self.monitoring  = False
        self._thread     = None
        self._calib_done = False

        # Flet UI refs
        self.score_ref      = ft.Ref()
        self.status_ref     = ft.Ref()
        self.ring_ref       = ft.Ref()
        self.cam_dot_ref    = ft.Ref()
        self.cam_label_ref  = ft.Ref()
        self.issue_col_ref  = ft.Ref()
        self.fps_ref        = ft.Ref()
        self.toggle_btn_ref = ft.Ref()
        self.calib_card_ref = ft.Ref()   # 캘리브레이션 안내 카드

    # ── 캘리브레이션 ──────────────────────────────────────────────
    def _run_calibration(self, landmarker, cap, mp, win_name, start_time):
        """
        카메라를 열어 3초 카운트다운 → 3초 수집 → 중앙값으로 baseline 확정.
        OpenCV 창에 안내 오버레이 표시.
        """
        import cv2
        COUNTDOWN = 3   # 준비 카운트다운 (초)
        COLLECT   = 3   # 수집 시간 (초)

        phase     = "countdown"   # countdown → collect → done
        phase_start = time.time()

        samples_ear_y  = []
        samples_face_w = []
        samples_tilt   = []

        self._set_status("바른 자세로 앉아주세요...")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            h, w  = frame.shape[:2]

            now     = time.time()
            elapsed = now - phase_start

            # ── MediaPipe 처리 ───────────────────────────────────
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

            # ── 오버레이 ─────────────────────────────────────────
            overlay = frame.copy()
            cv2.rectangle(overlay, (0,0), (w, h), (244,246,248), -1)
            cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

            if phase == "countdown":
                remaining = int(COUNTDOWN - elapsed) + 1
                cv2.putText(frame, "SIT UP STRAIGHT",
                            (w//2 - 160, h//2 - 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0,201,167), 2, cv2.LINE_AA)
                cv2.putText(frame, "Calibrating in...",
                            (w//2 - 110, h//2),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (90,99,117), 1, cv2.LINE_AA)
                cv2.putText(frame, str(remaining),
                            (w//2 - 22, h//2 + 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 3.0, (0,201,167), 4, cv2.LINE_AA)

                if elapsed >= COUNTDOWN:
                    phase       = "collect"
                    phase_start = time.time()

            elif phase == "collect":
                remaining = COLLECT - elapsed
                bar_w = int((elapsed / COLLECT) * (w - 60))
                cv2.putText(frame, "Hold still — recording baseline",
                            (w//2 - 200, h//2 - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,201,167), 2, cv2.LINE_AA)
                cv2.rectangle(frame, (30, h//2 + 20), (w-30, h//2 + 44), (220,224,230), -1)
                cv2.rectangle(frame, (30, h//2 + 20), (30 + bar_w, h//2 + 44), (0,201,167), -1)

                no_face_msg = "" if feat else "Face not detected!"
                if no_face_msg:
                    cv2.putText(frame, no_face_msg,
                                (w//2 - 100, h//2 + 80),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (92,92,255), 2, cv2.LINE_AA)

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
                return False   # 사용자가 취소

        # ── baseline 확정 ────────────────────────────────────────
        if len(samples_face_w) < 5:
            self._set_status("❌ 캘리브레이션 실패 — 얼굴이 감지되지 않았어요")
            return False

        _calib["ear_y"]    = statistics.median(samples_ear_y)
        _calib["face_w"]   = statistics.median(samples_face_w)
        _calib["tilt_raw"] = statistics.median(samples_tilt) if len(samples_tilt) >= 5 else None
        _calib["done"]        = True

        self._set_calib_done(True)
        self._set_status("분석 중... (별도 창 확인)")
        return True

    # ── 카메라 워커 (메인 루프) ───────────────────────────────────
    def _camera_worker(self):
        try:
            import cv2
            import mediapipe as mp
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python.vision import (
                PoseLandmarker, PoseLandmarkerOptions, RunningMode
            )
        except ImportError as e:
            self._set_status(f"❌ 라이브러리 오류: {e}")
            self.monitoring = False
            return

        model_path = _find_model()
        if not model_path:
            self._set_status("❌ pose_landmarker.task 파일 없음")
            self.monitoring = False
            return

        self._set_status("🔄 모델 로딩 중...")
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
            self._set_status(f"❌ 모델 로드 실패: {e}")
            self.monitoring = False
            return

        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        if not cap.isOpened():
            self._set_status("❌ 카메라를 열 수 없어요")
            self.monitoring = False
            landmarker.close()
            return

        self._set_cam_on(True)
        alert_manager.set_monitoring(True)

        import cv2 as _cv2
        win_name   = "FocusMate — 자세 분석 (Q: 종료)"
        start_time = time.time()
        _cv2.namedWindow(win_name, _cv2.WINDOW_NORMAL)
        _cv2.resizeWindow(win_name, 800, 600)

        # ── 캘리브레이션 ─────────────────────────────────────────
        reset_calibration()
        ok = self._run_calibration(landmarker, cap, mp, win_name, start_time)
        if not ok or not self.monitoring:
            cap.release()
            landmarker.close()
            _cv2.destroyAllWindows()
            alert_manager.set_monitoring(False)
            self._set_cam_on(False)
            self._set_status("모니터링을 시작해주세요")
            self._reset_score_ui()
            return

        SKEL_CONNS = [
            (11,12),(11,13),(13,15),(12,14),(14,16),
        ]

        fps_timer = time.time()
        fps_count = 0
        score     = 100
        issues    = ["자세 좋아요! 계속 유지하세요 👍"]

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
                zoom         = 0.0
                if result and result.pose_landmarks:
                    lm   = result.pose_landmarks[0]
                    feat = _extract_features(lm)
                    if feat:
                        score, issues, posture_type, ded, dbg = _calc_score(feat)
                        alert_manager.set_score(score)
                        alert_manager.set_posture_type(posture_type)

                        pts = [(int(l.x * w), int(l.y * h)) for l in lm]
                        for a, b in SKEL_CONNS:
                            if a < len(pts) and b < len(pts):
                                _cv2.line(frame, pts[a], pts[b], (0,201,167), 2, _cv2.LINE_AA)
                        for px, py in pts[:13]:
                            _cv2.circle(frame, (px, py), 4, (0,201,167), -1, _cv2.LINE_AA)

                # ── 상단 HUD ──────────────────────────────────────
                color_bgr = (0,201,167) if score>=70 else (71,179,255) if score>=50 else (92,92,255)
                _cv2.rectangle(frame, (0,0), (w,60), (244,246,248), -1)
                _cv2.putText(frame, f"Score: {score}",
                             (14, 36), _cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                             color_bgr, 2, _cv2.LINE_AA)
                _cv2.putText(frame, issues[0] if issues else "",
                             (14, 56), _cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                             (90,99,117), 1, _cv2.LINE_AA)

                # ── 하단 디버그 패널 ──────────────────────────────
                dbg_lines = [
                    f"[rounded] zoom     : {dbg.get('zoom',0):+.3f}  (margin +0.10)",
                    f"[slouch]  ear_drop : {dbg.get('ear_drop',0):+.3f}  (margin +0.04, need zoom<-0.08)",
                    f"[tilt]    base_tilt: {(_calib.get('tilt_raw') or 0):.3f}",
                    f"face_w now:{dbg.get('face_w',0):.3f}  base:{dbg.get('base_fw',0):.3f}",
                    f"ded  rounded:{ded.get(POSTURE_ROUNDED,0)}  slouch:{ded.get(POSTURE_SLOUCH,0)}  tilt:{ded.get(POSTURE_TILT,0)}",
                ]
                panel_h = len(dbg_lines) * 18 + 10
                panel_y = h - panel_h - 4
                _cv2.rectangle(frame, (0, panel_y), (w, h), (230,234,240), -1)
                for li, line in enumerate(dbg_lines):
                    _cv2.putText(frame, line,
                                 (8, panel_y + 14 + li * 18),
                                 _cv2.FONT_HERSHEY_SIMPLEX, 0.40,
                                 (60,70,90), 1, _cv2.LINE_AA)

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
            cap.release()
            landmarker.close()
            _cv2.destroyAllWindows()
            alert_manager.set_monitoring(False)
            self._set_cam_on(False)
            self._set_calib_done(False)
            self._set_status("모니터링을 시작해주세요")
            self._reset_score_ui()
            try:
                self.page.update()
            except Exception:
                pass

    # ── UI 헬퍼 ──────────────────────────────────────────────────
    def _update_score_ui(self, score: int, issues: list, fps: int):
        color = ACCENT if score >= 70 else (WARNING if score >= 50 else DANGER)
        try:
            if self.score_ref.current:
                self.score_ref.current.value = str(score)
                self.score_ref.current.color = color
            if self.ring_ref.current:
                self.ring_ref.current.value = score / 100
                self.ring_ref.current.color = color
            if self.status_ref.current:
                self.status_ref.current.value = issues[0] if issues else ""
                self.status_ref.current.color = color
            if self.fps_ref.current:
                self.fps_ref.current.value = f"{fps} FPS"
            if self.issue_col_ref.current:
                self.issue_col_ref.current.controls = [
                    ft.Text(f"• {i}", size=11, color=DANGER, font_family="DOSSaemmul")
                    for i in issues[1:]
                ]
            self.page.update()
        except Exception:
            pass

    def _reset_score_ui(self):
        try:
            if self.score_ref.current:
                self.score_ref.current.value = "--"
                self.score_ref.current.color = ACCENT
            if self.ring_ref.current:
                self.ring_ref.current.value = 0
                self.ring_ref.current.color = ACCENT
            if self.fps_ref.current:
                self.fps_ref.current.value = ""
            if self.issue_col_ref.current:
                self.issue_col_ref.current.controls = []
            self.page.update()
        except Exception:
            pass

    def _set_cam_on(self, on: bool):
        try:
            if self.cam_dot_ref.current:
                self.cam_dot_ref.current.bgcolor = ACCENT if on else DANGER
            if self.cam_label_ref.current:
                self.cam_label_ref.current.value = "카메라 켜짐" if on else "카메라 꺼짐"
                self.cam_label_ref.current.color = ACCENT if on else DANGER
            self.page.update()
        except Exception:
            pass

    def _set_status(self, msg: str):
        try:
            if self.status_ref.current:
                self.status_ref.current.value = msg
                self.page.update()
        except Exception:
            pass

    def _set_calib_done(self, done: bool):
        """캘리브레이션 완료 여부를 UI 카드에 반영"""
        try:
            if self.calib_card_ref.current:
                self.calib_card_ref.current.bgcolor = ACCENT_LT if done else BG_CARD2
                self.calib_card_ref.current.border  = ft.border.all(
                    1, ACCENT if done else BORDER)
                col: ft.Column = self.calib_card_ref.current.content
                icon_row: ft.Row = col.controls[0]
                icon_row.controls[0].name  = ft.Icons.CHECK_CIRCLE if done else ft.Icons.RADIO_BUTTON_UNCHECKED
                icon_row.controls[0].color = ACCENT if done else TEXT_MUT
                icon_row.controls[1].value = "기준 자세 완료 ✓" if done else "기준 자세 미설정"
                icon_row.controls[1].color = ACCENT if done else TEXT_MUT
                self.calib_card_ref.current.update()
        except Exception:
            pass

    def _toggle(self, e):
        self.monitoring = not self.monitoring
        btn: ft.Container = e.control
        row: ft.Row = btn.content
        if self.monitoring:
            row.controls[0].value = "\ue047"
            row.controls[1].value = "모니터링 중지"
            btn.bgcolor = DANGER
            btn.update()
            self._thread = threading.Thread(target=self._camera_worker, daemon=True)
            self._thread.start()
        else:
            row.controls[0].value = "\ue037"
            row.controls[1].value = "모니터링 시작"
            btn.bgcolor = ACCENT
            btn.update()

    # ── 점수 링 ──────────────────────────────────────────────────
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
                                ft.Text("자세 점수", size=11, color=TEXT_MUT,
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

    # ── build ─────────────────────────────────────────────────────
    def build(self) -> ft.Container:
        model_path = _find_model()

        # 캘리브레이션 상태 카드
        calib_card = ft.Container(
            ref=self.calib_card_ref,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED,
                                    size=16, color=TEXT_MUT),
                            ft.Text("기준 자세 미설정", size=12,
                                    color=TEXT_MUT, font_family="DOSSaemmul"),
                        ],
                        spacing=8,
                    ),
                    ft.Text(
                        "모니터링 시작 시 3초 카운트다운 후\n"
                        "바른 자세를 3초간 유지하면 기준이 설정됩니다",
                        size=11, color=TEXT_SEC, font_family="DOSSaemmul",
                    ),
                ],
                spacing=6,
            ),
            bgcolor=BG_CARD2,
            border_radius=10,
            border=ft.border.all(1, BORDER),
            padding=ft.padding.only(left=14, top=10, right=14, bottom=10),
        )

        preview_box = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.ACCESSIBILITY, size=52, color=BORDER),
                    ft.Text("모니터링 시작 버튼을 누르면\nOpenCV 창이 열립니다",
                            size=14, color=TEXT_MUT, font_family="DOSSaemmul",
                            text_align=ft.TextAlign.CENTER),
                    ft.Container(height=8),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Container(ref=self.cam_dot_ref,
                                             width=8, height=8, bgcolor=DANGER,
                                             border_radius=4),
                                ft.Text(ref=self.cam_label_ref,
                                        value="카메라 꺼짐", size=12,
                                        color=DANGER, font_family="DOSSaemmul"),
                                ft.Container(expand=True),
                                ft.Text(ref=self.fps_ref, value="",
                                        size=11, color=TEXT_MUT,
                                        font_family="DOSSaemmul"),
                            ],
                            spacing=6,
                        ),
                        bgcolor=BG_CARD2, border_radius=8,
                        padding=ft.padding.only(left=12, top=8, right=12, bottom=8),
                        border=ft.border.all(1, BORDER),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            height=220,
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
                        "pose_landmarker.task 파일 없음!\n"
                        "터미널: curl -o pose_landmarker.task "
                        "\"https://storage.googleapis.com/mediapipe-models/"
                        "pose_landmarker/pose_landmarker_lite/float16/latest/"
                        "pose_landmarker_lite.task\"",
                        size=11, color=WARNING, font_family="DOSSaemmul",
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
                            ft.Text("실시간 점수", size=14, weight=ft.FontWeight.W_400,
                                    color=TEXT_PRI, font_family="DOSSaemmul"),
                            ft.Container(height=14),
                            ft.Container(content=self._score_ring(),
                                         alignment=ft.Alignment(0, 0)),
                            ft.Container(height=10),
                            ft.Text(ref=self.status_ref,
                                    value="모니터링을 시작해주세요",
                                    size=12, color=TEXT_MUT,
                                    font_family="DOSSaemmul",
                                    text_align=ft.TextAlign.CENTER),
                            ft.Container(height=4),
                            issue_col,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                ft.Container(height=10),
                calib_card,
                ft.Container(height=10),
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.PLAY_ARROW, size=18, color="#FFFFFF"),
                            ft.Text("모니터링 시작", size=14, weight=ft.FontWeight.W_400,
                                    color="#FFFFFF", font_family="DOSSaemmul"),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    bgcolor=ACCENT, border_radius=12,
                    padding=ft.padding.only(top=14, bottom=14),
                    on_click=self._toggle,
                    shadow=ft.BoxShadow(blur_radius=12, color=ACCENT + "55",
                                        offset=ft.Offset(0, 4)),
                ),
            ],
            width=240, spacing=0,
        )

        main_area = ft.Column(
            controls=[
                ft.Column(controls=[
                    ft.Text("자세 교정", size=26, weight=ft.FontWeight.W_400,
                            color=TEXT_PRI, font_family="DOSSaemmul"),
                    ft.Text("시작 시 바른 자세를 3초 유지 → 이후 실시간 비교",
                            size=13, color=TEXT_SEC, font_family="DOSSaemmul"),
                ], spacing=2),
                ft.Container(height=12),
                model_warning,
                ft.Container(height=4),
                preview_box,
            ],
            expand=True, spacing=0,
            scroll=ft.ScrollMode.AUTO,
        )

        return ft.Container(
            content=ft.Row(
                controls=[main_area, ft.Container(width=20), right_panel],
                vertical_alignment=ft.CrossAxisAlignment.START,
                expand=True,
            ),
            expand=True,
            padding=ft.padding.only(left=28, top=24, right=28, bottom=24),
            bgcolor=BG_BASE,
        )
