import flet as ft

BG_DARK = "#080B10"
BG_CARD = "#0D1117"
BG_CARD2 = "#131920"
ACCENT = "#00E5CC"
ACCENT2 = "#FF6B6B"
TEXT_PRIMARY = "#E8EDF3"
TEXT_MUTED = "#4A5568"
BORDER = "#1A2332"


def card(content: ft.Control, padding=20, expand=False, **kwargs) -> ft.Container:
    return ft.Container(
        content=content,
        bgcolor=BG_CARD,
        border_radius=16,
        padding=padding,
        border=ft.border.all(1, BORDER),
        expand=expand,
        **kwargs,
    )


def section_title(text: str, sub: str = "") -> ft.Column:
    controls = [
        ft.Text(text, size=22, weight=ft.FontWeight.W_800,
                color=TEXT_PRIMARY, font_family="Pretendard"),
    ]
    if sub:
        controls.append(
            ft.Text(sub, size=13, color=TEXT_MUTED, font_family="Pretendard")
        )
    return ft.Column(controls=controls, spacing=2)


def accent_btn(label: str, on_click=None, icon: str = "", width=None,
               color=ACCENT) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            controls=[
                *(
                    [ft.Text(icon, font_family="Material Icons", size=16, color="#080B10")]
                    if icon else []
                ),
                ft.Text(label, size=13, weight=ft.FontWeight.W_700,
                        color="#080B10", font_family="Pretendard"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
        ),
        bgcolor=color,
        border_radius=10,
        padding=ft.padding.only(left=16, top=10, right=16, bottom=10),
        width=width,
        on_click=on_click,
        animate=ft.Animation(120, ft.AnimationCurve.EASE_OUT),
        on_hover=lambda e: setattr(e.control, 'opacity',
                                   0.85 if e.data == "true" else 1.0) or e.control.update(),
    )


def ghost_btn(label: str, on_click=None, icon: str = "") -> ft.Container:
    return ft.Container(
        content=ft.Row(
            controls=[
                *(
                    [ft.Text(icon, font_family="Material Icons", size=16, color=ACCENT)]
                    if icon else []
                ),
                ft.Text(label, size=13, weight=ft.FontWeight.W_600,
                        color=ACCENT, font_family="Pretendard"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
        ),
        border=ft.border.all(1, ACCENT),
        border_radius=10,
        padding=ft.padding.only(left=16, top=10, right=16, bottom=10),
        on_click=on_click,
    )


def stat_chip(label: str, value: str, color: str = ACCENT) -> ft.Container:
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(value, size=24, weight=ft.FontWeight.W_900,
                        color=color, font_family="Pretendard"),
                ft.Text(label, size=11, color=TEXT_MUTED, font_family="Pretendard"),
            ],
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=BG_CARD2,
        border_radius=12,
        padding=ft.padding.only(left=20, top=14, right=20, bottom=14),
        border=ft.border.all(1, BORDER),
    )
