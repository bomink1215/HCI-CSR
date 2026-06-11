import flet as ft
from views.dashboard import DashboardView
from views.posture import PostureView
from views.pomodoro import PomodoroView
from views.todo import TodoView
from views.ranking import RankingView
from views.auth_view import AuthView
from views.profile_view import ProfileView
from views.tutorial import TutorialOverlay
from components.nav import NavBar
from utils.alert_manager import start_alert_daemon
from utils import session, firebase, score_store, todo_store, prefs

APP_THEME = ft.Theme(
    color_scheme=ft.ColorScheme(
        primary="#7AC3B8",
        secondary="#B9E6E0",
        surface="#FFFFFF",
    ),
    font_family="DOSSaemmul",
)
BG_BASE   = "#F0F9F8"


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
        await page.window.center()
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


def _build_main(page: ft.Page, show_auth, initial_view: str = "dashboard", pomo_state: dict = None):
    current_view_name = [initial_view]
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
    # 언어 변경 시 포모도로 세션/타이머 상태 복원
    if pomo_state:
        pomodoro_view.sessions_done  = pomo_state["sessions_done"]
        pomodoro_view.cycle_count    = pomo_state["cycle_count"]
        pomodoro_view.focus_minutes  = pomo_state["focus_minutes"]
        pomodoro_view.rest_minutes   = pomo_state["rest_minutes"]
        pomodoro_view.remaining      = pomo_state["remaining"]
        pomodoro_view.mode           = pomo_state["mode"]
    todo_view      = TodoView(page)
    ranking_view   = RankingView(page)
    profile_view   = ProfileView(page, on_logout=show_auth)

    pomodoro_view.on_tick             = dashboard_view.update_pomodoro
    pomodoro_view.on_sessions_update  = dashboard_view.update_sessions
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
        v.visible = k == initial_view

    def _rebuild():
        """언어 변경 시 현재 탭을 유지한 채 메인 UI 전체를 재구성."""
        from utils import session as _sess
        user = _sess.get_user()
        if user:
            saved = current_view_name[0]
            # 포모도로 세션/타이머 상태 보존
            saved_pomo = {
                "sessions_done": pomodoro_view.sessions_done,
                "cycle_count":   pomodoro_view.cycle_count,
                "focus_minutes": pomodoro_view.focus_minutes,
                "rest_minutes":  pomodoro_view.rest_minutes,
                "remaining":     pomodoro_view.remaining,
                "mode":          pomodoro_view.mode,
            }
            page.controls.clear()
            _build_main(page, show_auth, initial_view=saved, pomo_state=saved_pomo)
            page.update()

    nav = NavBar(navigate, on_rebuild=_rebuild)
    nav_bar = nav.build()  # show_tutorial_cb는 아래서 주입

    content_stack = ft.Stack(controls=list(views.values()), expand=True)

    # 먼저 page에 추가해야 컨트롤 .update() 호출 가능
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

    # ── 튜토리얼 오버레이 ──────────────────────────────────────────
    user = session.get_user()
    uid  = user["uid"] if user else ""

    def _on_tutorial_close():
        if uid:
            prefs.mark_tutorial_seen(uid)

    tutorial = TutorialOverlay(page, on_close=_on_tutorial_close)
    tutorial_control = tutorial.build()
    page.overlay.append(tutorial_control)

    def _show_tutorial():
        tutorial.show()

    dashboard_view.show_tutorial_cb = _show_tutorial
    nav.show_tutorial_cb = _show_tutorial

    # page.add() 이후에 navigate + refresh (컨트롤이 페이지에 붙은 뒤)
    navigate(initial_view)
    dashboard_view.update_sessions(pomodoro_view.sessions_done, pomodoro_view.cycle_count)
    page.update()

    # 슬라이더 on_change가 page.update() 중에 remaining을 덮어쓸 수 있으므로 재적용
    if pomo_state:
        pomodoro_view.remaining = pomo_state["remaining"]
        pomodoro_view.total     = pomo_state["focus_minutes"] * 60
        pomodoro_view._update_display()
        page.update()

    # 신규 유저(튜토리얼 미확인)면 자동 표시
    if uid and not prefs.is_tutorial_seen(uid):
        tutorial.show()


ft.app(main)
