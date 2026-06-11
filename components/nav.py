import flet as ft
from utils import lang as lang_store

BG_NAV    = "#F4F6F8"
BG_ACTIVE = "#FFFFFF"
ACCENT    = "#00C9A7"
ACCENT_LT = "#D6F5EF"
TEXT_MUT  = "#9DA8B7"
TEXT_ACT  = "#1A1D23"
BORDER    = "#E2E6EC"


class NavBar:
    def __init__(self, navigate_fn, on_rebuild=None, show_tutorial_cb=None):
        self.navigate          = navigate_fn
        self.on_rebuild        = on_rebuild
        self.show_tutorial_cb  = show_tutorial_cb
        self.active = "dashboard"
        self.buttons: dict[str, ft.Container] = {}
        self.lang_btn_refs: dict[str, ft.Ref] = {
            "en": ft.Ref(), "ko": ft.Ref()
        }
        self.items = [
            ("dashboard", ft.Icons.DASHBOARD,      lang_store.t("nav_dashboard")),
            ("posture",   ft.Icons.ACCESSIBILITY,  lang_store.t("nav_posture")),
            ("pomodoro",  ft.Icons.TIMER,          lang_store.t("nav_timer")),
            ("todo",      ft.Icons.CHECKLIST,      lang_store.t("nav_todo")),
            ("ranking",   ft.Icons.LEADERBOARD,    lang_store.t("nav_ranking")),
            ("profile",   ft.Icons.PERSON,         lang_store.t("nav_profile")),
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
            size=12,
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

    def _set_lang(self, code: str):
        """언어 변경 → 버튼 UI 갱신 → 메인 UI 리빌드."""
        lang_store.set_lang(code)
        # Update lang button appearance
        for c, ref in self.lang_btn_refs.items():
            btn = ref.current
            if btn:
                is_active = c == code
                btn.content.color = "#F0F9F8" if is_active else TEXT_MUT
                btn.bgcolor       = ACCENT if is_active else "transparent"
                btn.border        = ft.border.all(1, ACCENT if is_active else BORDER)
                btn.update()
        # Rebuild main UI so all translated strings refresh
        if self.on_rebuild:
            self.on_rebuild()

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

        def _on_help(e):
            if self.show_tutorial_cb:
                self.show_tutorial_cb()

        def _tutorial_btn():
            def on_hover(e):
                e.control.bgcolor = ACCENT_LT if e.data == "true" else "transparent"
                e.control.update()

            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(width=3, height=32, bgcolor="transparent",
                                     border_radius=ft.BorderRadius(0, 4, 4, 0)),
                        ft.Container(
                            content=ft.Column(
                                controls=[
                                    ft.Icon(ft.Icons.SCHOOL, size=22, color=TEXT_MUT),
                                    ft.Text(
                                        lang_store.t("tut_help_tooltip"),
                                        size=12, weight=ft.FontWeight.W_400,
                                        color=TEXT_MUT, font_family="DOSSaemmul",
                                    ),
                                ],
                                spacing=2,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            expand=True,
                            padding=ft.padding.only(top=10, right=6, bottom=10),
                        ),
                    ],
                    spacing=0,
                ),
                bgcolor="transparent",
                border_radius=8,
                on_hover=on_hover,
                on_click=_on_help,
                animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
            )

        nav_buttons = ft.Column(
            controls=[self._nav_btn(k, i, l) for k, i, l in self.items] + [_tutorial_btn()],
            spacing=4,
            expand=True,
        )

        def _lang_btn(code: str):
            is_active = lang_store.get() == code
            return ft.Container(
                ref=self.lang_btn_refs[code],
                content=ft.Text(
                    code.upper(), size=11,
                    color="#F0F9F8" if is_active else TEXT_MUT,
                    font_family="DOSSaemmul",
                    text_align=ft.TextAlign.CENTER,
                ),
                bgcolor=ACCENT if is_active else "transparent",
                border_radius=6,
                border=ft.border.all(1, ACCENT if is_active else BORDER),
                padding=ft.padding.symmetric(horizontal=6, vertical=4),
                on_click=lambda _, c=code: self._set_lang(c),
                animate=ft.Animation(120, ft.AnimationCurve.EASE_OUT),
                expand=True,
                alignment=ft.Alignment(0, 0),
            )

        bottom_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Image(
                            src="assets/mascot.png",
                            width=56,
                            height=56,
                            fit="contain",
                        ),
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Container(height=6),
                    ft.Container(
                        content=ft.Row(
                            controls=[_lang_btn("en"), _lang_btn("ko")],
                            spacing=4,
                        ),
                        padding=ft.padding.symmetric(horizontal=8),
                    ),
                    ft.Container(height=4),
                    ft.Text(
                        lang_store.t("nav_lang_label"),
                        size=9,
                        color=TEXT_MUT,
                        font_family="DOSSaemmul",
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=14),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            ),
        )

        return ft.Container(
            content=ft.Column(
                controls=[logo, nav_buttons, bottom_section],
                spacing=0,
            ),
            width=76,
            bgcolor=BG_NAV,
            border_radius=0,
            border=ft.border.only(right=ft.BorderSide(1, BORDER)),
        )
