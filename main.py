import flet as ft
from views.dashboard import DashboardView
from views.posture import PostureView
from views.pomodoro import PomodoroView
from views.todo import TodoView
from views.ranking import RankingView
from components.nav import NavBar
from utils.alert_manager import start_alert_daemon

APP_THEME = ft.Theme(
    color_scheme_seed="#00C9A7",
    font_family="Galmuri",
)

BG_BASE = "#FFFFFF"


def main(page: ft.Page):
    page.title = "FocusMate"
    page.theme = APP_THEME
    page.bgcolor = BG_BASE
    page.window_width = 1100
    page.window_height = 740
    page.window_min_width = 900
    page.window_min_height = 620
    page.padding = 0
    page.fonts = {
        "Galmuri":     "fonts/Galmuri11.ttf",
        "GalmuriBold": "fonts/Galmuri11-Bold.ttf",
        
    }

    current_view_name = ["dashboard"]
    views = {}

    def navigate(view_name: str):
        current_view_name[0] = view_name
        for k, v in views.items():
            v.visible = k == view_name
        nav.update_active(view_name)
        page.update()

    dashboard_view = DashboardView(page, navigate)
    posture_view   = PostureView(page)
    pomodoro_view  = PomodoroView(page)
    todo_view      = TodoView(page)
    ranking_view   = RankingView(page)

    views = {
        "dashboard": dashboard_view.build(),
        "posture":   posture_view.build(),
        "pomodoro":  pomodoro_view.build(),
        "todo":      todo_view.build(),
        "ranking":   ranking_view.build(),
    }

    for k, v in views.items():
        v.visible = k == "dashboard"

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
                ft.VerticalDivider(width=1, color="#E2E6EC"),
                content_stack,
            ],
            expand=True,
            spacing=0,
        )
    )

    start_alert_daemon()
    page.update()


ft.app(target=main)
