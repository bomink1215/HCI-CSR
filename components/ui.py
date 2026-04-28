import flet as ft

# ── 디자인 토큰 ───────────────────────────────────────────────────
BG_BASE   = "#FFFFFF"
BG_CARD   = "#F4F6F8"
BG_CARD2  = "#EAECEF"
BG_HOVER  = "#EDF9F6"

ACCENT    = "#00C9A7"
ACCENT_DK = "#009E83"
ACCENT_LT = "#D6F5EF"
DANGER    = "#FF5C5C"
WARNING   = "#FFB347"

TEXT_PRI  = "#1A1D23"
TEXT_SEC  = "#5A6375"
TEXT_MUT  = "#9DA8B7"

BORDER    = "#E2E6EC"
SHADOW    = "#00000012"

RADIUS    = 14
RADIUS_SM = 8

# ── 폰트 상수 (한 곳에서 관리) ───────────────────────────────────
FONT      = "DOSSaemmul"   # 본문 폰트
FONT_MONO = "DOSSaemmul"      # 숫자/코드 폰트

# W300 기준 weight 매핑
W_LIGHT   = ft.FontWeight.W_400   # 기본 본문
W_REGULAR = ft.FontWeight.W_400   # 일반 강조
W_MEDIUM  = ft.FontWeight.W_500   # 소제목
W_BOLD    = ft.FontWeight.W_700   # 제목·버튼


def card(content: ft.Control, padding=20, expand=False, **kwargs) -> ft.Container:
    return ft.Container(
        content=content,
        bgcolor=BG_CARD,
        border_radius=RADIUS,
        padding=padding,
        border=ft.border.all(1, BORDER),
        shadow=ft.BoxShadow(blur_radius=12, color=SHADOW, offset=ft.Offset(0, 2)),
        expand=expand,
        **kwargs,
    )


def section_title(text: str, sub: str = "") -> ft.Column:
    controls = [
        ft.Text(text, size=22, weight=W_BOLD, color=TEXT_PRI, font_family=FONT),
    ]
    if sub:
        controls.append(
            ft.Text(sub, size=13, weight=W_LIGHT, color=TEXT_SEC, font_family=FONT)
        )
    return ft.Column(controls=controls, spacing=2)


def accent_btn(label: str, on_click=None, icon: str = "", width=None,
               color=ACCENT) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            controls=[
                *(
                    [ft.Text(icon, font_family="Material Icons", size=16, color="#FFFFFF")]
                    if icon else []
                ),
                ft.Text(label, size=13, weight=W_MEDIUM,
                        color="#FFFFFF", font_family=FONT),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
        ),
        bgcolor=color,
        border_radius=RADIUS_SM,
        padding=ft.padding.only(left=18, top=11, right=18, bottom=11),
        width=width,
        on_click=on_click,
        animate=ft.Animation(120, ft.AnimationCurve.EASE_OUT),
        shadow=ft.BoxShadow(blur_radius=10, color=color + "55", offset=ft.Offset(0, 3)),
        on_hover=lambda e: setattr(e.control, 'opacity',
                                   0.88 if e.data == "true" else 1.0) or e.control.update(),
    )


def ghost_btn(label: str, on_click=None, icon: str = "") -> ft.Container:
    return ft.Container(
        content=ft.Row(
            controls=[
                *(
                    [ft.Text(icon, font_family="Material Icons", size=16, color=ACCENT)]
                    if icon else []
                ),
                ft.Text(label, size=13, weight=W_MEDIUM,
                        color=ACCENT, font_family=FONT),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
        ),
        border=ft.border.all(1.5, ACCENT),
        border_radius=RADIUS_SM,
        padding=ft.padding.only(left=16, top=10, right=16, bottom=10),
        on_click=on_click,
        on_hover=lambda e: (
            setattr(e.control, 'bgcolor', ACCENT_LT if e.data == "true" else "transparent")
            or e.control.update()
        ),
    )


def stat_chip(label: str, value: str, color: str = ACCENT) -> ft.Container:
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(value, size=24, weight=W_BOLD,
                        color=color, font_family=FONT),
                ft.Text(label, size=11, weight=W_LIGHT,
                        color=TEXT_MUT, font_family=FONT),
            ],
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=BG_CARD2,
        border_radius=RADIUS_SM,
        padding=ft.padding.only(left=20, top=14, right=20, bottom=14),
        border=ft.border.all(1, BORDER),
    )


def mascot_widget(size: int = 64) -> ft.Container:
    """픽셀아트 마스코트 — 순수 Flet Container 블록"""
    s = size / 64

    def px(w, h, color, radius=0):
        return ft.Container(
            width=round(w * s), height=round(h * s),
            bgcolor=color, border_radius=radius,
        )

    def spacer(w):
        return ft.Container(width=round(w * s), height=1)

    antenna = ft.Column(
        controls=[
            ft.Row([spacer(28), px(8, 4, ACCENT, 2)], spacing=0),
            ft.Row([spacer(30), px(4, 5, "#9DA8B7")], spacing=0),
        ],
        spacing=0,
    )

    face_content = ft.Column(
        controls=[
            ft.Row([spacer(6), px(6, 5, TEXT_PRI, 1), spacer(8), px(6, 5, TEXT_PRI, 1)], spacing=0),
            ft.Container(height=round(3 * s)),
            ft.Row([spacer(4), px(16, 3, TEXT_PRI, 1)], spacing=0),
        ],
        spacing=0,
    )

    head_row = ft.Row(
        controls=[
            px(5, 14, "#FFD6A5", 2),
            ft.Container(
                content=face_content,
                width=round(28 * s), height=round(20 * s),
                bgcolor="#FFD6A5",
                border_radius=round(4 * s),
                padding=ft.padding.only(top=round(5 * s)),
            ),
            px(5, 14, "#FFD6A5", 2),
        ],
        spacing=0,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    body_row = ft.Row(
        controls=[
            px(7, 5, ACCENT, 2),
            px(24, 16, ACCENT, 3),
            px(7, 5, ACCENT, 2),
        ],
        spacing=0,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    legs_row = ft.Row(
        controls=[spacer(6), px(8, 7, ACCENT_DK, 2), spacer(4), px(8, 7, ACCENT_DK, 2)],
        spacing=0,
    )

    return ft.Container(
        content=ft.Column(
            controls=[antenna, head_row, body_row, legs_row],
            spacing=round(1 * s),
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=size, height=size,
        alignment=ft.Alignment(0, 0),
    )
