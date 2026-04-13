import flet as ft

BG_NAV = "#080B10"
ACCENT = "#00E5CC"
TEXT_MUTED = "#3A4A5C"
TEXT_ACTIVE = "#E8EDF3"
INDICATOR = "#0D1117"


class NavBar:
    def __init__(self, navigate_fn):
        self.navigate = navigate_fn
        self.active = "dashboard"
        self.buttons: dict[str, ft.Container] = {}
        self.items = [
            ("dashboard", "\ue871",  "대시보드"),
            ("posture",   "\ue3a5",  "자세 교정"),
            ("pomodoro",  "\ue425",  "뽀모도로"),
            ("todo",      "\ue8ef",  "할 일"),
            ("ranking",   "\ue8b6",  "랭킹"),
        ]

    def _nav_btn(self, key: str, icon: str, label: str) -> ft.Container:
        is_active = key == self.active

        def on_hover(e):
            if key != self.active:
                e.control.bgcolor = "#0D1117" if e.data == "true" else "transparent"
                e.control.update()

        def on_click(_):
            self.update_active(key)
            self.navigate(key)

        icon_text = ft.Text(
            icon,
            font_family="Material Icons",
            size=22,
            color=ACCENT if is_active else TEXT_MUTED,
        )
        label_text = ft.Text(
            label,
            size=11,
            weight=ft.FontWeight.W_600,
            color=ACCENT if is_active else TEXT_MUTED,
            font_family="Pretendard",
        )

        indicator = ft.Container(
            width=3,
            height=36,
            bgcolor=ACCENT if is_active else "transparent",
            border_radius=ft.BorderRadius(0, 4, 0, 4),
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
                        padding=ft.padding.only(left=0, top=10, right=8, bottom=10),
                    ),
                ],
                spacing=0,
            ),
            bgcolor="transparent",
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
            icon_t.color = ACCENT if is_active else TEXT_MUTED
            label_t.color = ACCENT if is_active else TEXT_MUTED
            btn.bgcolor = "#0D1117" if is_active else "transparent"
            btn.update()

    def build(self) -> ft.Container:
        logo = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Text("F", size=20, weight=ft.FontWeight.W_900,
                                        color="#080B10", font_family="Pretendard"),
                        width=38, height=38,
                        bgcolor=ACCENT,
                        border_radius=10,
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Text("Focus\nMate", size=10, color=ACCENT,
                            weight=ft.FontWeight.W_700, text_align=ft.TextAlign.CENTER,
                            font_family="Pretendard"),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            padding=ft.padding.only(left=0, top=24, right=0, bottom=28),
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
                    ft.Text("\ue8b8", font_family="Material Icons", size=20, color=TEXT_MUTED),
                    ft.Text("설정", size=10, color=TEXT_MUTED, font_family="Pretendard"),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
            ),
            padding=ft.padding.only(left=0, top=8, right=0, bottom=24),
            alignment=ft.Alignment(0, 0),
            on_hover=lambda e: None,
        )

        return ft.Container(
            content=ft.Column(
                controls=[logo, nav_buttons, settings_btn],
                spacing=0,
            ),
            width=76,
            bgcolor=BG_NAV,
            border_radius=0,
        )
