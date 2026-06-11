import flet as ft
import asyncio
from components.ui import card, accent_btn, ghost_btn, mascot_widget
from utils import firebase, session
from utils import lang as lang_store

BG_BASE   = "#F0F9F8"
BG_CARD   = "#F4F6F8"
BG_CARD2  = "#EAECEF"
ACCENT    = "#7AC3B8"
ACCENT_LT = "#D6F5EF"
DANGER    = "#FF5C5C"
WARNING   = "#FFB347"
TEXT_PRI  = "#1A1D23"
TEXT_SEC  = "#5A6375"
TEXT_MUT  = "#9DA8B7"
BORDER    = "#E2E6EC"
FONT      = "DOSSaemmul"


class ProfileView:
    def __init__(self, page: ft.Page, on_logout):
        self.page      = page
        self.on_logout = on_logout
        self.nickname_verified = False

        # nickname change refs
        self.new_nick_ref       = ft.Ref()
        self.nick_check_msg_ref = ft.Ref()
        self.nick_save_btn_ref  = ft.Ref()
        self.nick_status_ref    = ft.Ref()

        # password change refs
        self.curr_pw_ref    = ft.Ref()
        self.new_pw_ref     = ft.Ref()
        self.confirm_pw_ref = ft.Ref()
        self.pw_status_ref  = ft.Ref()

        # profile card refs (실시간 업데이트용)
        self.profile_nick_ref   = ft.Ref()
        self.profile_avatar_ref = ft.Ref()
        self.current_nick_ref   = ft.Ref()  # "Current: xxx" 텍스트

    def _user(self) -> dict:
        return session.get_user() or {}

    # ── 닉네임 중복 확인 ──────────────────────────────────────────────
    def _check_nickname(self, e=None):
        nickname = (self.new_nick_ref.current.value or "").strip()
        if not nickname:
            self._set_msg(self.nick_check_msg_ref, lang_store.t("err_enter_nick"), ok=False); return
        if nickname == self._user().get("nickname", ""):
            self._set_msg(self.nick_check_msg_ref, lang_store.t("err_same_nick"), ok=False); return

        async def _work():
            try:
                exists = await asyncio.to_thread(firebase.nickname_exists, nickname)
                if exists:
                    self.nickname_verified = False
                    self._set_msg(self.nick_check_msg_ref, lang_store.t("err_nick_taken"), ok=False)
                else:
                    self.nickname_verified = True
                    self._set_msg(self.nick_check_msg_ref, lang_store.t("ok_nick_available"), ok=True)
            except Exception:
                self._set_msg(self.nick_check_msg_ref, lang_store.t("no_record_today"), ok=False)

        self.page.run_task(_work)

    # ── 공통 메시지 헬퍼 ──────────────────────────────────────────────
    def _set_msg(self, ref: ft.Ref, msg: str, ok: bool):
        """인라인 메시지 텍스트 업데이트 (visible 토글 없이 값만 변경)"""
        if ref.current:
            ref.current.value = msg
            ref.current.color = ACCENT if ok else DANGER
            ref.current.update()

    # ── 프로필 카드 실시간 업데이트 ───────────────────────────────────
    def _update_profile_card(self, new_nick: str):
        if self.profile_avatar_ref.current:
            self.profile_avatar_ref.current.value = new_nick[:1].upper() if new_nick else "?"
            self.profile_avatar_ref.current.update()
        if self.profile_nick_ref.current:
            self.profile_nick_ref.current.value = new_nick
            self.profile_nick_ref.current.update()
        if self.current_nick_ref.current:
            self.current_nick_ref.current.value = lang_store.t("current_nick_fmt").format(nick=new_nick)
            self.current_nick_ref.current.update()

    # ── 닉네임 저장 ───────────────────────────────────────────────────
    def _save_nickname(self, e=None):
        new_nick = (self.new_nick_ref.current.value or "").strip()
        if not new_nick:
            self._set_msg(self.nick_check_msg_ref, lang_store.t("err_enter_nick"), ok=False); return
        if not self.nickname_verified:
            self._set_msg(self.nick_check_msg_ref, lang_store.t("err_check_nick"), ok=False); return

        user = self._user()

        async def _work():
            result = await asyncio.to_thread(
                lambda: firebase.change_nickname(
                    user["uid"], user["id_token"],
                    user.get("nickname", ""), new_nick,
                )
            )
            if "error" in result:
                self._set_msg(self.nick_status_ref, result["error"], ok=False)
            else:
                user["nickname"] = new_nick
                session.set_user(user)
                session.save(user)
                self.nickname_verified = False
                self._update_profile_card(new_nick)
                if self.new_nick_ref.current:
                    self.new_nick_ref.current.value = ""
                    self.new_nick_ref.current.update()
                # check 메시지와 같은 위치에 성공 메시지 표시 후 3초 뒤 제거
                self._set_msg(self.nick_check_msg_ref, lang_store.t("ok_nick_updated"), ok=True)
                await asyncio.sleep(3)
                self._set_msg(self.nick_check_msg_ref, "", ok=False)

        self.page.run_task(_work)

    # ── 비밀번호 변경 ─────────────────────────────────────────────────
    def _save_password(self, e=None):
        curr_pw    = self.curr_pw_ref.current.value    or ""
        new_pw     = self.new_pw_ref.current.value     or ""
        confirm_pw = self.confirm_pw_ref.current.value or ""

        if not curr_pw:
            self._set_msg(self.pw_status_ref, lang_store.t("err_enter_curr_pw"), ok=False); return
        if not new_pw:
            self._set_msg(self.pw_status_ref, lang_store.t("err_enter_new_pw"), ok=False); return
        if len(new_pw) < 6:
            self._set_msg(self.pw_status_ref, lang_store.t("err_pw_too_short"), ok=False); return
        if new_pw != confirm_pw:
            self._set_msg(self.pw_status_ref, lang_store.t("err_pw_no_match"), ok=False); return
        if curr_pw == new_pw:
            self._set_msg(self.pw_status_ref, lang_store.t("err_pw_same"), ok=False); return

        user = self._user()

        async def _work():
            verify = await asyncio.to_thread(firebase.sign_in, user["username"], curr_pw)
            if "error" in verify:
                self._set_msg(self.pw_status_ref, lang_store.t("err_curr_pw_wrong"), ok=False)
                return

            # verify["id_token"]은 방금 sign_in으로 받은 최신 토큰 — 세션 토큰이 만료됐어도 동작
            result = await asyncio.to_thread(firebase.change_password, verify["id_token"], new_pw)
            if "error" in result:
                self._set_msg(self.pw_status_ref, result["error"], ok=False)
            else:
                user["id_token"]      = result["id_token"]
                user["refresh_token"] = result["refresh_token"]
                session.set_user(user)
                session.save(user)
                for ref in [self.curr_pw_ref, self.new_pw_ref, self.confirm_pw_ref]:
                    if ref.current:
                        ref.current.value = ""
                        ref.current.update()
                # 성공 메시지 3초 후 자동 제거
                self._set_msg(self.pw_status_ref, lang_store.t("ok_pw_updated"), ok=True)
                await asyncio.sleep(3)
                self._set_msg(self.pw_status_ref, "", ok=False)

        self.page.run_task(_work)

    # ── 로그아웃 ──────────────────────────────────────────────────────
    def _logout(self, e=None):
        session.clear()
        session.set_user(None)
        self.on_logout()

    # ── 필드 헬퍼 ─────────────────────────────────────────────────────
    def _field(self, ref, hint: str, icon, password=False):
        return ft.TextField(
            ref=ref,
            hint_text=hint,
            hint_style=ft.TextStyle(color=TEXT_MUT, font_family=FONT, size=15),
            text_style=ft.TextStyle(color=TEXT_PRI, font_family=FONT, size=15),
            border_color=BORDER,
            focused_border_color=ACCENT,
            border_radius=10,
            content_padding=ft.padding.symmetric(horizontal=14, vertical=12),
            password=password,
            can_reveal_password=password,
            prefix_icon=icon,
            bgcolor=BG_BASE,
            cursor_color=ACCENT,
        )

    # ── 빌드 ──────────────────────────────────────────────────────────
    def build(self) -> ft.Container:
        user = self._user()
        username = user.get("username", "—")
        nickname = user.get("nickname", "—")

        # ── 프로필 카드 ─────────────────────────────────────────────
        profile_card = card(
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(
                                    ref=self.profile_avatar_ref,
                                    value=nickname[:1].upper() if nickname else "?",
                                    size=24, color="#F0F9F8", font_family=FONT,
                                ),
                                width=56, height=56, border_radius=28,
                                bgcolor=ACCENT, alignment=ft.Alignment(0, 0),
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(
                                        ref=self.profile_nick_ref,
                                        value=nickname,
                                        size=18, color=TEXT_PRI, font_family=FONT,
                                    ),
                                    ft.Text(f"@{username}", size=14,
                                            color=TEXT_MUT, font_family=FONT),
                                ],
                                spacing=2,
                            ),
                        ],
                        spacing=16,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
            ),
            padding=20,
        )

        # ── 닉네임 변경 카드 ────────────────────────────────────────
        nickname_card = card(
            ft.Column(
                controls=[
                    ft.Text(lang_store.t("change_nickname"), size=16, color=TEXT_PRI, font_family=FONT),
                    ft.Container(height=4),
                    ft.Text(
                        ref=self.current_nick_ref,
                        value=lang_store.t("current_nick_fmt").format(nick=nickname),
                        size=14, color=TEXT_MUT, font_family=FONT,
                    ),
                    ft.Container(height=12),
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=self._field(self.new_nick_ref, lang_store.t("new_nickname_hint"),
                                                    ft.Icons.BADGE_OUTLINED),
                                expand=True,
                            ),
                            ft.Container(width=8),
                            ft.Container(
                                content=ft.Text(lang_store.t("check"), size=14, color="#F0F9F8",
                                                font_family=FONT,
                                                text_align=ft.TextAlign.CENTER),
                                bgcolor=ACCENT, border_radius=10,
                                padding=ft.padding.symmetric(horizontal=14, vertical=15),
                                on_click=self._check_nickname,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    ft.Text(ref=self.nick_check_msg_ref, value="", size=13, font_family=FONT),
                    ft.Container(height=8),
                    ft.Container(
                        content=ft.Text(lang_store.t("save_nickname_btn"), size=15, color="#F0F9F8",
                                        font_family=FONT, text_align=ft.TextAlign.CENTER),
                        bgcolor=ACCENT, border_radius=10,
                        padding=ft.padding.symmetric(horizontal=20, vertical=12),
                        on_click=self._save_nickname,
                        alignment=ft.Alignment(0, 0),
                        shadow=ft.BoxShadow(blur_radius=10, color=ACCENT + "55",
                                            offset=ft.Offset(0, 3)),
                    ),
                ],
                spacing=4,
            ),
            padding=20,
        )

        # ── 비밀번호 변경 카드 ──────────────────────────────────────
        password_card = card(
            ft.Column(
                controls=[
                    ft.Text(lang_store.t("change_password"), size=16, color=TEXT_PRI, font_family=FONT),
                    ft.Container(height=12),
                    self._field(self.curr_pw_ref, lang_store.t("curr_pw_hint"),
                                ft.Icons.LOCK_OUTLINE, password=True),
                    ft.Container(height=8),
                    self._field(self.new_pw_ref, lang_store.t("new_pw_hint"),
                                ft.Icons.LOCK_OPEN_OUTLINED, password=True),
                    ft.Container(height=8),
                    self._field(self.confirm_pw_ref, lang_store.t("confirm_pw_hint"),
                                ft.Icons.LOCK_RESET, password=True),
                    ft.Text(ref=self.pw_status_ref, value="", size=13, font_family=FONT),
                    ft.Container(height=8),
                    ft.Container(
                        content=ft.Text(lang_store.t("save_password_btn"), size=15, color="#F0F9F8",
                                        font_family=FONT, text_align=ft.TextAlign.CENTER),
                        bgcolor=ACCENT, border_radius=10,
                        padding=ft.padding.symmetric(horizontal=20, vertical=12),
                        on_click=self._save_password,
                        alignment=ft.Alignment(0, 0),
                        shadow=ft.BoxShadow(blur_radius=10, color=ACCENT + "55",
                                            offset=ft.Offset(0, 3)),
                    ),
                ],
                spacing=4,
            ),
            padding=20,
        )

        # ── 로그아웃 버튼 ────────────────────────────────────────────
        logout_btn = ft.Container(
            content=ft.Text(lang_store.t("log_out"), size=15, color=DANGER,
                            font_family=FONT, text_align=ft.TextAlign.CENTER),
            border=ft.border.all(1.5, DANGER),
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=20, vertical=12),
            alignment=ft.Alignment(0, 0),
            on_click=self._logout,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(lang_store.t("profile_title"), size=26, color=TEXT_PRI, font_family=FONT),
                    ft.Text(lang_store.t("profile_sub"),
                            size=15, color=TEXT_MUT, font_family=FONT),
                    ft.Container(height=12),
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    profile_card,
                                    ft.Container(height=10),
                                    logout_btn,
                                ],
                                width=280,
                                spacing=0,
                            ),
                            ft.Container(width=16),
                            ft.Column(
                                controls=[
                                    nickname_card,
                                    ft.Container(height=10),
                                    password_card,
                                ],
                                expand=True,
                                spacing=0,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        expand=True,
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            expand=True,
            padding=ft.padding.only(left=28, top=18, right=28, bottom=18),
            bgcolor=BG_BASE,
        )
