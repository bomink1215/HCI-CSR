import flet as ft
from components.ui import card
import threading
import os
import tempfile
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


def _calc_score(landmarks) -> tuple:
    try:
        nose       = landmarks[0]
        l_ear      = landmarks[7];  r_ear      = landmarks[8]
        l_shoulder = landmarks[11]; r_shoulder = landmarks[12]
        l_hip      = landmarks[23]; r_hip      = landmarks[24]

        score, issues = 100, []

        sh_mid_x = (l_shoulder.x + r_shoulder.x) / 2
        fwd = abs(nose.x - sh_mid_x)
        if fwd > 0.08:
            score -= min(30, int(fwd * 200))
            issues.append("거북목 주의! 머리를 뒤로 당겨주세요")

        tilt = abs(l_shoulder.y - r_shoulder.y)
        if tilt > 0.04:
            score -= min(20, int(tilt * 300))
            issues.append("어깨가 한쪽으로 기울었어요")

        hip_mid_x = (l_hip.x + r_hip.x) / 2
        lean = abs(sh_mid_x - hip_mid_x)
        if lean > 0.06:
            score -= min(25, int(lean * 250))
            issues.append("등이 굽었어요 — 등을 펴주세요")

        sh_mid_y  = (l_shoulder.y + r_shoulder.y) / 2
        ear_mid_y = (l_ear.y + r_ear.y) / 2
        if ear_mid_y - sh_mid_y > -0.10:
            score -= 15
            issues.append("고개를 들어주세요")

        score = max(0, min(100, score))
        if not issues:
            issues.append("자세 좋아요! 계속 유지하세요 👍")
        return score, issues
    except Exception as e:
        return 0, [f"분석 오류: {e}"]


class PostureView:
    def __init__(self, page: ft.Page):
        self.page       = page
        self.monitoring = False
        self._thread    = None

        self.score_ref     = ft.Ref()
        self.status_ref    = ft.Ref()
        self.ring_ref      = ft.Ref()
        self.cam_dot_ref   = ft.Ref()
        self.cam_label_ref = ft.Ref()
        self.issue_col_ref = ft.Ref()
        self.fps_ref       = ft.Ref()

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
        self._set_status("분석 중... (별도 창 확인)")
        alert_manager.set_monitoring(True)

        import time
        frame_ts  = 0
        fps_timer = time.time()
        fps_count = 0
        score     = 0

        win_name = "FocusMate — 자세 분석 (Q: 종료)"
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(win_name, 800, 600)

        SKEL_CONNS = [
            (11,12),(11,13),(13,15),(12,14),(14,16),
            (11,23),(12,24),(23,24),
            (23,25),(24,26),(25,27),(26,28),
        ]

        try:
            while self.monitoring:
                ret, frame = cap.read()
                if not ret:
                    break

                frame = cv2.flip(frame, 1)
                h, w  = frame.shape[:2]
                rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

                frame_ts += 33
                try:
                    result = landmarker.detect_for_video(mp_img, frame_ts)
                except Exception:
                    result = None

                issues = ["사람을 감지하지 못했어요"]
                if result and result.pose_landmarks:
                    lm = result.pose_landmarks[0]
                    score, issues = _calc_score(lm)
                    alert_manager.set_score(score)

                    pts = [(int(l.x * w), int(l.y * h)) for l in lm]
                    for a, b in SKEL_CONNS:
                        if a < len(pts) and b < len(pts):
                            cv2.line(frame, pts[a], pts[b], (0, 201, 167), 2, cv2.LINE_AA)
                    for x, y in pts:
                        cv2.circle(frame, (x, y), 4, (0, 201, 167), -1, cv2.LINE_AA)

                color_bgr = (0,201,167) if score>=70 else (71,179,255) if score>=50 else (92,92,255)
                overlay = frame.copy()
                cv2.rectangle(overlay, (0, 0), (w, 70), (244, 246, 248), -1)
                cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)
                cv2.putText(frame, f"Score: {score}",
                            (14, 38), cv2.FONT_HERSHEY_SIMPLEX, 1.1, color_bgr, 2, cv2.LINE_AA)
                cv2.putText(frame, issues[0] if issues else "",
                            (14, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (90,99,117), 1, cv2.LINE_AA)

                fps_count += 1
                elapsed = time.time() - fps_timer
                if elapsed >= 1.0:
                    fps = fps_count / elapsed
                    fps_count = 0
                    fps_timer = time.time()
                    self._update_score_ui(score, issues, round(fps))

                cv2.imshow(win_name, frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or cv2.getWindowProperty(win_name, cv2.WND_PROP_VISIBLE) < 1:
                    self.monitoring = False
                    break
        finally:
            cap.release()
            landmarker.close()
            cv2.destroyAllWindows()
            alert_manager.set_monitoring(False)
            self._set_cam_on(False)
            self._set_status("모니터링을 시작해주세요")
            self._reset_score_ui()
            try:
                self.page.update()
            except Exception:
                pass

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
                    ft.Text(f"• {i}", size=11, color=DANGER, font_family="Galmuri")
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
                                        color=ACCENT, font_family="GalmuriBold",
                                        text_align=ft.TextAlign.CENTER),
                                ft.Text("자세 점수", size=11, color=TEXT_MUT,
                                        font_family="Galmuri",
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
        tips = [
            ("모니터 높이", "눈높이와 모니터 상단이 일치하도록"),
            ("목 각도",    "앞으로 15° 이상 기울지 않도록"),
            ("허리",       "등받이에 완전히 밀착시키기"),
            ("발 위치",    "바닥에 평평하게 놓기"),
        ]

        model_path = _find_model()

        preview_box = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("\ue3a5", font_family="Material Icons", size=52, color=BORDER),
                    ft.Text("모니터링 시작 버튼을 누르면\nOpenCV 창이 열립니다",
                            size=14, color=TEXT_MUT, font_family="Galmuri",
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
                                        color=DANGER, font_family="Galmuri"),
                                ft.Container(expand=True),
                                ft.Text(ref=self.fps_ref, value="",
                                        size=11, color=TEXT_MUT,
                                        font_family="Galmuri"),
                            ],
                            spacing=6,
                        ),
                        bgcolor=BG_CARD2,
                        border_radius=8,
                        padding=ft.padding.only(left=12, top=8, right=12, bottom=8),
                        border=ft.border.all(1, BORDER),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=8,
            ),
            height=240,
            bgcolor=BG_CARD,
            border_radius=16,
            border=ft.border.all(1, BORDER),
            alignment=ft.Alignment(0, 0),
            padding=20,
        )

        model_warning = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text("\ue002", font_family="Material Icons", size=16, color=WARNING),
                    ft.Text(
                        "pose_landmarker.task 파일 없음!\n"
                        "터미널: curl -o pose_landmarker.task \"https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task\"",
                        size=11, color=WARNING, font_family="Galmuri",
                    ),
                ],
                spacing=8,
            ),
            bgcolor=WARNING + "15",
            border_radius=8,
            padding=12,
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
                                    color=TEXT_PRI, font_family="Galmuri"),
                            ft.Container(height=14),
                            ft.Container(content=self._score_ring(),
                                         alignment=ft.Alignment(0, 0)),
                            ft.Container(height=10),
                            ft.Text(ref=self.status_ref,
                                    value="모니터링을 시작해주세요",
                                    size=12, color=TEXT_MUT,
                                    font_family="Galmuri",
                                    text_align=ft.TextAlign.CENTER),
                            ft.Container(height=4),
                            issue_col,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ),
                ft.Container(height=12),
                card(
                    ft.Column(
                        controls=[
                            ft.Text("자세 체크리스트", size=13, weight=ft.FontWeight.W_400,
                                    color=TEXT_PRI, font_family="Galmuri"),
                            ft.Container(height=6),
                            *[
                                ft.Row(controls=[
                                    ft.Container(
                                        content=ft.Text("\ue5ca",
                                                        font_family="Material Icons",
                                                        size=16, color=ACCENT),
                                        width=24,
                                    ),
                                    ft.Column(controls=[
                                        ft.Text(t, size=12, color=TEXT_PRI,
                                                font_family="Galmuri"),
                                        ft.Text(d, size=10, color=TEXT_MUT,
                                                font_family="Galmuri"),
                                    ], spacing=1),
                                ], spacing=8)
                                for t, d in tips
                            ],
                        ],
                        spacing=10,
                    ),
                ),
                ft.Container(height=12),
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Text("\ue037", font_family="Material Icons",
                                    size=18, color="#FFFFFF"),
                            ft.Text("모니터링 시작", size=14, weight=ft.FontWeight.W_400,
                                    color="#FFFFFF", font_family="Galmuri"),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=8,
                    ),
                    bgcolor=ACCENT,
                    border_radius=12,
                    padding=ft.padding.only(top=14, bottom=14),
                    on_click=self._toggle,
                    shadow=ft.BoxShadow(blur_radius=12, color=ACCENT + "55",
                                        offset=ft.Offset(0, 4)),
                ),
            ],
            width=240, spacing=0,
        )

        tip_cards = ft.Column(
            controls=[
                card(ft.Row(controls=[
                    ft.Container(
                        content=ft.Text("\ue3a5", font_family="Material Icons",
                                       size=20, color=ACCENT),
                        width=38, height=38, bgcolor=ACCENT_LT,
                        border_radius=10, alignment=ft.Alignment(0, 0),
                    ),
                    ft.Column(controls=[
                        ft.Text(t, size=13, weight=ft.FontWeight.W_400,
                                color=TEXT_PRI, font_family="Galmuri"),
                        ft.Text(d, size=11, color=TEXT_SEC,
                                font_family="Galmuri"),
                    ], spacing=2, expand=True),
                ], spacing=12))
                for t, d in tips
            ],
            spacing=8,
        )

        main_area = ft.Column(
            controls=[
                ft.Column(controls=[
                    ft.Text("자세 교정", size=26, weight=ft.FontWeight.W_400,
                            color=TEXT_PRI, font_family="Galmuri"),
                    ft.Text("OpenCV 창에서 실시간 자세 분석 · 점수는 앱에 표시",
                            size=13, color=TEXT_SEC, font_family="Galmuri"),
                ], spacing=2),
                ft.Container(height=12),
                model_warning,
                ft.Container(height=4),
                preview_box,
                ft.Container(height=16),
                ft.Text("교정 팁", size=14, weight=ft.FontWeight.W_400,
                        color=TEXT_PRI, font_family="Galmuri"),
                ft.Container(height=8),
                tip_cards,
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
