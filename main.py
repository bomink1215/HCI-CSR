import flet as ft
from views.dashboard import DashboardView
from views.posture import PostureView
from views.pomodoro import PomodoroView
from views.todo import TodoView
from views.ranking import RankingView
from views.auth_view import AuthView
from views.profile_view import ProfileView
from components.nav import NavBar
from utils.alert_manager import start_alert_daemon
from utils import session, firebase, score_store, todo_store

APP_THEME = ft.Theme(
    color_scheme_seed="#00C9A7",
    font_family="DOSSaemmul",
)
BG_BASE = "#FFFFFF"


def main(page: ft.Page):
    page.title = "ZZOOK"
    page.theme = APP_THEME
    page.bgcolor = BG_BASE
    page.padding = 0
    page.fonts = {"DOSSaemmul": "fonts/DOSSaemmul.ttf"}

    page.window.width        = 1200
    page.window.height       = 720
    page.window.min_width    = 960
    page.window.min_height   = 576
    page.window.aspect_ratio = 5 / 3

    # 윈도우가 최종 크기(1200×720)로 완전히 자리잡은 뒤 중앙 이동
    async def _center_window():
        import asyncio
        await asyncio.sleep(0.5)
        page.window.center()
        page.update()

    page.run_task(_center_window)

    def show_auth():
        session.stop_auto_refresh()         # 로그아웃 시 토큰 갱신 중단
        score_store.init_for_user("")       # 로컬 데이터 초기화 (계정 전환 오염 방지)
        todo_store.init_for_user("")        # 투두 데이터 초기화
        page.controls.clear()
        auth = AuthView(page, on_login_success=show_main)
        page.add(auth.build())
        page.update()

    def show_main(user: dict):
        remember_me = user.pop("remember_me", False)
        session.set_user(user)
        if remember_me:
            user["remember_me"] = True
            session.save(user)
        else:
            session.clear()
        score_store.init_for_user(user["uid"])          # UID별 로컬 데이터 전환
        todo_store.init_for_user(user["uid"])           # UID별 투두 데이터 전환
        session.start_auto_refresh(firebase.refresh_id_token)  # 토큰 자동 갱신
        page.controls.clear()
        _build_main(page, show_auth)
        page.update()

    # Check for saved session (only auto-login if remember_me is set)
    saved = session.load()
    if saved and saved.get("remember_me"):
        session.set_user(saved)
        score_store.init_for_user(saved["uid"])         # UID별 로컬 데이터 전환
        todo_store.init_for_user(saved["uid"])          # UID별 투두 데이터 전환
        session.start_auto_refresh(firebase.refresh_id_token)  # 저장된 세션도 즉시 갱신
        _build_main(page, show_auth)
    else:
        show_auth()


def _build_main(page: ft.Page, show_auth):
    current_view_name = ["dashboard"]
    views = {}

    def navigate(view_name: str):
        current_view_name[0] = view_name
        for k, v in views.items():
            v.visible = k == view_name
        nav.update_active(view_name)
        page.update()
        if view_name == "ranking":
            ranking_view.refresh()
        elif view_name == "dashboard":
            dashboard_view.refresh()

    dashboard_view = DashboardView(page, navigate)
    posture_view   = PostureView(page)
    pomodoro_view  = PomodoroView(page)
    todo_view      = TodoView(page)
    ranking_view   = RankingView(page)
    profile_view   = ProfileView(page, on_logout=show_auth)

    pomodoro_view.on_tick             = dashboard_view.update_pomodoro
    dashboard_view.pomo_start_stop_cb = pomodoro_view._start_stop
    dashboard_view.pomo_reset_cb      = pomodoro_view._reset
    dashboard_view.pomo_skip_cb       = pomodoro_view._skip_next

    views = {
        "dashboard": dashboard_view.build(),
        "posture":   posture_view.build(),
        "pomodoro":  pomodoro_view.build(),
        "todo":      todo_view.build(),
        "ranking":   ranking_view.build(),
        "profile":   profile_view.build(),
    }

    for k, v in views.items():
        v.visible = k == "dashboard"

    nav = NavBar(navigate)
    nav_bar = nav.build()

    content_stack = ft.Stack(controls=list(views.values()), expand=True)

    page.add(
        ft.Row(
            controls=[
                nav_bar,
                ft.VerticalDivider(width=1, color="#E2E6EC"),
                content_stack,
            ],
            expand=True,
            spacing=0,
        )
    )

    start_alert_daemon()
    page.update()
    dashboard_view.refresh()


ft.app(target=main)
