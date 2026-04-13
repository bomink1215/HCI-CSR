import flet as ft
from components.ui import card, section_title, stat_chip, accent_btn, ghost_btn
from datetime import datetime

BG_DARK = "#080B10"
BG_CARD = "#0D1117"
BG_CARD2 = "#131920"
ACCENT = "#00E5CC"
ACCENT2 = "#FF6B6B"
TEXT_PRIMARY = "#E8EDF3"
TEXT_MUTED = "#4A5568"
BORDER = "#1A2332"


class DashboardView:
    def __init__(self, page: ft.Page, navigate):
        self.page = page
        self.navigate = navigate

    def _posture_ring(self, score=78) -> ft.Stack:
        """Circular posture score ring (mock SVG-style using ft.ProgressRing)"""
        color = ACCENT if score >= 70 else ("#FFA500" if score >= 50 else "#FF6B6B")
        return ft.Stack(
            controls=[
                ft.Container(
                    content=ft.ProgressRing(
                        value=score / 100,
                        width=120, height=120,
                        stroke_width=10,
                        color=color,
                        bgcolor="#1A2332",
                    ),
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(str(score), size=30, weight=ft.FontWeight.W_900,
                                    color=color, font_family="Pretendard",
                                    text_align=ft.TextAlign.CENTER),
                            ft.Text("자세", size=11, color=TEXT_MUTED,
                                    font_family="Pretendard",
                                    text_align=ft.TextAlign.CENTER),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0,
                    ),
                    width=120, height=120,
                    alignment=ft.Alignment(0, 0),
                ),
            ],
            width=120, height=120,
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
                                size=14,
                                color=ACCENT if done else "transparent",
                            ),
                            width=22, height=22,
                            border_radius=6,
                            border=ft.border.all(1, ACCENT if done else "#2A3A4C"),
                            bgcolor="#0A1F1C" if done else "transparent",
                            alignment=ft.Alignment(0, 0),
                        ),
                        ft.Text(
                            label,
                            size=13,
                            color=TEXT_MUTED if done else TEXT_PRIMARY,
                            font_family="Pretendard",
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
            bar_h = max(4, int(v * 0.7))
            bars.append(
                ft.Column(
                    controls=[
                        ft.Container(
                            width=24,
                            height=bar_h,
                            bgcolor=ACCENT if is_today else ("#1E3A3A" if v > 0 else "#1A2332"),
                            border_radius=4,
                        ),
                        ft.Text(d, size=10,
                                color=ACCENT if is_today else TEXT_MUTED,
                                font_family="Pretendard",
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

        # ── Top row: posture + stats ───────────────────────────
        posture_card = card(
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("오늘의 자세 점수", size=13,
                                            color=TEXT_MUTED, font_family="Pretendard"),
                                    ft.Text("양호", size=22, weight=ft.FontWeight.W_800,
                                            color=ACCENT, font_family="Pretendard"),
                                    ft.Container(height=4),
                                    ft.Text("지난 1시간 평균 78점\n지속적으로 모니터링 중",
                                            size=11, color=TEXT_MUTED,
                                            font_family="Pretendard"),
                                ],
                                spacing=4,
                                expand=True,
                            ),
                            self._posture_ring(78),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=12),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Container(
                                    width=8, height=8,
                                    bgcolor=ACCENT,
                                    border_radius=4,
                                    animate=ft.Animation(800, ft.AnimationCurve.EASE_IN_OUT),
                                ),
                                ft.Text("실시간 감지 중", size=11, color=ACCENT,
                                        font_family="Pretendard"),
                            ],
                            spacing=6,
                        ),
                        bgcolor="#071A17",
                        border_radius=8,
                        padding=ft.padding.only(left=12, top=8, right=12, bottom=8),
                        border=ft.border.all(1, "#0D3330"),
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
                        stat_chip("총 집중", "3h 20m", "#A78BFA"),
                    ],
                    spacing=12,
                ),
                stat_chip("연속 집중일", "🔥 5일", ACCENT2),
            ],
            spacing=12,
            expand=True,
        )

        top_row = ft.Row(
            controls=[posture_card, ft.Container(width=16), stats_col],
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        # ── Middle row: today tasks + pomodoro quick ───────────
        todo_card = card(
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("오늘의 할 일", size=15, weight=ft.FontWeight.W_700,
                                    color=TEXT_PRIMARY, font_family="Pretendard"),
                            ft.Container(
                                content=ft.Text("4개", size=11, color=ACCENT,
                                                font_family="Pretendard"),
                                bgcolor="#071A17",
                                border_radius=10,
                                padding=ft.padding.only(left=8, top=3, right=8, bottom=3),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=12),
                    self._today_tasks(),
                    ft.Container(height=8),
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
                    ft.Text("뽀모도로", size=15, weight=ft.FontWeight.W_700,
                            color=TEXT_PRIMARY, font_family="Pretendard"),
                    ft.Container(height=12),
                    ft.Text("25:00", size=44, weight=ft.FontWeight.W_900,
                            color=ACCENT, font_family="JetBrains",
                            text_align=ft.TextAlign.CENTER),
                    ft.Text("세션 준비됨", size=12, color=TEXT_MUTED,
                            font_family="Pretendard",
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
            controls=[todo_card, ft.Container(width=16), pomodoro_quick],
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        # ── Bottom row: weekly chart + ranking preview ─────────
        weekly_card = card(
            ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text("이번 주 집중도", size=15, weight=ft.FontWeight.W_700,
                                    color=TEXT_PRIMARY, font_family="Pretendard"),
                            ft.Text("평균 78점", size=12, color=ACCENT,
                                    font_family="Pretendard"),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=14),
                    ft.Container(
                        content=self._weekly_bar(),
                        height=70,
                        alignment=ft.Alignment(0, 1),
                    ),
                ],
            ),
            expand=2,
        )

        rank_preview = card(
            ft.Column(
                controls=[
                    ft.Text("친구 랭킹", size=15, weight=ft.FontWeight.W_700,
                            color=TEXT_PRIMARY, font_family="Pretendard"),
                    ft.Container(height=10),
                    *[
                        ft.Row(
                            controls=[
                                ft.Text(medal, size=16),
                                ft.Container(
                                    content=ft.Text(name[0], size=12,
                                                    color="#080B10", font_family="Pretendard"),
                                    width=26, height=26, border_radius=13,
                                    bgcolor=color, alignment=ft.Alignment(0, 0),
                                ),
                                ft.Text(name, size=13, color=TEXT_PRIMARY,
                                        font_family="Pretendard", expand=True),
                                ft.Text(time_, size=12, color=TEXT_MUTED,
                                        font_family="JetBrains"),
                            ],
                            spacing=8,
                        )
                        for medal, name, time_, color in [
                            ("🥇", "김철수", "4h 32m", ACCENT),
                            ("🥈", "이영희", "3h 55m", "#A78BFA"),
                            ("🥉", "나", "3h 20m", ACCENT2),
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
            controls=[weekly_card, ft.Container(width=16), rank_preview],
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        # ── Page header ────────────────────────────────────────
        header = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(greeting, size=13, color=TEXT_MUTED,
                                font_family="Pretendard"),
                        ft.Text("오늘의 현황", size=26, weight=ft.FontWeight.W_900,
                                color=TEXT_PRIMARY, font_family="Pretendard"),
                    ],
                    spacing=2,
                ),
                ft.Container(
                    content=ft.Text(now.strftime("%m월 %d일 %A"),
                                    size=12, color=TEXT_MUTED, font_family="Pretendard"),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    header,
                    ft.Container(height=16),
                    top_row,
                    ft.Container(height=14),
                    mid_row,
                    ft.Container(height=14),
                    bottom_row,
                ],
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
            padding=ft.padding.only(left=28, top=24, right=28, bottom=24),
            bgcolor="#080B10",
        )
