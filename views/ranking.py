import flet as ft
import asyncio
from datetime import date as _date
from components.ui import card
from utils import firebase, session, score_store

BG_BASE   = "#F0F9F8"
BG_CARD   = "#FFFFFF"
BG_CARD2  = "#E8F5F3"
ACCENT    = "#7AC3B8"
ACCENT_LT = "#EAF6F4"
DANGER    = "#FF5C5C"
WARNING   = "#FFB347"
PINK    = "#F3A2BE"
PINK_LT = "#FDEEF2"
LEMON    = "#A8C048"
LEMON_LT = "#F5FAD4"
TEXT_PRI  = "#1A1D23"
TEXT_SEC  = "#5A6375"
TEXT_MUT  = "#9DA8B7"
BORDER    = "#E2E6EC"
FONT      = "DOSSaemmul"

_AVATAR_COLORS = [
    "#7AC3B8", "#F3A2BE", "#FF5C5C", "#FFB347",
    "#34D399", "#60A5FA", "#F3A2BE", "#7AC3B8",
]


def _avatar_color(nickname: str) -> str:
    return _AVATAR_COLORS[sum(ord(c) for c in (nickname or "?")) % len(_AVATAR_COLORS)]


def _fmt_min(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"


class RankingView:
    def __init__(self, page: ft.Page):
        self.page   = page
        self.tab    = "friends"   # "friends" | "all"
        self.metric = "focus"     # "focus"   | "posture"

        # My card
        self.my_nick_ref        = ft.Ref()
        self.my_avatar_text_ref = ft.Ref()
        self.my_rank_ref        = ft.Ref()
        self.my_val_ref         = ft.Ref()
        self.my_unit_ref        = ft.Ref()

        # Tabs
        self.tab_all_ref          = ft.Ref()
        self.tab_all_text_ref     = ft.Ref()
        self.tab_friends_ref      = ft.Ref()
        self.tab_friends_text_ref = ft.Ref()

        # Metric toggle
        self.metric_focus_ref         = ft.Ref()
        self.metric_focus_text_ref    = ft.Ref()
        self.metric_posture_ref       = ft.Ref()
        self.metric_posture_text_ref  = ft.Ref()

        # All Users panel
        self.all_users_wrap_ref = ft.Ref()
        self.all_users_list_ref = ft.Ref()

        # Friends panel
        self.friends_wrap_ref = ft.Ref()
        self.requests_col_ref = ft.Ref()
        self.add_nick_ref     = ft.Ref()
        self.add_msg_ref      = ft.Ref()
        self.friends_list_ref = ft.Ref()

    def _user(self) -> dict:
        return session.get_user() or {}

    # ── 탭 전환 ───────────────────────────────────────────────────────
    def _switch_tab(self, tab: str, e=None):
        self.tab = tab
        for t, t_ref, tx_ref in [
            ("all",     self.tab_all_ref,     self.tab_all_text_ref),
            ("friends", self.tab_friends_ref, self.tab_friends_text_ref),
        ]:
            active = t == tab
            if t_ref.current:
                t_ref.current.bgcolor = ACCENT_LT if active else "transparent"
                t_ref.current.border  = ft.border.all(1, ACCENT if active else "transparent")
                t_ref.current.update()
            if tx_ref.current:
                tx_ref.current.color = ACCENT if active else TEXT_MUT
                tx_ref.current.update()

        if self.all_users_wrap_ref.current:
            self.all_users_wrap_ref.current.visible = (tab == "all")
            self.all_users_wrap_ref.current.update()
        if self.friends_wrap_ref.current:
            self.friends_wrap_ref.current.visible = (tab == "friends")
            self.friends_wrap_ref.current.update()

        if tab == "friends":
            self.page.run_task(self._load_friends)
        else:
            self.page.run_task(self._load_all_users)

    # ── 지표 전환 ─────────────────────────────────────────────────────
    def _switch_metric(self, metric: str, e=None):
        self.metric = metric
        _META = {
            "focus":   (self.metric_focus_ref,   self.metric_focus_text_ref,   LEMON,  LEMON_LT),
            "posture": (self.metric_posture_ref,  self.metric_posture_text_ref, PINK,  PINK_LT),
        }
        for m, (m_ref, mt_ref, color, bg) in _META.items():
            active = m == metric
            if m_ref.current:
                m_ref.current.bgcolor = bg if active else "transparent"
                m_ref.current.border  = ft.border.all(1, color if active else "transparent")
                m_ref.current.update()
            if mt_ref.current:
                mt_ref.current.color = color if active else TEXT_MUT
                mt_ref.current.update()

        if self.tab == "friends":
            self.page.run_task(self._load_friends)
        else:
            self.page.run_task(self._load_all_users)

    # ── refresh ──────────────────────────────────────────────────────
    def refresh(self):
        self.page.run_task(self._refresh_async)

    async def _refresh_async(self):
        user = self._user()
        nick = user.get("nickname", "?")
        if self.my_nick_ref.current:
            self.my_nick_ref.current.value = nick
            self.my_nick_ref.current.update()
        if self.my_avatar_text_ref.current:
            self.my_avatar_text_ref.current.value = nick[:1].upper() if nick else "?"
            self.my_avatar_text_ref.current.update()

        await self._sync_to_firebase(user)

        if self.tab == "friends":
            await self._load_friends()
        else:
            await self._load_all_users()

    async def _sync_to_firebase(self, user: dict):
        """로컬 오늘 집중·자세 데이터를 Firebase에 동기화."""
        uid      = user.get("uid", "")
        id_token = user.get("id_token", "")
        if not uid or not id_token:
            return
        today_str = _date.today().isoformat()

        today_min = score_store.get_today_focus_minutes()
        await asyncio.to_thread(
            firebase.update_today_focus, uid, id_token, today_min, today_str
        )

        posture = score_store.get_today_posture()
        if posture > 0:
            await asyncio.to_thread(
                firebase.update_today_posture, uid, id_token, posture, today_str
            )

    # ── 공통: 유저 목록에 display_val 채우기 ─────────────────────────
    def _apply_metric(self, users: list) -> tuple[str, callable]:
        """metric에 따라 각 user의 focus_min을 display 값으로 치환."""
        today_str = _date.today().isoformat()
        if self.metric == "focus":
            for u in users:
                u["focus_min"] = (u.get("today_focus_min", 0)
                                  if u.get("today_date") == today_str else 0)
            return "Focus", _fmt_min
        else:
            for u in users:
                u["focus_min"] = (u.get("today_posture_score", 0)
                                  if u.get("today_posture_date") == today_str else 0)
            return "Posture", lambda v: f"{v}pts"

    # ── 전체 유저 로드 ────────────────────────────────────────────────
    async def _load_all_users(self):
        user = self._user()
        if not user.get("id_token"):
            return

        self._set_list_loading(self.all_users_list_ref)

        users = await asyncio.to_thread(
            firebase.get_all_users_ranked, user["id_token"]
        )

        # 자신이 쿼리 결과에 없으면 직접 조회해서 추가
        my_uid = user.get("uid", "")
        if not any(u["uid"] == my_uid for u in users):
            my_direct = await asyncio.to_thread(
                firebase.get_user_stats, my_uid, user["id_token"]
            )
            if my_direct:
                users.append(my_direct)

        unit_label, fmt = self._apply_metric(users)
        users.sort(key=lambda u: u["focus_min"], reverse=True)

        my_idx = next((i for i, u in enumerate(users) if u["uid"] == my_uid), None)

        if my_idx is not None:
            my_data = users[my_idx]
            if self.my_rank_ref.current:
                self.my_rank_ref.current.value = f"#{my_idx + 1} today"
                self.my_rank_ref.current.update()
            if self.my_val_ref.current:
                self.my_val_ref.current.value = fmt(my_data["focus_min"])
                self.my_val_ref.current.update()
            if self.my_unit_ref.current:
                self.my_unit_ref.current.value = unit_label
                self.my_unit_ref.current.update()
        else:
            if self.my_rank_ref.current:
                self.my_rank_ref.current.value = "No record today"
                self.my_rank_ref.current.update()

        rows = [
            self._rank_row(i + 1, u, is_me=(u["uid"] == my_uid),
                           value_str=fmt(u["focus_min"]), unit_label=unit_label)
            for i, u in enumerate(users)
        ]
        if not rows:
            rows = [ft.Container(
                content=ft.Text("No data yet.", size=12, color=TEXT_MUT,
                                font_family=FONT, text_align=ft.TextAlign.CENTER),
                alignment=ft.Alignment(0, 0),
                padding=ft.padding.symmetric(vertical=24),
            )]

        if self.all_users_list_ref.current:
            self.all_users_list_ref.current.controls = rows
            self.all_users_list_ref.current.update()

    # ── 친구 목록 로드 ────────────────────────────────────────────────
    async def _load_friends(self):
        user = self._user()
        if not user.get("id_token"):
            return

        self._set_list_loading(self.friends_list_ref)
        my_uid = user.get("uid", "")

        requests_coro = asyncio.to_thread(
            firebase.get_incoming_requests, user["uid"], user["id_token"]
        )
        friends_coro = asyncio.to_thread(
            firebase.get_friends_with_stats, user["uid"], user["id_token"]
        )
        # 자신 데이터는 쿼리 의존 없이 직접 GET (orderBy 제외 문서 문제 우회)
        my_coro = asyncio.to_thread(
            firebase.get_user_stats, my_uid, user["id_token"]
        )
        requests, friends, my_data = await asyncio.gather(
            requests_coro, friends_coro, my_coro
        )

        # 나 자신 추가 (친구 목록에 중복이 없으면)
        combined = list(friends)
        if my_data and not any(f.get("uid") == my_uid for f in combined):
            combined.append(my_data)

        unit_label, fmt = self._apply_metric(combined)
        combined.sort(key=lambda x: x.get("focus_min", 0), reverse=True)

        my_idx = next((i for i, u in enumerate(combined) if u.get("uid") == my_uid), None)
        if my_data is not None:
            if self.my_rank_ref.current:
                rank_str = f"#{my_idx + 1} today" if my_idx is not None else "No record today"
                self.my_rank_ref.current.value = rank_str
                self.my_rank_ref.current.update()
            if self.my_val_ref.current:
                self.my_val_ref.current.value = fmt(my_data.get("focus_min", 0))
                self.my_val_ref.current.update()
            if self.my_unit_ref.current:
                self.my_unit_ref.current.value = unit_label
                self.my_unit_ref.current.update()
        else:
            if self.my_rank_ref.current:
                self.my_rank_ref.current.value = "No record today"
                self.my_rank_ref.current.update()

        # 친구 요청 섹션
        if self.requests_col_ref.current:
            req_controls = []
            if requests:
                req_controls.append(
                    ft.Text("Friend Requests", size=13, color=TEXT_PRI, font_family=FONT)
                )
                for req in requests:
                    req_controls.append(self._request_row(req))
                req_controls.append(ft.Divider(color=BORDER, height=1))
            self.requests_col_ref.current.controls = req_controls
            self.requests_col_ref.current.update()

        # 친구 랭킹 목록
        rows = [
            self._rank_row(i + 1, f, is_me=(f.get("uid") == my_uid),
                           value_str=fmt(f.get("focus_min", 0)), unit_label=unit_label)
            for i, f in enumerate(combined)
        ]
        if not rows:
            rows = [ft.Container(
                content=ft.Text(
                    "No friends yet.\nSearch by nickname above to send a friend request!",
                    size=12, color=TEXT_MUT, font_family=FONT,
                    text_align=ft.TextAlign.CENTER,
                ),
                alignment=ft.Alignment(0, 0),
                padding=ft.padding.symmetric(vertical=24),
            )]

        if self.friends_list_ref.current:
            self.friends_list_ref.current.controls = rows
            self.friends_list_ref.current.update()

    # ── 친구 추가 ─────────────────────────────────────────────────────
    def _send_friend_request(self, e=None):
        to_nick = (self.add_nick_ref.current.value or "").strip()
        if not to_nick:
            self._set_add_msg("Enter a nickname", ok=False)
            return
        user = self._user()

        async def _work():
            result = await asyncio.to_thread(
                firebase.send_friend_request,
                user["uid"], user.get("nickname", ""), user.get("username", ""),
                to_nick, user["id_token"],
            )
            if "error" in result:
                self._set_add_msg(result["error"], ok=False)
            else:
                self._set_add_msg(f"Request sent to {to_nick} ✓", ok=True)
                if self.add_nick_ref.current:
                    self.add_nick_ref.current.value = ""
                    self.add_nick_ref.current.update()
                await asyncio.sleep(3)
                self._set_add_msg("", ok=False)

        self.page.run_task(_work)

    def _accept_request(self, req: dict):
        user = self._user()

        async def _work():
            await asyncio.to_thread(
                firebase.accept_friend_request,
                user["uid"], user["id_token"],
                user.get("nickname", ""), user.get("username", ""),
                req["from_uid"], req["from_nickname"], req["from_username"],
            )
            await self._load_friends()

        self.page.run_task(_work)

    def _reject_request(self, req: dict):
        user = self._user()

        async def _work():
            await asyncio.to_thread(
                firebase.reject_friend_request,
                user["uid"], user["id_token"], req["from_uid"],
            )
            await self._load_friends()

        self.page.run_task(_work)

    # ── 공통 헬퍼 ─────────────────────────────────────────────────────
    def _set_add_msg(self, msg: str, ok: bool):
        if self.add_msg_ref.current:
            self.add_msg_ref.current.value = msg
            self.add_msg_ref.current.color = ACCENT if ok else DANGER
            self.add_msg_ref.current.update()

    def _set_list_loading(self, ref: ft.Ref):
        if ref.current:
            ref.current.controls = [
                ft.Row(
                    controls=[ft.ProgressRing(
                        width=20, height=20, stroke_width=2, color=ACCENT,
                    )],
                    alignment=ft.MainAxisAlignment.CENTER,
                )
            ]
            ref.current.update()

    # ── 랭킹 행 ──────────────────────────────────────────────────────
    def _rank_row(self, rank: int, user_data: dict, is_me: bool,
                  value_str: str = "—", unit_label: str = "Focus") -> ft.Container:
        nickname = user_data.get("nickname", "?")
        sessions = user_data.get("sessions", 0)
        color    = _avatar_color(nickname)
        medal    = ["🥇", "🥈", "🥉"][rank - 1] if rank <= 3 else f"#{rank}"
        val_color = LEMON if unit_label == "Focus" else PINK

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            medal, size=13 if rank <= 3 else 11,
                            color=val_color if is_me else TEXT_MUT,
                            font_family=FONT,
                        ),
                        width=38, alignment=ft.Alignment(0, 0),
                    ),
                    ft.Container(
                        content=ft.Text(
                            nickname[:1].upper(), size=12,
                            color="#FFFFFF", font_family=FONT,
                        ),
                        width=32, height=32, border_radius=16,
                        bgcolor=color, alignment=ft.Alignment(0, 0),
                    ),
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(nickname, size=13,
                                            color=val_color if is_me else TEXT_PRI,
                                            font_family=FONT),
                                    *(
                                        [ft.Container(
                                            content=ft.Text(
                                                "Me", size=9,
                                                color="#FFFFFF", font_family=FONT,
                                            ),
                                            bgcolor=val_color, border_radius=4,
                                            padding=ft.padding.only(
                                                left=5, top=1, right=5, bottom=1,
                                            ),
                                        )]
                                        if is_me else []
                                    ),
                                ],
                                spacing=6,
                            ),
                            ft.Text(
                                f"{sessions} sessions" if unit_label == "Focus" else "avg today",
                                size=11, color=TEXT_MUT, font_family=FONT,
                            ),
                        ],
                        spacing=2, expand=True,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                value_str, size=13,
                                color=val_color if is_me else TEXT_PRI,
                                font_family=FONT,
                            ),
                            ft.Text(unit_label, size=10, color=TEXT_MUT, font_family=FONT),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                        spacing=1,
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=(LEMON_LT if unit_label == "Focus" else PINK_LT) if is_me else BG_CARD,
            border_radius=12,
            padding=ft.padding.only(left=12, top=10, right=14, bottom=10),
            border=ft.border.all(1.5, val_color + "50" if is_me else BORDER),
            shadow=ft.BoxShadow(blur_radius=3, color="#00000008", offset=ft.Offset(0, 1)),
        )

    # ── 친구 요청 행 ──────────────────────────────────────────────────
    def _request_row(self, req: dict) -> ft.Container:
        nick  = req.get("from_nickname", "?")
        uname = req.get("from_username", "")
        color = _avatar_color(nick)

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(nick[:1].upper(), size=12,
                                        color="#FFFFFF", font_family=FONT),
                        width=32, height=32, border_radius=16,
                        bgcolor=color, alignment=ft.Alignment(0, 0),
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(nick, size=13, color=TEXT_PRI, font_family=FONT),
                            ft.Text(f"@{uname}", size=11, color=TEXT_MUT, font_family=FONT),
                        ],
                        spacing=2, expand=True,
                    ),
                    ft.Container(
                        content=ft.Text("Accept", size=11, color="#FFFFFF", font_family=FONT),
                        bgcolor=ACCENT, border_radius=8,
                        padding=ft.padding.symmetric(horizontal=14, vertical=7),
                        on_click=lambda _, r=req: self._accept_request(r),
                    ),
                    ft.Container(
                        content=ft.Text("Reject", size=11, color=DANGER, font_family=FONT),
                        border=ft.border.all(1.5, DANGER), border_radius=8,
                        padding=ft.padding.symmetric(horizontal=14, vertical=7),
                        on_click=lambda _, r=req: self._reject_request(r),
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=BG_CARD,
            border_radius=12,
            padding=ft.padding.only(left=12, top=10, right=12, bottom=10),
            border=ft.border.all(1, BORDER),
        )

    # ── 빌드 ──────────────────────────────────────────────────────────
    def build(self) -> ft.Container:
        user     = self._user()
        nickname = user.get("nickname", "?")
        color    = _avatar_color(nickname)

        # ── My card ──────────────────────────────────────────────────
        my_card = card(
            ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            ref=self.my_avatar_text_ref,
                            value=nickname[:1].upper() if nickname else "?",
                            size=20, color="#FFFFFF", font_family=FONT,
                        ),
                        width=52, height=52, border_radius=26,
                        bgcolor=color, alignment=ft.Alignment(0, 0),
                        shadow=ft.BoxShadow(
                            blur_radius=10, color=color + "55", offset=ft.Offset(0, 3),
                        ),
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(ref=self.my_nick_ref, value=nickname,
                                    size=15, color=TEXT_PRI, font_family=FONT),
                            ft.Text(ref=self.my_rank_ref, value="Loading...",
                                    size=13, color=ACCENT, font_family=FONT),
                        ],
                        spacing=4, expand=True,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(ref=self.my_val_ref, value="—",
                                    size=20, color=ACCENT, font_family=FONT),
                            ft.Text(ref=self.my_unit_ref, value="Today's Focus",
                                    size=11, color=TEXT_MUT, font_family=FONT),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                        spacing=2,
                    ),
                ],
                spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.only(left=20, top=14, right=20, bottom=14),
        )

        # ── Metric toggle ─────────────────────────────────────────────
        def _metric_btn(m, label, m_ref, mt_ref, color, bg):
            active = m == self.metric
            return ft.Container(
                ref=m_ref,
                content=ft.Text(
                    ref=mt_ref, value=label, size=13, font_family=FONT,
                    color=color if active else TEXT_MUT,
                    text_align=ft.TextAlign.CENTER,
                ),
                bgcolor=bg if active else "transparent",
                border_radius=8,
                border=ft.border.all(1, color if active else "transparent"),
                padding=ft.padding.symmetric(horizontal=20, vertical=8),
                on_click=lambda _, metric=m: self._switch_metric(metric),
                expand=True,
                alignment=ft.Alignment(0, 0),
            )

        metric_bar = ft.Container(
            content=ft.Row(
                controls=[
                    _metric_btn("focus",   "Focus",
                                self.metric_focus_ref,   self.metric_focus_text_ref,
                                LEMON, LEMON_LT),
                    _metric_btn("posture", "Posture",
                                self.metric_posture_ref, self.metric_posture_text_ref,
                                PINK, PINK_LT),
                ],
                spacing=4,
            ),
            bgcolor=BG_CARD2,
            border_radius=10,
            border=ft.border.all(1, BORDER),
            padding=4,
        )

        # ── Tab bar ──────────────────────────────────────────────────
        def _tab_btn(t, label, t_ref, tx_ref):
            active = t == self.tab
            return ft.Container(
                ref=t_ref,
                content=ft.Text(
                    ref=tx_ref, value=label, size=13, font_family=FONT,
                    color=ACCENT if active else TEXT_MUT,
                    text_align=ft.TextAlign.CENTER,
                ),
                bgcolor=ACCENT_LT if active else "transparent",
                border_radius=8,
                border=ft.border.all(1, ACCENT if active else "transparent"),
                padding=ft.padding.symmetric(horizontal=20, vertical=8),
                on_click=lambda _, tab=t: self._switch_tab(tab),
                expand=True,
                alignment=ft.Alignment(0, 0),
            )

        tab_bar = ft.Container(
            content=ft.Row(
                controls=[
                    _tab_btn("friends", "Friends",
                             self.tab_friends_ref, self.tab_friends_text_ref),
                    _tab_btn("all",     "All Users",
                             self.tab_all_ref,     self.tab_all_text_ref),
                ],
                spacing=4,
            ),
            bgcolor=BG_CARD2,
            border_radius=10,
            border=ft.border.all(1, BORDER),
            padding=4,
        )

        # ── All Users panel ──────────────────────────────────────────
        all_users_panel = ft.Container(
            ref=self.all_users_wrap_ref,
            content=ft.Column(
                ref=self.all_users_list_ref,
                controls=[
                    ft.Row(
                        controls=[ft.ProgressRing(
                            width=20, height=20, stroke_width=2, color=ACCENT,
                        )],
                        alignment=ft.MainAxisAlignment.CENTER,
                    )
                ],
                spacing=8,
            ),
            visible=(self.tab == "all"),
        )

        # ── Friends panel ────────────────────────────────────────────
        friends_panel = ft.Container(
            ref=self.friends_wrap_ref,
            content=ft.Column(
                controls=[
                    ft.Column(ref=self.requests_col_ref, controls=[], spacing=8),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("Add Friend", size=13, color=TEXT_PRI, font_family=FONT),
                                ft.Container(height=6),
                                ft.Row(
                                    controls=[
                                        ft.Container(
                                            content=ft.TextField(
                                                ref=self.add_nick_ref,
                                                hint_text="Search by nickname",
                                                hint_style=ft.TextStyle(
                                                    color=TEXT_MUT, font_family=FONT, size=13,
                                                ),
                                                text_style=ft.TextStyle(
                                                    color=TEXT_PRI, font_family=FONT, size=13,
                                                ),
                                                border_color=BORDER,
                                                focused_border_color=ACCENT,
                                                border_radius=10,
                                                content_padding=ft.padding.symmetric(
                                                    horizontal=14, vertical=12,
                                                ),
                                                prefix_icon=ft.Icons.PERSON_SEARCH,
                                                bgcolor=BG_BASE,
                                                cursor_color=ACCENT,
                                                on_submit=self._send_friend_request,
                                            ),
                                            expand=True,
                                        ),
                                        ft.Container(width=8),
                                        ft.Container(
                                            content=ft.Text(
                                                "Send", size=12, color="#FFFFFF",
                                                font_family=FONT,
                                                text_align=ft.TextAlign.CENTER,
                                            ),
                                            bgcolor=ACCENT,
                                            border_radius=10,
                                            padding=ft.padding.symmetric(
                                                horizontal=16, vertical=15,
                                            ),
                                            on_click=self._send_friend_request,
                                        ),
                                    ],
                                    vertical_alignment=ft.CrossAxisAlignment.START,
                                ),
                                ft.Text(
                                    ref=self.add_msg_ref,
                                    value="", size=11, font_family=FONT,
                                ),
                            ],
                            spacing=4,
                        ),
                        bgcolor=BG_CARD,
                        border_radius=14,
                        padding=16,
                        border=ft.border.all(1, BORDER),
                    ),
                    ft.Container(height=4),
                    ft.Column(
                        ref=self.friends_list_ref,
                        controls=[
                            ft.Row(
                                controls=[ft.ProgressRing(
                                    width=20, height=20, stroke_width=2, color=ACCENT,
                                )],
                                alignment=ft.MainAxisAlignment.CENTER,
                            )
                        ],
                        spacing=8,
                    ),
                ],
                spacing=10,
            ),
            visible=(self.tab == "friends"),
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Ranking", size=26, color=TEXT_PRI, font_family=FONT),
                    ft.Text("Today's leaderboard",
                            size=13, color=TEXT_MUT, font_family=FONT),
                    ft.Container(height=10),
                    my_card,
                    ft.Container(height=12),
                    metric_bar,
                    ft.Container(height=8),
                    tab_bar,
                    ft.Container(height=12),
                    all_users_panel,
                    friends_panel,
                ],
                scroll=ft.ScrollMode.AUTO,
                spacing=0,
                expand=True,
            ),
            expand=True,
            alignment=ft.Alignment(-1, -1),
            padding=ft.padding.only(left=28, top=18, right=28, bottom=18),
            bgcolor=BG_BASE,
        )
