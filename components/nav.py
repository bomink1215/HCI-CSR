import flet as ft

BG_NAV    = "#F4F6F8"
BG_ACTIVE = "#FFFFFF"
ACCENT    = "#00C9A7"
ACCENT_LT = "#D6F5EF"
TEXT_MUT  = "#9DA8B7"
TEXT_ACT  = "#1A1D23"
BORDER    = "#E2E6EC"


class NavBar:
    def __init__(self, navigate_fn):
        self.navigate = navigate_fn
        self.active = "dashboard"
        self.buttons: dict[str, ft.Container] = {}
        self.items = [
            ("dashboard", "\ue871",  "대시보드"),
            ("posture",   "\ue3a5",  "자세"),
            ("pomodoro",  "\ue425",  "타이머"),
            ("todo",      "\ue8ef",  "할 일"),
            ("ranking",   "\ue8b6",  "랭킹"),
        ]

    def _nav_btn(self, key: str, icon: str, label: str) -> ft.Container:
        is_active = key == self.active

        def on_hover(e):
            if key != self.active:
                e.control.bgcolor = ACCENT_LT if e.data == "true" else "transparent"
                e.control.update()

        def on_click(_):
            self.update_active(key)
            self.navigate(key)

        indicator = ft.Container(
            width=3,
            height=32,
            bgcolor=ACCENT if is_active else "transparent",
            border_radius=ft.BorderRadius(0, 4, 4, 0),
        )

        icon_text = ft.Text(
            icon,
            font_family="Material Icons",
            size=22,
            color=ACCENT if is_active else TEXT_MUT,
        )
        label_text = ft.Text(
            label,
            size=10,
            weight=ft.FontWeight.W_400,
            color=ACCENT if is_active else TEXT_MUT,
            font_family="DOSSaemmul",
        )

        btn = ft.Container(
            content=ft.Row(
                controls=[
                    indicator,
                    ft.Container(
                        content=ft.Column(
                            controls=[icon_text, label_text],
                            spacing=2,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        expand=True,
                        padding=ft.padding.only(top=10, right=6, bottom=10),
                    ),
                ],
                spacing=0,
            ),
            bgcolor=ACCENT_LT if is_active else "transparent",
            border_radius=8,
            on_hover=on_hover,
            on_click=on_click,
            animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
        )
        self.buttons[key] = btn
        return btn

    def update_active(self, key: str):
        self.active = key
        for k, btn in self.buttons.items():
            is_active = k == key
            row: ft.Row = btn.content
            indicator: ft.Container = row.controls[0]
            col: ft.Column = row.controls[1].content
            icon_t: ft.Text = col.controls[0]
            label_t: ft.Text = col.controls[1]

            indicator.bgcolor = ACCENT if is_active else "transparent"
            icon_t.color = ACCENT if is_active else TEXT_MUT
            label_t.color = ACCENT if is_active else TEXT_MUT
            btn.bgcolor = ACCENT_LT if is_active else "transparent"
            btn.update()

    def build(self) -> ft.Container:
        logo = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text("F", size=20, weight=ft.FontWeight.W_400,
                                        color="#FFFFFF", font_family="DOSSaemmul"),
                        width=38, height=38,
                        bgcolor=ACCENT,
                        border_radius=12,
                        alignment=ft.Alignment(0, 0),
                        shadow=ft.BoxShadow(blur_radius=12, color=ACCENT + "55",
                                            offset=ft.Offset(0, 3)),
                    ),
                    ft.Text("Focus\nMate", size=10, color=ACCENT,
                            weight=ft.FontWeight.W_400, text_align=ft.TextAlign.CENTER,
                            font_family="DOSSaemmul"),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
            ),
            padding=ft.padding.only(top=24, bottom=28),
            alignment=ft.Alignment(0, 0),
        )

        nav_buttons = ft.Column(
            controls=[self._nav_btn(k, i, l) for k, i, l in self.items],
            spacing=4,
            expand=True,
        )

        settings_btn = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("\ue8b8", font_family="Material Icons", size=20, color=TEXT_MUT),
                    ft.Text("설정", size=10, color=TEXT_MUT, font_family="DOSSaemmul"),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
            ),
            padding=ft.padding.only(top=8, bottom=24),
            alignment=ft.Alignment(0, 0),
        )

        return ft.Container(
            content=ft.Column(
                controls=[logo, nav_buttons, settings_btn],
                spacing=0,
            ),
            width=76,
            bgcolor=BG_NAV,
            border_radius=0,
            border=ft.border.only(right=ft.BorderSide(1, BORDER)),
        )
