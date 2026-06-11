import flet as ft
import os
from utils import lang as lang_store

_ASSETS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")

FONT     = "DOSSaemmul"
ACCENT   = "#7AC3B8"
ACCENT_LT = "#D6F5EF"
TEXT_PRI = "#1A1D23"
TEXT_SEC = "#5A6375"
TEXT_MUT = "#9DA8B7"
BORDER   = "#E2E6EC"
BG_BASE  = "#F0F9F8"

# ── 스텝 콘텐츠 ────────────────────────────────────────────────────────
_STEPS_EN = [
    {
        "step":     "1 / 4",
        "title":    "Measure Your Posture",
        "subtitle": "Dr.ZZOOK is watching you!\nWe'll help you fix your posture.",
        "image":    os.path.join(_ASSETS, "tutorial_en_step1.png"),
    },
    {
        "step":     "2 / 4",
        "title":    "Focus with Pomodoro Timer",
        "subtitle": "Set focus time, break time, and goals.\nBoost your concentration!",
        "image":    os.path.join(_ASSETS, "tutorial_en_step2.png"),
    },
    {
        "step":     "3 / 4",
        "title":    "Manage Tasks with To-Do",
        "subtitle": "Handle urgent and important tasks first.",
        "image":    os.path.join(_ASSETS, "tutorial_en_step3.png"),
    },
    {
        "step":     "4 / 4",
        "title":    "Compete with Friends",
        "subtitle": "Who's better at posture and focus?\nLet's find out!",
        "image":    os.path.join(_ASSETS, "tutorial_en_step4.png"),
    },
]

_STEPS_KO = [
    {
        "step":     "1 / 4",
        "title":    "자세를 측정해요",
        "subtitle": "Dr.ZZOOK이 당신을 감시하고 있어요!\n교정을 도와줄 거예요",
        "image":    os.path.join(_ASSETS, "tutorial_ko_step1.png"),
    },
    {
        "step":     "2 / 4",
        "title":    "뽀모도로 타이머로 집중해요",
        "subtitle": "집중 시간과 휴식 시간, 목표를 설정해요\n당신의 집중력을 높여줄 거예요",
        "image":    os.path.join(_ASSETS, "tutorial_ko_step2.png"),
    },
    {
        "step":     "3 / 4",
        "title":    "투두리스트로 일정을 관리해요",
        "subtitle": "급한 일, 중요한 일부터 처리해요",
        "image":    os.path.join(_ASSETS, "tutorial_ko_step3.png"),
    },
    {
        "step":     "4 / 4",
        "title":    "친구들과 함께해요",
        "subtitle": "자세 교정도 집중도\n누가 더 잘하는지 경쟁해요",
        "image":    os.path.join(_ASSETS, "tutorial_ko_step4.png"),
    },
]


class TutorialOverlay:
    def __init__(self, page: ft.Page, on_close=None):
        self.page     = page
        self.on_close = on_close
        self._step    = 0

        # refs
        self._wrap_ref       = ft.Ref()   # 전체 오버레이 (show/hide)
        self._image_ref      = ft.Ref()   # ft.Image
        self._step_ref       = ft.Ref()   # "1 / 4" 라벨
        self._title_ref      = ft.Ref()   # 제목
        self._subtitle_ref   = ft.Ref()   # 부제
        self._dots_ref       = ft.Ref()   # 도트 Row
        self._prev_wrap_ref  = ft.Ref()   # prev 버튼 Container (visible toggle)
        self._next_label_ref = ft.Ref()   # Next/Done 텍스트
        self._skip_label_ref = ft.Ref()   # Skip 텍스트

    # ── 내부 헬퍼 ────────────────────────────────────────────────────
    def _steps(self):
        return _STEPS_KO if lang_store.get() == "ko" else _STEPS_EN

    def _build_dots(self, n: int, cur: int):
        return [
            ft.Container(
                width=20 if i == cur else 8,
                height=8,
                border_radius=4,
                bgcolor=ACCENT if i == cur else BORDER,
            )
            for i in range(n)
        ]

    def _go_to(self, step: int):
        self._step = step
        steps = self._steps()
        n = len(steps)
        s = steps[step]
        is_last = step == n - 1

        if self._image_ref.current:
            self._image_ref.current.src = s["image"]
            self._image_ref.current.update()
        if self._step_ref.current:
            self._step_ref.current.value = s["step"]
            self._step_ref.current.update()
        if self._title_ref.current:
            self._title_ref.current.value = s["title"]
            self._title_ref.current.update()
        if self._subtitle_ref.current:
            self._subtitle_ref.current.value = s["subtitle"]
            self._subtitle_ref.current.update()
        if self._dots_ref.current:
            self._dots_ref.current.controls = self._build_dots(n, step)
            self._dots_ref.current.update()
        if self._prev_wrap_ref.current:
            self._prev_wrap_ref.current.opacity = 1 if step > 0 else 0
            self._prev_wrap_ref.current.update()
        if self._next_label_ref.current:
            self._next_label_ref.current.value = (
                lang_store.t("tut_done") if is_last else lang_store.t("tut_next")
            )
            self._next_label_ref.current.update()

    # ── 이벤트 핸들러 ────────────────────────────────────────────────
    def _on_prev(self, e):
        if self._step > 0:
            self._go_to(self._step - 1)

    def _on_next(self, e):
        steps = self._steps()
        if self._step < len(steps) - 1:
            self._go_to(self._step + 1)
        else:
            self.close()

    def _on_skip(self, e):
        self.close()

    # ── 공개 API ─────────────────────────────────────────────────────
    def close(self):
        if self._wrap_ref.current:
            self._wrap_ref.current.visible = False
            self._wrap_ref.current.update()
        if self.on_close:
            self.on_close()

    def show(self):
        """언제든 다시 열 때 호출 — step 0으로 초기화 후 표시."""
        self._step = 0
        steps = self._steps()
        n = len(steps)
        s = steps[0]

        if self._image_ref.current:
            self._image_ref.current.src = s["image"]
        if self._step_ref.current:
            self._step_ref.current.value = s["step"]
        if self._title_ref.current:
            self._title_ref.current.value = s["title"]
        if self._subtitle_ref.current:
            self._subtitle_ref.current.value = s["subtitle"]
        if self._dots_ref.current:
            self._dots_ref.current.controls = self._build_dots(n, 0)
        if self._prev_wrap_ref.current:
            self._prev_wrap_ref.current.opacity = 0
        if self._next_label_ref.current:
            self._next_label_ref.current.value = lang_store.t("tut_next")
        if self._skip_label_ref.current:
            self._skip_label_ref.current.value = lang_store.t("tut_skip")
        if self._wrap_ref.current:
            self._wrap_ref.current.visible = True
            self._wrap_ref.current.update()
        self.page.update()

    # ── 빌드 ─────────────────────────────────────────────────────────
    def build(self) -> ft.Control:
        steps = self._steps()
        n = len(steps)
        s = steps[0]

        # ── 이미지 영역 ───────────────────────────────────────────
        img = ft.Image(
            ref=self._image_ref,
            src=s["image"],
            fit="contain",
            width=780,
            error_content=ft.Container(
                content=ft.Text("Dashboard Screenshot", color=TEXT_MUT,
                                font_family=FONT, size=13),
                alignment=ft.Alignment(0, 0),
                bgcolor=BG_BASE,
                expand=True,
            ),
        )

        image_area = ft.Container(
            content=img,
            height=365,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            border_radius=ft.border_radius.only(top_left=16, top_right=16),
            bgcolor=BG_BASE,
            alignment=ft.Alignment(0, 0),
        )

        # ── 텍스트 영역 ───────────────────────────────────────────
        step_label = ft.Text(
            ref=self._step_ref,
            value=s["step"],
            size=12,
            color=ACCENT,
            font_family=FONT,
        )

        title = ft.Text(
            ref=self._title_ref,
            value=s["title"],
            size=21,
            weight=ft.FontWeight.BOLD,
            font_family=FONT,
            color=TEXT_PRI,
            text_align=ft.TextAlign.CENTER,
        )

        subtitle = ft.Text(
            ref=self._subtitle_ref,
            value=s["subtitle"],
            size=14,
            font_family=FONT,
            color=TEXT_SEC,
            text_align=ft.TextAlign.CENTER,
        )

        # ── 도트 인디케이터 ───────────────────────────────────────
        dots_row = ft.Row(
            ref=self._dots_ref,
            controls=self._build_dots(n, 0),
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
        )

        # ── 네비게이션 버튼 ───────────────────────────────────────
        prev_btn = ft.Container(
            ref=self._prev_wrap_ref,
            content=ft.IconButton(
                icon=ft.Icons.ARROW_BACK_IOS_ROUNDED,
                icon_color=TEXT_SEC,
                icon_size=18,
                on_click=self._on_prev,
                style=ft.ButtonStyle(overlay_color=ft.Colors.TRANSPARENT),
            ),
            width=48,
            opacity=0,  # 공간 유지하면서 투명하게
        )

        skip_btn = ft.TextButton(
            content=ft.Text(
                ref=self._skip_label_ref,
                value=lang_store.t("tut_skip"),
                size=13,
                font_family=FONT,
                color=TEXT_MUT,
            ),
            style=ft.ButtonStyle(overlay_color=ft.Colors.TRANSPARENT),
            on_click=self._on_skip,
        )

        next_btn = ft.ElevatedButton(
            content=ft.Text(
                ref=self._next_label_ref,
                value=lang_store.t("tut_next"),
                size=14,
                font_family=FONT,
                color="#FFFFFF",
            ),
            bgcolor=ACCENT,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.padding.symmetric(horizontal=24, vertical=10),
                elevation=0,
                overlay_color=ft.Colors.with_opacity(0.1, "#FFFFFF"),
            ),
            on_click=self._on_next,
        )

        # 도트는 Stack으로 완벽 중앙 고정, nav 버튼은 양 끝 (nav가 위 레이어여야 클릭 가능)
        bottom_row = ft.Stack(
            controls=[
                # 아래 레이어: dots 정중앙
                ft.Container(
                    content=dots_row,
                    alignment=ft.Alignment(0, 0),
                    expand=True,
                ),
                # 위 레이어: prev ← → skip+next (클릭 받아야 해서 위에)
                ft.Row(
                    controls=[
                        prev_btn,
                        ft.Row(controls=[skip_btn, next_btn], spacing=8),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True,
                ),
            ],
            expand=True,
        )

        text_area = ft.Container(
            content=ft.Column(
                controls=[
                    step_label,
                    ft.Container(height=2),
                    title,
                    ft.Container(height=4),
                    ft.Container(
                        content=subtitle,
                        height=36,
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Container(height=6),
                    bottom_row,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
            padding=ft.padding.only(left=32, right=32, top=10, bottom=16),
            expand=True,
        )

        # ── 카드 ─────────────────────────────────────────────────
        card = ft.Container(
            content=ft.Column(
                controls=[image_area, text_area],
                spacing=0,
                expand=True,
            ),
            width=800,
            height=510,
            bgcolor="#FFFFFF",
            border_radius=16,
            shadow=ft.BoxShadow(
                blur_radius=40,
                spread_radius=0,
                color=ft.Colors.with_opacity(0.28, "#000000"),
                offset=ft.Offset(0, 10),
            ),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

        # ── 전체 오버레이 ─────────────────────────────────────────
        overlay = ft.Container(
            ref=self._wrap_ref,
            content=ft.Stack(
                controls=[
                    # 반투명 백드롭
                    ft.Container(
                        expand=True,
                        bgcolor="#00000088",
                    ),
                    # 중앙 카드
                    ft.Container(
                        content=card,
                        alignment=ft.Alignment(0, 0),
                        expand=True,
                    ),
                ],
                expand=True,
            ),
            expand=True,
            visible=False,
        )

        return overlay
