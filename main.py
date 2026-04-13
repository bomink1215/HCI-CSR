import flet as ft
from views.dashboard import DashboardView
from views.posture import PostureView
from views.pomodoro import PomodoroView
from views.todo import TodoView
from views.ranking import RankingView
from components.nav import NavBar
from components.notification import PostureAlert
from utils.alert_manager import start_alert_daemon
import threading

APP_THEME = ft.Theme(
    color_scheme_seed="#00E5CC",
    font_family="Pretendard",
)

BG_DARK = "#080B10"
BG_CARD = "#0D1117"
BG_CARD2 = "#131920"
ACCENT = "#00E5CC"
ACCENT2 = "#FF6B6B"
TEXT_PRIMARY = "#E8EDF3"
TEXT_MUTED = "#4A5568"


def main(page: ft.Page):
    page.title = "FocusMate"
    page.theme = APP_THEME
    page.bgcolor = BG_DARK
    page.window_width = 1100
    page.window_height = 740
    page.window_min_width = 900
    page.window_min_height = 620
    page.padding = 0
    page.fonts = {
        "Pretendard": "https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css",
        "JetBrains": "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap",
    }

    # ── State ──────────────────────────────────────────────────
    current_view_name = ["dashboard"]

    views = {}

    def navigate(view_name: str):
        current_view_name[0] = view_name
        for k, v in views.items():
            v.visible = k == view_name
        nav.update_active(view_name)
        page.update()

    # ── Views ──────────────────────────────────────────────────
    dashboard_view = DashboardView(page, navigate)
    posture_view = PostureView(page)
    pomodoro_view = PomodoroView(page)
    todo_view = TodoView(page)
    ranking_view = RankingView(page)

    views = {
        "dashboard": dashboard_view.build(),
        "posture": posture_view.build(),
        "pomodoro": pomodoro_view.build(),
        "todo": todo_view.build(),
        "ranking": ranking_view.build(),
    }

    for k, v in views.items():
        v.visible = k == "dashboard"

    # ── Layout ─────────────────────────────────────────────────
    nav = NavBar(navigate)
    nav_bar = nav.build()

    content_stack = ft.Stack(
        controls=list(views.values()),
        expand=True,
    )

    page.add(
        ft.Row(
            controls=[
                nav_bar,
                ft.VerticalDivider(width=1, color="#1A2332"),
                content_stack,
            ],
            expand=True,
            spacing=0,
        )
    )

    # ── 자세 알림 데몬 시작 ────────────────────────────────────
    start_alert_daemon()

    page.update()


ft.app(target=main)
