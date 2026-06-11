import flet as ft
import asyncio
from components.ui import card, accent_btn, ghost_btn, mascot_widget
from datetime import datetime
from utils import firebase, session, todo_store, score_store
from utils.alert_manager import is_monitoring
from utils import lang as lang_store

BG_BASE   = "#F0F9F8"
BG_CARD   = "#F4F6F8"
ACCENT    = "#7AC3B8"
ACCENT_LT = "#D6F5EF"
DANGER    = "#FF5C5C"
WARNING   = "#FFB347"
PINK = "#F3A2BE"
TEXT_PRI  = "#1A1D23"
TEXT_SEC  = "#5A6375"
TEXT_MUT  = "#9DA8B7"
BORDER    = "#E2E6EC"
FONT      = "DOSSaemmul"

ROW1_H = 240
ROW2_H = 260

POMO_LABELS = {"focus": "focus_session", "rest": "break_session"}  # lang keys
POMO_COLORS = {"focus": ACCENT,          "rest": PINK}


def _fmt_min(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"

_AVATAR_COLORS = [
    "#B9E6E0", "#9B8FFF", "#FF5C5C", "#FFB347",
    "#34D399", "#60A5FA", "#F472B6", "#A78BFA",
]

def _avatar_color(nickname: str) -> str:
    return _AVATAR_COLORS[sum(ord(c) for c in (nickname or "?")) % len(_AVATAR_COLORS)]


class DashboardView:
    def __init__(self, page: ft.Page, navigate):
        self.page = page
        self.navigate = navigate
        self.pomo_time_ref      = ft.Ref()
        self.pomo_status_ref    = ft.Ref()
        self.pomo_ring_ref      = ft.Ref()
        self.pomo_play_icon_ref = ft.Ref()
        self.pomo_play_btn_ref  = ft.Ref()
        self.pomo_start_stop_cb = None
        self.pomo_reset_cb      = None
        self.pomo_skip_cb       = None
        self.dash_rank_col_ref         = ft.Ref()
        self.dash_rank_posture_col_ref = ft.Ref()
        self.live_status_ref           = ft.Ref()
        self.live_dot_ref           = ft.Ref()
        self.live_text_ref          = ft.Ref()
        self.todo_col_ref           = ft.Ref()
        self.todo_count_ref         = ft.Ref()
        # 점수 관련
        self.dash_posture_ring_ref  = ft.Ref()
        self.dash_posture_score_ref = ft.Ref()
        self.dash_posture_label_ref = ft.Ref()
        self.dash_focus_bars_ref    = ft.Ref()
        self.dash_posture_bars_ref  = ft.Ref()
        self.dash_focus_avg_ref     = ft.Ref()
        self.dash_posture_avg_ref   = ft.Ref()
        self.pomo_cycles_ref        = ft.Ref()

    def update_pomodoro(self, remaining: int, total: int, mode: str, running: bool):
        mins, secs = remaining // 60, remaining % 60
        time_str = f"{mins:02d}:{secs:02d}"
        color = POMO_COLORS.get(mode, ACCENT)
        if running:
            status = lang_store.t(POMO_LABELS.get(mode, mode))
        elif remaining == 0:
            status = lang_store.t("session_complete")
        elif remaining < total:
            status = lang_store.t("paused")
        else:
            status = lang_store.t("session_ready")
        try:
            if self.pomo_time_ref.current:
                self.pomo_time_ref.current.value = time_str
                self.pomo_time_ref.current.color = color
                self.pomo_time_ref.current.update()
            if self.pomo_status_ref.current:
                self.pomo_status_ref.current.value = status
                self.pomo_status_ref.current.update()
            if self.pomo_ring_ref.current:
                self.pomo_ring_ref.current.value = remaining / total if total else 0
                self.pomo_ring_ref.current.color = color
                self.pomo_ring_ref.current.update()
            if self.pomo_play_icon_ref.current:
                self.pomo_play_icon_ref.current.icon = (
                    ft.Icons.PAUSE if running else ft.Icons.PLAY_ARROW
                )
                self.pomo_play_icon_ref.current.update()
            if self.pomo_play_btn_ref.current:
                self.pomo_play_btn_ref.current.bgcolor = color
                self.pomo_play_btn_ref.current.update()
        except Exception:
            pass

    def update_sessions(self, done: int, goal: int):
        """뽀모도로 세션 완료 수/목표 수 표시 갱신."""
        try:
            if self.pomo_cycles_ref.current:
                color = (DANGER if done == 0
                         else ACCENT if done > goal / 2
                         else WARNING)
                self.pomo_cycles_ref.current.value = f"{done} / {goal}"
                self.pomo_cycles_ref.current.color = color
                self.pomo_cycles_ref.current.update()
        except Exception:
            pass

    # ── 랭킹 카드 실데이터 로드 ─────────────────────────────────────
    def refresh(self):
        self._update_live_badge()
        self._refresh_todo()
        self._refresh_scores()
        self.page.run_task(self._load_ranking)
        todo_store.add_listener(self._refresh_todo)
        score_store.add_listener(self._refresh_scores)

    def _refresh_todo(self):
        tasks = todo_store.get_tasks()
        total = len(tasks)

        # 미완료 우선, 최대 4개 미리보기
        order = {"High": 0, "Medium": 1, "Low": 2}
        sorted_tasks = sorted(tasks,
                              key=lambda t: (t["done"], order.get(t["priority"], 1)))
        preview = sorted_tasks[:4]

        def _make_task_row(task):
            done = task["done"]
            def toggle(_):
                todo_store.toggle_task(task)
            return ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(ft.Icons.DONE, size=13,
                                        color="#F0F9F8" if done else "transparent"),
                        width=18, height=18, border_radius=5,
                        border=ft.border.all(1.5, ACCENT if done else BORDER),
                        bgcolor=ACCENT if done else "transparent",
                        alignment=ft.Alignment(0, 0),
                        on_click=toggle,
                    ),
                    ft.Text(
                        task["title"], size=15,
                        color=TEXT_MUT if done else TEXT_PRI,
                        font_family=FONT, expand=True,
                        spans=[ft.TextSpan(style=ft.TextStyle(
                            decoration=ft.TextDecoration.LINE_THROUGH)
                        )] if done else [],
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )

        rows = [_make_task_row(t) for t in preview]

        if not rows:
            rows = [ft.Text(lang_store.t("no_tasks"), size=14, color=TEXT_MUT, font_family=FONT)]

        if self.todo_col_ref.current:
            self.todo_col_ref.current.controls = rows
            self.todo_col_ref.current.update()

        if self.todo_count_ref.current:
            label = lang_store.t("items_fmt_plural" if total != 1 else "items_fmt").format(n=total)
            self.todo_count_ref.current.value = label
            self.todo_count_ref.current.update()

    def _refresh_scores(self):
        from datetime import date as _date
        today_idx    = _date.today().weekday()
        days         = [lang_store.t("mon"), lang_store.t("tue"), lang_store.t("wed"), lang_store.t("thu"), lang_store.t("fri"), lang_store.t("sat"), lang_store.t("sun")]
        MAX_H, MIN_H = 44, 12

        # ── 오늘 자세 점수 ───────────────────────────────────────────
        p_score = score_store.get_today_posture()
        p_color = ACCENT if p_score >= 70 else (WARNING if p_score >= 50 else DANGER)

        if self.dash_posture_ring_ref.current:
            self.dash_posture_ring_ref.current.value = p_score / 100
            self.dash_posture_ring_ref.current.color = p_color
            self.dash_posture_ring_ref.current.update()
        if self.dash_posture_score_ref.current:
            self.dash_posture_score_ref.current.value = str(p_score) if p_score else "--"
            self.dash_posture_score_ref.current.color = p_color
            self.dash_posture_score_ref.current.update()
        if self.dash_posture_label_ref.current:
            lbl = (lang_store.t("posture_good") if p_score >= 70
                   else lang_store.t("posture_fair") if p_score >= 50
                   else lang_store.t("posture_poor") if p_score > 0
                   else lang_store.t("not_measured"))
            self.dash_posture_label_ref.current.value = lbl
            self.dash_posture_label_ref.current.color = p_color
            self.dash_posture_label_ref.current.update()

        # ── 주간 바 차트 ─────────────────────────────────────────────
        focus_vals   = score_store.get_week_focus()
        posture_vals = score_store.get_week_posture()

        def make_bars(vals, color_fn):
            bars = []
            for i, (d, val) in enumerate(zip(days, vals)):
                is_today = i == today_idx
                h = 4 if val == 0 else int(MIN_H + (val / 100) * (MAX_H - MIN_H))
                c = color_fn(val, is_today)
                bars.append(
                    ft.Column(
                        controls=[
                            ft.Container(
                                width=22, height=MAX_H,
                                content=ft.Column(
                                    controls=[
                                        ft.Container(expand=True),
                                        ft.Container(
                                            width=22, height=h,
                                            bgcolor=c if is_today else (c + "88" if val > 0 else BORDER),
                                            border_radius=4,
                                        ),
                                    ],
                                    spacing=0,
                                ),
                            ),
                            ft.Text(d, size=12,
                                    color=c if is_today else TEXT_MUT,
                                    font_family=FONT,
                                    text_align=ft.TextAlign.CENTER),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=16,
                    )
                )
            return bars

        if self.dash_focus_bars_ref.current:
            self.dash_focus_bars_ref.current.controls = make_bars(
                focus_vals,
                lambda v, today: ACCENT,
            )
            self.dash_focus_bars_ref.current.update()

        if self.dash_posture_bars_ref.current:
            self.dash_posture_bars_ref.current.controls = make_bars(
                posture_vals,
                lambda v, today: ACCENT if v >= 70 else (WARNING if v >= 50 else DANGER),
            )
            self.dash_posture_bars_ref.current.update()

        # ── 평균 라벨 ────────────────────────────────────────────────
        focus_avg   = score_store.get_weekly_focus_avg_minutes()
        posture_avg = score_store.get_weekly_posture_avg()

        if self.dash_focus_avg_ref.current:
            self.dash_focus_avg_ref.current.value = (
                lang_store.t("avg_focus_fmt").format(n=focus_avg) if focus_avg else lang_store.t("no_data")
            )
            self.dash_focus_avg_ref.current.update()
        if self.dash_posture_avg_ref.current:
            self.dash_posture_avg_ref.current.value = (
                lang_store.t("avg_posture_fmt").format(n=posture_avg) if posture_avg else lang_store.t("no_data")
            )
            self.dash_posture_avg_ref.current.update()

        try:
            self.page.update()
        except Exception:
            pass

    def _update_live_badge(self):
        on = is_monitoring()
        color  = ACCENT    if on else DANGER
        bg     = ACCENT_LT if on else "#FFF0F0"
        border = None
        label  = lang_store.t("live_on") if on else lang_store.t("live_off")
        if self.live_dot_ref.current:
            self.live_dot_ref.current.bgcolor = color
            self.live_dot_ref.current.update()
        if self.live_text_ref.current:
            self.live_text_ref.current.value = label
            self.live_text_ref.current.color = color
            self.live_text_ref.current.update()
        if self.live_status_ref.current:
            self.live_status_ref.current.bgcolor = bg
            self.live_status_ref.current.border  = None
            self.live_status_ref.current.update()

    # ── 이웃 슬라이스: 리스트가 길면 나 ± 1 범위만 반환 ────────────────
    @staticmethod
    def _neighbor_slice(ranked: list, my_uid: str, max_n: int = 3) -> list:
        if len(ranked) <= max_n:
            return ranked
        my_i = next((i for i, u in enumerate(ranked) if u.get("uid") == my_uid), -1)
        if my_i == -1:
            return ranked[:max_n]
        if my_i == 0:                        # 1위: 나 + 아래 2명
            end = min(3, len(ranked))
            return ranked[0:end]
        if my_i >= len(ranked) - 1:          # 꼴찌: 위 2명 + 나
            start = max(0, len(ranked) - 3)
            return ranked[start:]
        return ranked[my_i - 1: my_i + 2]   # 일반: 위 1 + 나 + 아래 1

    async def _load_ranking(self):
        user = session.get_user() or {}
        if not user.get("id_token"):
            return

        _loading = ft.Row(
            controls=[ft.ProgressRing(width=16, height=16, stroke_width=2, color=ACCENT)],
            alignment=ft.MainAxisAlignment.CENTER,
        )
        if self.dash_rank_col_ref.current:
            self.dash_rank_col_ref.current.controls = [_loading]
            self.dash_rank_col_ref.current.update()
        if self.dash_rank_posture_col_ref.current:
            self.dash_rank_posture_col_ref.current.controls = []
            self.dash_rank_posture_col_ref.current.update()

        my_uid = user.get("uid", "")
        friends_coro = asyncio.to_thread(
            firebase.get_friends_with_stats, user["uid"], user["id_token"]
        )
        my_coro = asyncio.to_thread(
            firebase.get_user_stats, my_uid, user["id_token"]
        )
        friends, my_data = await asyncio.gather(friends_coro, my_coro)

        from datetime import date as _date
        today_str = _date.today().isoformat()

        combined = list(friends)
        if my_data and not any(f.get("uid") == my_uid for f in combined):
            combined.append(my_data)

        # ── 집중 시간 랭킹 ────────────────────────────────────────────
        for u in combined:
            u["_focus_val"] = (
                u.get("today_focus_min", 0)
                if u.get("today_date") == today_str else 0
            )
        focus_sorted = sorted(combined, key=lambda x: x["_focus_val"], reverse=True)
        focus_slice  = self._neighbor_slice(focus_sorted, my_uid)

        medals = ["🥇", "🥈", "🥉"]
        focus_rows = []
        for u in focus_slice:
            rank = focus_sorted.index(u)
            is_me = u["uid"] == my_uid
            medal = medals[rank] if rank < 3 else f"#{rank + 1}"
            focus_rows.append(self._dash_rank_row(
                medal, u["nickname"],
                _fmt_min(u["_focus_val"]),
                _avatar_color(u["nickname"]), is_me,
            ))
        if not focus_rows:
            focus_rows = [ft.Text(lang_store.t("no_friends"),
                                  size=13, color=TEXT_MUT, font_family=FONT)]

        if self.dash_rank_col_ref.current:
            self.dash_rank_col_ref.current.controls = focus_rows
            self.dash_rank_col_ref.current.update()

        # ── 자세 점수 랭킹 ────────────────────────────────────────────
        for u in combined:
            u["_posture_val"] = (
                u.get("today_posture_score", 0)
                if u.get("today_posture_date") == today_str else 0
            )
        posture_sorted = sorted(combined, key=lambda x: x["_posture_val"], reverse=True)
        posture_slice  = self._neighbor_slice(posture_sorted, my_uid)

        posture_rows = []
        for u in posture_slice:
            rank  = posture_sorted.index(u)
            is_me = u["uid"] == my_uid
            medal = medals[rank] if rank < 3 else f"#{rank + 1}"
            posture_rows.append(self._dash_rank_row(
                medal, u["nickname"],
                f"{u['_posture_val']}pts",
                _avatar_color(u["nickname"]), is_me,
                accent_color=PINK,
            ))
        if not posture_rows:
            posture_rows = [ft.Text(lang_store.t("no_posture_data"),
                                    size=13, color=TEXT_MUT, font_family=FONT)]

        if self.dash_rank_posture_col_ref.current:
            self.dash_rank_posture_col_ref.current.controls = posture_rows
            self.dash_rank_posture_col_ref.current.update()

    def _dash_rank_row(self, medal: str, name: str, val: str,
                       color: str, is_me: bool = False,
                       accent_color: str = ACCENT) -> ft.Row:
        return ft.Row(
            controls=[
                ft.Text(medal, size=15),
                ft.Container(
                    content=ft.Text(
                        name[:1].upper(), size=12,
                        color="#F0F9F8", font_family=FONT,
                    ),
                    width=22, height=22, border_radius=11,
                    bgcolor=color, alignment=ft.Alignment(0, 0),
                ),
                ft.Text(
                    name, size=14,
                    color=accent_color if is_me else TEXT_PRI,
                    font_family=FONT, expand=True,
                ),
                ft.Text(val, size=14, color=accent_color if is_me else TEXT_SEC,
                        font_family=FONT),
            ],
            spacing=7,
        )

    def _posture_ring(self, score=0, ring_ref=None, score_ref=None) -> ft.Container:
        color = ACCENT if score >= 70 else (WARNING if score >= 50 else DANGER)
        return ft.Container(
            width=113, height=113,
            content=ft.Stack(
                controls=[
                    ft.ProgressRing(
                        ref=ring_ref,
                        value=score / 100, width=113, height=113,
                        stroke_width=10, color=color, bgcolor=BORDER,
                    ),
                    ft.Container(
                        width=113, height=113,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Text(
                            ref=score_ref,
                            value=str(score) if score else "--",
                            size=26, weight=ft.FontWeight.W_500,
                            color=color, font_family=FONT,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ),
                ],
            ),
        )

    def _today_tasks(self) -> ft.Column:
        tasks = todo_store.get_tasks()
        order = {"High": 0, "Medium": 1, "Low": 2}
        sorted_tasks = sorted(tasks,
                              key=lambda t: (t["done"], order.get(t["priority"], 1)))
        preview = sorted_tasks[:4]

        def _make_task_row(task):
            done = task["done"]
            def toggle(_):
                todo_store.toggle_task(task)
            return ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(ft.Icons.DONE, size=13,
                                        color="#F0F9F8" if done else "transparent"),
                        width=18, height=18, border_radius=5,
                        border=ft.border.all(1.5, ACCENT if done else BORDER),
                        bgcolor=ACCENT if done else "transparent",
                        alignment=ft.Alignment(0, 0),
                        on_click=toggle,
                    ),
                    ft.Text(
                        task["title"], size=15,
                        color=TEXT_MUT if done else TEXT_PRI,
                        font_family=FONT, expand=True,
                        spans=[ft.TextSpan(style=ft.TextStyle(
                            decoration=ft.TextDecoration.LINE_THROUGH)
                        )] if done else [],
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )

        rows = [_make_task_row(t) for t in preview]

        if not rows:
            rows = [ft.Text(lang_store.t("no_tasks"), size=14, color=TEXT_MUT, font_family=FONT)]

        return ft.Column(ref=self.todo_col_ref, controls=rows, spacing=7)

    def build(self) -> ft.Container:
        now = datetime.now()
        today_idx = now.weekday()
        greeting = (
            lang_store.t("greeting_morning") if now.hour < 12
            else lang_store.t("greeting_afternoon") if now.hour < 18
            else lang_store.t("greeting_evening")
        )

        # ── Header ───────────────────────────────────────────────────
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(greeting, size=14, color=TEXT_SEC, font_family=FONT),
                            ft.Text(lang_store.t("today_overview"), size=20, color=TEXT_PRI, font_family=FONT),
                            ft.Text(now.strftime("%B %d, %Y"),
                                    size=13, color=TEXT_MUT, font_family=FONT),
                        ],
                        spacing=2, expand=True,
                    ),
                    ft.Column(
                        controls=[
                            mascot_widget(44),
                            ft.Text("ZZOOK", size=11, color=TEXT_MUT,
                                    font_family=FONT, text_align=ft.TextAlign.CENTER),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ACCENT_LT, border_radius=12,
            padding=ft.padding.only(left=18, top=8, right=14, bottom=8),
            border=ft.border.all(1.5, "#00C9A7"),
        )

        # ── Row 1: Posture / Tasks / Pomodoro ────────────────────────
        posture_card = ft.Container(
            content=card(
                ft.Column(
                    controls=[
                        ft.Text(lang_store.t("today_posture"), size=17,
                                color=TEXT_PRI, font_family=FONT),
                        ft.Container(expand=True),
                        ft.Row(
                            controls=[
                                self._posture_ring(0,
                                    ring_ref=self.dash_posture_ring_ref,
                                    score_ref=self.dash_posture_score_ref),
                                ft.Container(width=16),
                                ft.Column(
                                    width=128,
                                    controls=[
                                        ft.Text(
                                            ref=self.dash_posture_label_ref,
                                            value=lang_store.t("not_measured"), size=24,
                                            color=TEXT_MUT, font_family=FONT,
                                            weight=ft.FontWeight.W_400,
                                            no_wrap=False),
                                        ft.Container(height=6),
                                        ft.Container(
                                            width=162,
                                            ref=self.live_status_ref,
                                            content=ft.Column(
                                                controls=[
                                                    ft.Row(
                                                        controls=[
                                                            ft.Container(
                                                                ref=self.live_dot_ref,
                                                                width=6, height=6,
                                                                bgcolor=DANGER, border_radius=3,
                                                            ),
                                                            ft.Text(
                                                                ref=self.live_text_ref,
                                                                value=lang_store.t("live_off"),
                                                                size=11, color=DANGER,
                                                                font_family=FONT,
                                                            ),
                                                        ],
                                                        spacing=5,
                                                    ),
                                                ],
                                                spacing=0,
                                            ),
                                            bgcolor="#FFF0F0", border_radius=6,
                                            padding=ft.padding.only(
                                                left=8, top=4, right=12, bottom=4),
                                        ),
                                    ],
                                    spacing=0,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Container(expand=True),
                        ghost_btn(lang_store.t("go_to_posture"),
                                on_click=lambda _: self.navigate("posture"),
                                icon=ft.Icons.ARROW_FORWARD),
                    ],
                    spacing=0,
                ),
                padding=14,
                expand=True,
            ),
            height=ROW1_H, expand=True,
        )

        todo_card = ft.Container(
            content=card(
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(lang_store.t("todays_todo"), size=17,
                                        color=TEXT_PRI, font_family=FONT),
                                ft.Container(
                                    content=ft.Text(
                                        ref=self.todo_count_ref,
                                        value=f"{len(todo_store.get_tasks())} item{'s' if len(todo_store.get_tasks()) != 1 else ''}",
                                        size=13, color=ACCENT, font_family=FONT,
                                    ),
                                    bgcolor=ACCENT_LT, border_radius=8,
                                    padding=ft.padding.only(left=7, top=2, right=7, bottom=2),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Container(height=8),
                        self._today_tasks(),
                        ft.Container(expand=True),
                        ghost_btn(lang_store.t("view_all"),
                                  on_click=lambda _: self.navigate("todo"),
                                  icon=ft.Icons.ARROW_FORWARD),
                    ],
                    spacing=0,
                ),
                padding=14,
            ),
            height=ROW1_H, expand=True,
        )

        RING_SZ = 118
        BTN_SZ  = 34

        play_btn = ft.Container(
            ref=self.pomo_play_btn_ref,
            content=ft.Icon(
                ref=self.pomo_play_icon_ref,
                icon=ft.Icons.PLAY_ARROW,
                size=20, color="#F0F9F8",
            ),
            width=BTN_SZ + 10, height=BTN_SZ + 10,
            border_radius=(BTN_SZ + 10) // 2,
            bgcolor=ACCENT,
            alignment=ft.Alignment(0, 0),
            on_click=lambda e: self.pomo_start_stop_cb(e) if self.pomo_start_stop_cb else None,
            shadow=ft.BoxShadow(blur_radius=10, color=ACCENT + "55", offset=ft.Offset(0, 3)),
        )

        pomodoro_card = ft.Container(
            content=card(
                ft.Column(
                    controls=[
                        ft.Text(lang_store.t("pomodoro"), size=17, color=TEXT_PRI, font_family=FONT),
                        ft.Container(expand=True),
                        ft.Row(
                            controls=[
                                ft.Container(width=24),
                                # ── 링 ──────────────────────────────
                                ft.Stack(
                                    controls=[
                                        ft.ProgressRing(
                                            ref=self.pomo_ring_ref,
                                            value=1.0, width=RING_SZ, height=RING_SZ,
                                            stroke_width=10, color=ACCENT, bgcolor=BORDER,
                                        ),
                                        ft.Container(
                                            width=RING_SZ, height=RING_SZ,
                                            alignment=ft.Alignment(0, 0),
                                            content=ft.Text(
                                                ref=self.pomo_time_ref,
                                                value="25:00", size=22,
                                                color=ACCENT, font_family=FONT,
                                                text_align=ft.TextAlign.CENTER,
                                            ),
                                        ),
                                    ],
                                    width=RING_SZ, height=RING_SZ,
                                ),
                                ft.Container(width=16),
                                # ── 세션 수 ──────────────────────────
                                ft.Column(
                                    width=128,
                                    controls=[
                                        ft.Text(
                                            ref=self.pomo_cycles_ref,
                                            value="0 / 4",
                                            size=36, color=DANGER,
                                            font_family=FONT,
                                        ),
                                        ft.Container(height=4),
                                        ft.Text(
                                            ref=self.pomo_status_ref,
                                            value=lang_store.t("session_ready"),
                                            size=13, color=TEXT_MUT,
                                            font_family=FONT,
                                        ),
                                    ],
                                    spacing=0,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Container(expand=True),
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Icon(ft.Icons.REPLAY, size=16, color=TEXT_MUT),
                                    width=BTN_SZ, height=BTN_SZ,
                                    border_radius=BTN_SZ // 2,
                                    border=ft.border.all(1.5, BORDER),
                                    alignment=ft.Alignment(0, 0),
                                    on_click=lambda e: self.pomo_reset_cb(e) if self.pomo_reset_cb else None,
                                ),
                                play_btn,
                                ft.Container(
                                    content=ft.Icon(ft.Icons.SKIP_NEXT, size=16, color=TEXT_MUT),
                                    width=BTN_SZ, height=BTN_SZ,
                                    border_radius=BTN_SZ // 2,
                                    border=ft.border.all(1.5, BORDER),
                                    alignment=ft.Alignment(0, 0),
                                    on_click=lambda e: self.pomo_skip_cb(e) if self.pomo_skip_cb else None,
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                        ),
                    ],
                    spacing=0,
                ),
                padding=14,
                expand=True,
            ),
            on_click=lambda _: self.navigate("pomodoro"),
            height=ROW1_H, expand=True,
        )

        row1 = ft.Row(
            controls=[
                posture_card,
                ft.Container(width=12),
                pomodoro_card,
                ft.Container(width=12),
                todo_card,
            ],
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        # ── Row 2: Charts / Ranking ──────────────────────────────────
        days         = [lang_store.t("mon"), lang_store.t("tue"), lang_store.t("wed"), lang_store.t("thu"), lang_store.t("fri"), lang_store.t("sat"), lang_store.t("sun")]
        focus_vals   = [0] * 7
        posture_vals = [0] * 7
        MAX_H = 44
        MIN_H = 12

        def _bar_col(d, val, color, is_today):
            if val == 0:
                h = 4
            else:
                h = int(MIN_H + (val / 100) * (MAX_H - MIN_H))
            return ft.Column(
                controls=[
                    ft.Container(
                        width=22,
                        height=MAX_H,
                        content=ft.Column(
                            controls=[
                                ft.Container(expand=True),
                                ft.Container(
                                    width=22, height=h,
                                    bgcolor=color if is_today
                                            else (color + "88" if val > 0 else BORDER),
                                    border_radius=4,
                                ),
                            ],
                            spacing=0,
                        ),
                    ),
                    ft.Text(d, size=12,
                            color=color if is_today else TEXT_MUT,
                            font_family=FONT, text_align=ft.TextAlign.CENTER),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=16,
            )

        focus_bars = [
            _bar_col(d, v, ACCENT, i == today_idx)
            for i, (d, v) in enumerate(zip(days, focus_vals))
        ]
        posture_bars = [
            _bar_col(d, v,
                     ACCENT if v >= 70 else (WARNING if v >= 50 else DANGER),
                     i == today_idx)
            for i, (d, v) in enumerate(zip(days, posture_vals))
        ]

        CHART_H = (ROW2_H - 10) // 2 - 20

        def _chart(title, avg, bars, row_ref=None, avg_ref=None):
            return ft.Container(
                content=card(
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(title, size=17, color=TEXT_PRI, font_family=FONT),
                                    ft.Container(
                                        content=ft.Text(
                                            ref=avg_ref,
                                            value=avg, size=13, color=ACCENT,
                                            font_family=FONT),
                                        bgcolor=ACCENT_LT, border_radius=6,
                                        padding=ft.padding.only(left=8, top=3, right=8, bottom=3),
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Container(height=8),
                            ft.Container(
                                content=ft.Row(
                                    ref=row_ref,
                                    controls=bars,
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                height=MAX_H + 16,
                                alignment=ft.Alignment(0, 1),
                            ),
                        ],
                        spacing=0,
                    ),
                    padding=14,
                ),
                height=CHART_H, expand=1,
            )

        charts_col = ft.Container(
            content=ft.Column(
                controls=[
                    _chart(lang_store.t("weekly_focus") + lang_store.t("score_suffix"),   "No data", focus_bars,
                           row_ref=self.dash_focus_bars_ref,
                           avg_ref=self.dash_focus_avg_ref),
                    ft.Container(height=10),
                    _chart(lang_store.t("weekly_posture") + lang_store.t("score_suffix"), "No data", posture_bars,
                           row_ref=self.dash_posture_bars_ref,
                           avg_ref=self.dash_posture_avg_ref),
                ],
                spacing=0,
            ),
            height=310, expand=2,
        )

        rank_card = ft.Container(
            content=card(
                ft.Column(
                    controls=[
                        # ── 헤더 ────────────────────────────────────
                        ft.Row(
                            controls=[
                                ft.Text(lang_store.t("ranking"), size=17, color=TEXT_PRI, font_family=FONT),
                                ft.Container(
                                    content=ft.Text(lang_store.t("live"), size=12, color=ACCENT,
                                                    font_family=FONT),
                                    bgcolor=ACCENT_LT, border_radius=6,
                                    padding=ft.padding.only(left=6, top=2, right=6, bottom=2),
                                    border=ft.border.all(1.5, "#00C9A7"),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Container(height=2),
                        # ── 두 섹션 동등 분할 (각 50%) ─────────────
                        ft.Column(
                            controls=[
                                # 집중 시간 섹션
                                ft.Container(
                                    expand=1,
                                    content=ft.Column(
                                        controls=[
                                            ft.Text(lang_store.t("rank_focus_time"), size=13,
                                                    color=TEXT_SEC, font_family=FONT),
                                            ft.Container(height=2),
                                            ft.Column(
                                                ref=self.dash_rank_col_ref,
                                                controls=[ft.Row(
                                                    controls=[ft.ProgressRing(
                                                        width=16, height=16,
                                                        stroke_width=2, color=ACCENT,
                                                    )],
                                                    alignment=ft.MainAxisAlignment.CENTER,
                                                )],
                                                spacing=3,
                                            ),
                                        ],
                                        spacing=0,
                                    ),
                                ),
                                ft.Divider(color=BORDER, height=1),
                                # 자세 점수 섹션
                                ft.Container(
                                    expand=1,
                                    content=ft.Column(
                                        controls=[
                                            ft.Text(lang_store.t("rank_posture"), size=13,
                                                    color=TEXT_SEC, font_family=FONT),
                                            ft.Container(height=2),
                                            ft.Column(
                                                ref=self.dash_rank_posture_col_ref,
                                                controls=[],
                                                spacing=3,
                                            ),
                                        ],
                                        spacing=0,
                                    ),
                                ),
                            ],
                            spacing=2,
                            expand=True,
                        ),
                        ghost_btn(lang_store.t("view_all"),
                                  on_click=lambda _: self.navigate("ranking"),
                                  icon=ft.Icons.ARROW_FORWARD),
                    ],
                    spacing=2,
                    expand=True,
                ),
                padding=14,
            ),
            height=310, expand=1,
        )

        row2 = ft.Row(
            controls=[
                charts_col,
                ft.Container(width=9),
                ft.Container(content=rank_card, expand=1, padding=ft.padding.only(left=3, right=1)),
            ],
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    header,
                    ft.Container(height=8),
                    row1,
                    ft.Container(height=8),
                    row2,
                ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
            padding=ft.padding.only(left=22, top=12, right=22, bottom=12),
            bgcolor=BG_BASE,
        )
