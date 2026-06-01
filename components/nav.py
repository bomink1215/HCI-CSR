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
            ("dashboard", ft.Icons.DASHBOARD,      "Dashboard"),
            ("posture",   ft.Icons.ACCESSIBILITY,  "Posture"),
            ("pomodoro",  ft.Icons.TIMER,          "Timer"),
            ("todo",      ft.Icons.CHECKLIST,      "To-Do"),
            ("ranking",   ft.Icons.LEADERBOARD,    "Ranking"),
            ("profile",   ft.Icons.PERSON,         "Profile"),
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

        icon_widget = ft.Icon(
            icon,
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
                            controls=[icon_widget, label_text],
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
            icon_w: ft.Icon = col.controls[0]
            label_t: ft.Text = col.controls[1]

            indicator.bgcolor = ACCENT if is_active else "transparent"
            icon_w.color = ACCENT if is_active else TEXT_MUT
            label_t.color = ACCENT if is_active else TEXT_MUT
            btn.bgcolor = ACCENT_LT if is_active else "transparent"
            btn.update()

    def build(self) -> ft.Container:
        logo = ft.Container(
            content=ft.Image(
                src="assets/logo_zzook.png",
                width=56,
                height=28,
                fit="contain",
            ),
            padding=ft.padding.only(top=24, bottom=28),
            alignment=ft.Alignment(0, 0),
        )

        nav_buttons = ft.Column(
            controls=[self._nav_btn(k, i, l) for k, i, l in self.items],
            spacing=4,
            expand=True,
        )

        mascot = ft.Container(
            content=ft.Image(
                src="assets/mascot.png",
                width=104,
                height=104,
                fit="contain",
            ),
            padding=ft.padding.only(bottom=24),
            alignment=ft.Alignment(0, 0),
        )

        return ft.Container(
            content=ft.Column(
                controls=[logo, nav_buttons, mascot],
                spacing=0,
            ),
            width=76,
            bgcolor=BG_NAV,
            border_radius=0,
            border=ft.border.only(right=ft.BorderSide(1, BORDER)),
        )
