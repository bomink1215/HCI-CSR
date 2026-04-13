import flet as ft
from components.ui import card, section_title, stat_chip, accent_btn, ghost_btn, mascot_widget
from datetime import datetime

BG_BASE   = "#FFFFFF"
BG_CARD   = "#F4F6F8"
BG_CARD2  = "#EAECEF"
ACCENT    = "#00C9A7"
ACCENT_LT = "#D6F5EF"
ACCENT_DK = "#009E83"
DANGER    = "#FF5C5C"
WARNING   = "#FFB347"
TEXT_PRI  = "#1A1D23"
TEXT_SEC  = "#5A6375"
TEXT_MUT  = "#9DA8B7"
BORDER    = "#E2E6EC"


class DashboardView:
    def __init__(self, page: ft.Page, navigate):
        self.page = page
        self.navigate = navigate

    def _posture_ring(self, score=78) -> ft.Container:
        color = ACCENT if score >= 70 else (WARNING if score >= 50 else DANGER)
        return ft.Container(
            width=110, height=110,
            content=ft.Stack(
                controls=[
                    ft.ProgressRing(
                        value=score / 100,
                        width=110, height=110,
                        stroke_width=10,
                        color=color,
                        bgcolor="#E2E6EC",
                    ),
                    ft.Container(
                        width=110, height=110,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Column(
                            controls=[
                                ft.Text(str(score), size=26, weight=ft.FontWeight.W_500,
                                        color=color, font_family="GalmuriBold",
                                        text_align=ft.TextAlign.CENTER),
                                ft.Text("자세", size=11, color=TEXT_MUT,
                                        font_family="Galmuri",
                                        text_align=ft.TextAlign.CENTER),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=2,
                        ),
                    ),
                ],
            ),
        )

    def _today_tasks(self) -> ft.Column:
        tasks = [
            ("프로젝트 기획서 작성", True),
            ("팀 미팅 준비", True),
            ("코드 리뷰", False),
            ("문서화 작업", False),
        ]
        rows = []
        for label, done in tasks:
            rows.append(
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(
                                "\ue876" if done else "",
                                font_family="Material Icons",
                                size=13,
                                color="#FFFFFF" if done else "transparent",
                            ),
                            width=22, height=22,
                            border_radius=6,
                            border=ft.border.all(1.5, ACCENT if done else BORDER),
                            bgcolor=ACCENT if done else "transparent",
                            alignment=ft.Alignment(0, 0),
                        ),
                        ft.Text(
                            label,
                            size=13,
                            color=TEXT_MUT if done else TEXT_PRI,
                            font_family="Galmuri",
                            expand=True,
                            spans=[
                                ft.TextSpan(
                                    style=ft.TextStyle(decoration=ft.TextDecoration.LINE_THROUGH)
                                )
                            ] if done else [],
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
        return ft.Column(controls=rows, spacing=10)

    def _weekly_bar(self) -> ft.Row:
        days = ["월", "화", "수", "목", "금", "토", "일"]
        values = [85, 92, 67, 88, 95, 40, 0]
        today_idx = datetime.now().weekday()
        bars = []
        for i, (d, v) in enumerate(zip(days, values)):
            is_today = i == today_idx
            bar_h = max(4, int(v * 0.65))
            bars.append(
                ft.Column(
                    controls=[
                        ft.Container(
                            width=22,
                            height=bar_h,
                            bgcolor=ACCENT if is_today else (BG_CARD2 if v > 0 else BORDER),
                            border_radius=4,
                            shadow=ft.BoxShadow(blur_radius=6, color=ACCENT + "44",
                                                offset=ft.Offset(0, 2)) if is_today else None,
                        ),
                        ft.Text(d, size=10,
                                color=ACCENT if is_today else TEXT_MUT,
                                font_family="Galmuri",
                                text_align=ft.TextAlign.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                )
            )
        return ft.Row(
            controls=bars,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

    def build(self) -> ft.Container:
        now = datetime.now()
        greeting = (
            "좋은 아침이에요! ☀️" if now.hour < 12
            else "점심 식사는 하셨나요? 🍱" if now.hour < 18
            else "오늘도 수고하셨어요! 🌙"
        )

        # ── 마스코트 + 인사 헤더 ───────────────────────────────
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(greeting, size=13, color=TEXT_SEC,
                                    font_family="Galmuri"),
                            ft.Text("오늘의 현황", size=26, weight=ft.FontWeight.W_400,
                                    color=TEXT_PRI, font_family="Galmuri"),
                            ft.Text(now.strftime("%Y년 %m월 %d일"),
                                    size=12, color=TEXT_MUT, font_family="Galmuri"),
                        ],
                        spacing=3,
                        expand=True,
                    ),
                    # 픽셀아트 마스코트
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                mascot_widget(64),
                                ft.Text("FocusMate", size=9, color=TEXT_MUT,
                                        font_family="Galmuri",
                                        text_align=ft.TextAlign.CENTER),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=4,
                        ),
                        padding=ft.padding.only(right=4),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ACCENT_LT,
            border_radius=16,
            padding=ft.padding.only(left=24, top=18, right=20, bottom=18),
            border=ft.border.all(1, ACCENT + "40"),
        )

        # ── 자세 카드 ────────────────────────────────────────────
        posture_card = card(
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("오늘의 자세 점수", size=12,
                                            color=TEXT_MUT, font_family="Galmuri"),
                                    ft.Text("양호 👍", size=20, weight=ft.FontWeight.W_400,
                                            color=ACCENT, font_family="Galmuri"),
                                    ft.Container(height=4),
                                    ft.Text("지난 1시간 평균 78점",
                                            size=11, color=TEXT_SEC,
                                            font_family="Galmuri"),
                                ],
                                spacing=4,
                                expand=True,
                            ),
                            self._posture_ring(78),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Container(
                                    width=7, height=7,
                                    bgcolor=ACCENT,
                                    border_radius=4,
                                ),
                                ft.Text("실시간 감지 중", size=11, color=ACCENT,
                                        font_family="Galmuri"),
                            ],
                            spacing=6,
                        ),
                        bgcolor=ACCENT_LT,
                        border_radius=8,
                        padding=ft.padding.only(left=12, top=7, right=12, bottom=7),
                        border=ft.border.all(1, ACCENT + "40"),
                    ),
                ],
                spacing=0,
            ),
            expand=True,
        )

        stats_col = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        stat_chip("집중 세션", "7회", ACCENT),
                        stat_chip("총 집중", "3h 20m", "#9B8FFF"),
                    ],
                    spacing=12,
                ),
                stat_chip("연속 집중일", "🔥 5일", DANGER),
            ],
            spacing=12,
            expand=True,
        )

        top_row = ft.Row(
            controls=[posture_card, ft.Container(width=14), stats_col],
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        # ── 할 일 + 뽀모도로 빠른 실행 ───────────────────────────
        todo_card = card(
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("오늘의 할 일", size=14, weight=ft.FontWeight.W_400,
                                    color=TEXT_PRI, font_family="Galmuri"),
                            ft.Container(
                                content=ft.Text("4개", size=11, color=ACCENT,
                                                font_family="Galmuri"),
                                bgcolor=ACCENT_LT,
                                border_radius=10,
                                padding=ft.padding.only(left=8, top=3, right=8, bottom=3),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=12),
                    self._today_tasks(),
                    ft.Container(height=10),
                    ghost_btn("모두 보기", on_click=lambda _: self.navigate("todo"),
                              icon="\ue5c8"),
                ],
                spacing=0,
            ),
            expand=2,
        )

        pomodoro_quick = card(
            ft.Column(
                controls=[
                    ft.Text("뽀모도로", size=14, weight=ft.FontWeight.W_400,
                            color=TEXT_PRI, font_family="Galmuri"),
                    ft.Container(height=10),
                    ft.Text("25:00", size=40, weight=ft.FontWeight.W_400,
                            color=ACCENT, font_family="Galmuri",
                            text_align=ft.TextAlign.CENTER),
                    ft.Text("세션 준비됨", size=12, color=TEXT_MUT,
                            font_family="Galmuri",
                            text_align=ft.TextAlign.CENTER),
                    ft.Container(height=12),
                    accent_btn("시작하기", on_click=lambda _: self.navigate("pomodoro"),
                               icon="\ue037"),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            expand=1,
        )

        mid_row = ft.Row(
            controls=[todo_card, ft.Container(width=14), pomodoro_quick],
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        # ── 주간 차트 + 랭킹 미리보기 ────────────────────────────
        weekly_card = card(
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("이번 주 집중도", size=14, weight=ft.FontWeight.W_400,
                                    color=TEXT_PRI, font_family="Galmuri"),
                            ft.Container(
                                content=ft.Text("평균 78점", size=11, color=ACCENT,
                                                font_family="Galmuri"),
                                bgcolor=ACCENT_LT,
                                border_radius=8,
                                padding=ft.padding.only(left=8, top=3, right=8, bottom=3),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=14),
                    ft.Container(
                        content=self._weekly_bar(),
                        height=68,
                        alignment=ft.Alignment(0, 1),
                    ),
                ],
            ),
            expand=2,
        )

        rank_preview = card(
            ft.Column(
                controls=[
                    ft.Text("친구 랭킹", size=14, weight=ft.FontWeight.W_400,
                            color=TEXT_PRI, font_family="Galmuri"),
                    ft.Container(height=10),
                    *[
                        ft.Row(
                            controls=[
                                ft.Text(medal, size=16),
                                ft.Container(
                                    content=ft.Text(name[0], size=11,
                                                    color="#FFFFFF", font_family="Galmuri"),
                                    width=26, height=26, border_radius=13,
                                    bgcolor=color, alignment=ft.Alignment(0, 0),
                                ),
                                ft.Text(name, size=13, color=TEXT_PRI,
                                        font_family="Galmuri", expand=True),
                                ft.Text(time_, size=12, color=TEXT_SEC,
                                        font_family="Galmuri"),
                            ],
                            spacing=8,
                        )
                        for medal, name, time_, color in [
                            ("🥇", "김철수", "4h 32m", ACCENT),
                            ("🥈", "이영희", "3h 55m", "#9B8FFF"),
                            ("🥉", "나", "3h 20m", DANGER),
                        ]
                    ],
                    ft.Container(height=4),
                    ghost_btn("전체 보기", on_click=lambda _: self.navigate("ranking"),
                              icon="\ue5c8"),
                ],
                spacing=8,
            ),
            expand=1,
        )

        bottom_row = ft.Row(
            controls=[weekly_card, ft.Container(width=14), rank_preview],
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    header,
                    ft.Container(height=16),
                    top_row,
                    ft.Container(height=12),
                    mid_row,
                    ft.Container(height=12),
                    bottom_row,
                ],
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
            padding=ft.padding.only(left=28, top=24, right=28, bottom=24),
            bgcolor=BG_BASE,
        )
