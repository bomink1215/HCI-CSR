import flet as ft
import asyncio
from components.ui import mascot_widget
from utils import firebase

BG_BASE   = "#F0F9F8"
BG_CARD   = "#F4F6F8"
BG_CARD2  = "#EAECEF"
ACCENT    = "#7AC3B8"
ACCENT_LT = "#D6F5EF"
DANGER    = "#FF5C5C"
TEXT_PRI  = "#1A1D23"
TEXT_MUT  = "#9DA8B7"
BORDER    = "#E2E6EC"
FONT      = "DOSSaemmul"


class AuthView:
    def __init__(self, page: ft.Page, on_login_success):
        self.page             = page
        self.on_login_success = on_login_success
        self.mode             = "login"   # "login" | "signup"

        self.username_ref           = ft.Ref()
        self.password_ref           = ft.Ref()
        self.nickname_ref           = ft.Ref()
        self.nickname_wrap_ref      = ft.Ref()
        self.nick_check_btn_ref     = ft.Ref()
        self.nick_check_msg_ref     = ft.Ref()
        self.error_ref              = ft.Ref()
        self.submit_text_ref        = ft.Ref()
        self.submit_btn_ref         = ft.Ref()
        self.nickname_verified      = False   # 중복확인 통과 여부
        self.remember_me_ref     = ft.Ref()
        self.loading_ref         = ft.Ref()
        self.tab_login_ref       = ft.Ref()
        self.tab_signup_ref      = ft.Ref()
        self.tab_login_text_ref  = ft.Ref()
        self.tab_signup_text_ref = ft.Ref()
        self.heading_ref         = ft.Ref()
        self.subheading_ref      = ft.Ref()

    # ── 탭 전환 ─────────────────────────────────────────────────────
    def _switch_mode(self, mode: str):
        self.mode = mode
        for m, t_ref, tx_ref in [
            ("login",  self.tab_login_ref,  self.tab_login_text_ref),
            ("signup", self.tab_signup_ref, self.tab_signup_text_ref),
        ]:
            active = m == mode
            if t_ref.current:
                t_ref.current.bgcolor = ACCENT_LT if active else "transparent"
                t_ref.current.border  = ft.border.all(1, ACCENT if active else "transparent")
                t_ref.current.update()
            if tx_ref.current:
                tx_ref.current.color = ACCENT if active else TEXT_MUT
                tx_ref.current.update()

        if self.nickname_wrap_ref.current:
            self.nickname_wrap_ref.current.visible = (mode == "signup")
            self.nickname_wrap_ref.current.update()

        # 탭 전환 시 닉네임 확인 상태 초기화
        self.nickname_verified = False
        self._set_nick_msg("", ok=False)

        if self.submit_text_ref.current:
            self.submit_text_ref.current.value = "Sign Up" if mode == "signup" else "Log In"
            self.submit_text_ref.current.update()

        if self.heading_ref.current:
            self.heading_ref.current.value = "Create an account" if mode == "signup" else "Welcome back"
            self.heading_ref.current.update()

        if self.subheading_ref.current:
            self.subheading_ref.current.value = (
                "Join ZZOOK and start your journey"
                if mode == "signup"
                else "Sign in to your account or create a new one"
            )
            self.subheading_ref.current.update()

        self._set_error("")

    # ── 닉네임 중복확인 ──────────────────────────────────────────────
    def _set_nick_msg(self, msg: str, ok: bool):
        if self.nick_check_msg_ref.current:
            self.nick_check_msg_ref.current.value   = msg
            self.nick_check_msg_ref.current.color   = "#B9E6E0" if ok else DANGER
            self.nick_check_msg_ref.current.visible = bool(msg)
            self.nick_check_msg_ref.current.update()

    def _check_nickname(self, e=None):
        nickname = (self.nickname_ref.current.value or "").strip()
        if not nickname:
            self._set_nick_msg("Enter a nickname", ok=False)
            return

        async def _work():
            try:
                exists = await asyncio.to_thread(firebase.nickname_exists, nickname)
                if exists:
                    self.nickname_verified = False
                    self._set_nick_msg("Nickname already taken", ok=False)
                else:
                    self.nickname_verified = True
                    self._set_nick_msg("Available ✓", ok=True)
            except Exception:
                self._set_nick_msg("Network error", ok=False)

        self.page.run_task(_work)

    # ── 유틸 ────────────────────────────────────────────────────────
    def _set_error(self, msg: str):
        if self.error_ref.current:
            self.error_ref.current.value   = msg
            self.error_ref.current.visible = bool(msg)
            self.error_ref.current.update()

    def _set_loading(self, on: bool):
        if self.loading_ref.current:
            self.loading_ref.current.visible = on
            self.loading_ref.current.update()
        if self.submit_btn_ref.current:
            self.submit_btn_ref.current.disabled = on
            self.submit_btn_ref.current.update()

    # ── 제출 ────────────────────────────────────────────────────────
    def _submit(self, e=None):
        username = (self.username_ref.current.value or "").strip()
        password = (self.password_ref.current.value or "")
        nickname = (self.nickname_ref.current.value or "").strip()

        if not username:
            self._set_error("Enter a username"); return
        if " " in username:
            self._set_error("Username cannot contain spaces"); return
        if not password:
            self._set_error("Enter a password"); return
        if self.mode == "signup" and not nickname:
            self._set_error("Enter a nickname"); return
        if self.mode == "signup" and not self.nickname_verified:
            self._set_error("Please check nickname availability first"); return

        self._set_loading(True)
        self._set_error("")

        async def _work():
            try:
                if self.mode == "signup":
                    result = await asyncio.to_thread(
                        lambda: firebase.sign_up(username, password, nickname,
                                                 nickname_verified=self.nickname_verified)
                    )
                else:
                    result = await asyncio.to_thread(firebase.sign_in, username, password)

                if "error" in result:
                    self._set_error(result["error"])
                else:
                    result["remember_me"] = bool(
                        self.mode == "login"
                        and self.remember_me_ref.current
                        and self.remember_me_ref.current.value
                    )
                    self.on_login_success(result)
            except Exception:
                self._set_error("Network error")
            finally:
                self._set_loading(False)

        self.page.run_task(_work)

    # ── 빌드 ────────────────────────────────────────────────────────
    def build(self) -> ft.Container:

        def _tab(mode, label, t_ref, tx_ref):
            active = mode == self.mode
            return ft.Container(
                ref=t_ref,
                content=ft.Text(
                    ref=tx_ref,
                    value=label, size=13, font_family=FONT,
                    color=ACCENT if active else TEXT_MUT,
                    text_align=ft.TextAlign.CENTER,
                ),
                bgcolor=ACCENT_LT if active else "transparent",
                border_radius=8,
                border=ft.border.all(1, ACCENT if active else "transparent"),
                padding=ft.padding.symmetric(horizontal=20, vertical=8),
                on_click=lambda _, m=mode: self._switch_mode(m),
                expand=True,
                alignment=ft.Alignment(0, 0),
            )

        def _field(ref, hint, icon, password=False):
            return ft.TextField(
                ref=ref,
                hint_text=hint,
                hint_style=ft.TextStyle(color=TEXT_MUT, font_family=FONT, size=13),
                text_style=ft.TextStyle(color=TEXT_PRI, font_family=FONT, size=13),
                border_color=BORDER,
                focused_border_color=ACCENT,
                border_radius=10,
                content_padding=ft.padding.symmetric(horizontal=14, vertical=13),
                password=password,
                can_reveal_password=password,
                prefix_icon=icon,
                bgcolor=BG_BASE,
                cursor_color=ACCENT,
                on_submit=self._submit,
            )

        def _feature_row(icon, title, desc):
            return ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(icon, color=ACCENT, size=20),
                        bgcolor=BG_BASE,
                        border_radius=10,
                        padding=ft.padding.all(10),
                    ),
                    ft.Container(width=12),
                    ft.Column(
                        controls=[
                            ft.Text(title, size=13, color=TEXT_PRI, font_family=FONT,
                                    weight=ft.FontWeight.W_600),
                            ft.Text(desc, size=11, color=TEXT_MUT, font_family=FONT),
                        ],
                        spacing=1,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            )

        # ── 왼쪽 패널 (브랜딩) ─────────────────────────────────────
        left_panel = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(expand=True),
                    ft.Column(
                        controls=[
                            mascot_widget(80),
                            ft.Container(height=12),
                            ft.Image(
                                src="assets/logo_zzook.png",
                                width=240,
                                height=75,
                                fit="contain",
                            ),
                            ft.Container(height=4),
                            ft.Text("Build your rhythm of focus and rest",
                                    size=13, color=TEXT_MUT, font_family=FONT,
                                    text_align=ft.TextAlign.CENTER),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=4,
                    ),
                    ft.Container(height=40),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                _feature_row(ft.Icons.TIMER_OUTLINED,
                                             "Pomodoro Timer",
                                             "Stay focused with timed sessions"),
                                ft.Container(height=16),
                                _feature_row(ft.Icons.ACCESSIBILITY_NEW_OUTLINED,
                                             "Posture Monitor",
                                             "Keep your posture healthy"),
                                ft.Container(height=16),
                                _feature_row(ft.Icons.LEADERBOARD_OUTLINED,
                                             "Leaderboard",
                                             "Compete with friends"),
                            ],
                            spacing=0,
                        ),
                        bgcolor="#EAECEF",
                        border_radius=14,
                        border=ft.border.all(1, BORDER),
                        padding=ft.padding.all(20),
                    ),
                    ft.Container(expand=True),
                ],
                spacing=0,
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            expand=2,
            bgcolor=ACCENT_LT,
            padding=ft.padding.symmetric(horizontal=40, vertical=40),
        )

        # ── 오른쪽 패널 (폼) ────────────────────────────────────────
        form_column = ft.Column(
            controls=[
                ft.Container(expand=True),
                ft.Column(
                    controls=[
                        ft.Text(ref=self.heading_ref,
                                value="Welcome back", size=22, color=TEXT_PRI,
                                font_family=FONT, weight=ft.FontWeight.W_700),
                        ft.Text(ref=self.subheading_ref,
                                value="Sign in to your account or create a new one",
                                size=12, color=TEXT_MUT, font_family=FONT),
                        ft.Container(height=28),
                        # 탭
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    _tab("login",  "Log In",  self.tab_login_ref,  self.tab_login_text_ref),
                                    _tab("signup", "Sign Up", self.tab_signup_ref, self.tab_signup_text_ref),
                                ],
                                spacing=4,
                            ),
                            bgcolor=BG_CARD2,
                            border_radius=10,
                            border=ft.border.all(1, BORDER),
                            padding=4,
                        ),
                        ft.Container(height=20),
                        # 입력 필드
                        _field(self.username_ref, "ID", ft.Icons.PERSON_OUTLINE),
                        ft.Container(height=10),
                        _field(self.password_ref, "Password", ft.Icons.LOCK_OUTLINE, password=True),
                        ft.Container(height=6),
                        # Remember me (로그인 전용)
                        ft.Checkbox(
                            ref=self.remember_me_ref,
                            label="Remember me on this device",
                            label_style=ft.TextStyle(
                                size=12, color=TEXT_MUT, font_family=FONT,
                            ),
                            fill_color={
                                ft.ControlState.SELECTED: ACCENT,
                                ft.ControlState.DEFAULT: TEXT_MUT,
                            },
                            value=False,
                        ),
                        ft.Container(height=4),
                        # 닉네임 (회원가입 전용)
                        ft.Container(
                            ref=self.nickname_wrap_ref,
                            content=ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Container(
                                                content=_field(self.nickname_ref, "Nickname",
                                                               ft.Icons.BADGE_OUTLINED),
                                                expand=True,
                                            ),
                                            ft.Container(width=8),
                                            ft.Container(
                                                ref=self.nick_check_btn_ref,
                                                content=ft.Text("Check", size=12,
                                                                color="#F0F9F8", font_family=FONT,
                                                                text_align=ft.TextAlign.CENTER),
                                                bgcolor=ACCENT,
                                                border_radius=10,
                                                padding=ft.padding.symmetric(horizontal=14, vertical=16),
                                                on_click=self._check_nickname,
                                            ),
                                        ],
                                        spacing=0,
                                        vertical_alignment=ft.CrossAxisAlignment.START,
                                    ),
                                    ft.Text(
                                        ref=self.nick_check_msg_ref,
                                        value="", size=11, visible=False,
                                        font_family=FONT,
                                    ),
                                    ft.Container(height=6),
                                ],
                                spacing=4,
                            ),
                            visible=False,
                        ),
                        # 에러 메시지
                        ft.Container(
                            content=ft.Text(
                                ref=self.error_ref,
                                value="", size=11, color=DANGER,
                                font_family=FONT, visible=False,
                                text_align=ft.TextAlign.CENTER,
                            ),
                            alignment=ft.Alignment(0, 0),
                        ),
                        ft.Container(height=6),
                        # 제출 버튼
                        ft.Container(
                            ref=self.submit_btn_ref,
                            content=ft.Stack(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Text(
                                                ref=self.submit_text_ref,
                                                value="Log In", size=14,
                                                color="#F0F9F8", font_family=FONT,
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                    ),
                                    ft.Row(
                                        ref=self.loading_ref,
                                        controls=[
                                            ft.ProgressRing(
                                                width=18, height=18,
                                                stroke_width=2, color="#F0F9F8",
                                            ),
                                        ],
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        visible=False,
                                    ),
                                ],
                            ),
                            bgcolor=ACCENT,
                            border_radius=10,
                            padding=ft.padding.symmetric(vertical=14),
                            on_click=self._submit,
                            shadow=ft.BoxShadow(
                                blur_radius=12, color=ACCENT + "55",
                                offset=ft.Offset(0, 3),
                            ),
                        ),
                    ],
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    width=380,
                ),
                ft.Container(expand=True),
            ],
            spacing=0,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

        right_panel = ft.Container(
            content=form_column,
            expand=3,
            bgcolor=BG_BASE,
            padding=ft.padding.symmetric(horizontal=48, vertical=40),
            border=ft.border.only(left=ft.BorderSide(1, BORDER)),
        )

        return ft.Container(
            content=ft.Row(
                controls=[left_panel, right_panel],
                spacing=0,
                expand=True,
            ),
            expand=True,
            bgcolor=ACCENT_LT,
            alignment=ft.Alignment(0, 0),
        )
