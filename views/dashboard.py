import flet as ft
from components.ui import card, accent_btn, ghost_btn, mascot_widget
from datetime import datetime

BG_BASE   = "#FFFFFF"
BG_CARD   = "#F4F6F8"
ACCENT    = "#00C9A7"
ACCENT_LT = "#D6F5EF"
DANGER    = "#FF5C5C"
WARNING   = "#FFB347"
PURPLE    = "#9B8FFF"
TEXT_PRI  = "#1A1D23"
TEXT_SEC  = "#5A6375"
TEXT_MUT  = "#9DA8B7"
BORDER    = "#E2E6EC"
FONT      = "DOSSaemmul"

# 행 높이 상수
ROW1_H = 220
ROW2_H = 340


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
                        value=score / 100, width=110, height=110,
                        stroke_width=10, color=color, bgcolor=BORDER,
                    ),
                    ft.Container(
                        width=110, height=110,
                        alignment=ft.Alignment(0, 0),
                        content=ft.Column(
                            controls=[
                                ft.Text(str(score), size=26,
                                        weight=ft.FontWeight.W_500,
                                        color=color, font_family=FONT,
                                        text_align=ft.TextAlign.CENTER),
                                ft.Text("자세", size=11, color=TEXT_MUT,
                                        font_family=FONT,
                                        text_align=ft.TextAlign.CENTER),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=1,
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
                                font_family="Material Icons", size=11,
                                color="#FFFFFF" if done else "transparent",
                            ),
                            width=18, height=18, border_radius=5,
                            border=ft.border.all(1.5, ACCENT if done else BORDER),
                            bgcolor=ACCENT if done else "transparent",
                            alignment=ft.Alignment(0, 0),
                        ),
                        ft.Text(
                            label, size=13,
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
            )
        return ft.Column(controls=rows, spacing=7)

    def build(self) -> ft.Container:
        now = datetime.now()
        today_idx = now.weekday()
        greeting = (
            "좋은 아침이에요! ☀️" if now.hour < 12
            else "점심 식사는 하셨나요? 🍱" if now.hour < 18
            else "오늘도 수고하셨어요! 🌙"
        )

        # ── 헤더 ─────────────────────────────────────────────────
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(greeting, size=12, color=TEXT_SEC, font_family=FONT),
                            ft.Text("오늘의 현황", size=20, color=TEXT_PRI, font_family=FONT),
                            ft.Text(now.strftime("%Y년 %m월 %d일"),
                                    size=11, color=TEXT_MUT, font_family=FONT),
                        ],
                        spacing=2, expand=True,
                    ),
                    ft.Column(
                        controls=[
                            mascot_widget(44),
                            ft.Text("FocusMate", size=9, color=TEXT_MUT,
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
            border=ft.border.all(1, ACCENT + "40"),
        )

        # ── 1행: 자세 / 할 일 / 뽀모도로 (height=ROW1_H 고정) ───
        posture_card = ft.Container(
            content=card(
                ft.Column(
                    controls=[
                        ft.Container(expand=1),
                        ft.Row(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Text("오늘의 자세", size=11,
                                                color=TEXT_MUT, font_family=FONT),
                                        ft.Container(height=6),
                                        ft.Text("양호 👍", size=20,
                                                color=ACCENT, font_family=FONT),
                                        ft.Container(height=4),
                                        ft.Text("평균 78점", size=12,
                                                color=TEXT_SEC, font_family=FONT),
                                    ],
                                    spacing=0, expand=True,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                self._posture_ring(78),
                            ],
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=8,
                        ),
                        ft.Container(expand=1),
                        # 하단: 뱃지
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Container(width=6, height=6,
                                                 bgcolor=ACCENT, border_radius=3),
                                    ft.Text("실시간 감지 중", size=10,
                                            color=ACCENT, font_family=FONT),
                                ],
                                spacing=5,
                            ),
                            bgcolor=ACCENT_LT, border_radius=6,
                            padding=ft.padding.only(left=10, top=5, right=10, bottom=5),
                            border=ft.border.all(1, ACCENT + "40"),
                        ),
                    ],
                    spacing=0,
                ),
                padding=14,
            ),
            height=ROW1_H, expand=1,
        )

        todo_card = ft.Container(
            content=card(
                ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("오늘의 할 일", size=13,
                                        color=TEXT_PRI, font_family=FONT),
                                ft.Container(
                                    content=ft.Text("4개", size=11, color=ACCENT,
                                                    font_family=FONT),
                                    bgcolor=ACCENT_LT, border_radius=8,
                                    padding=ft.padding.only(left=7, top=2, right=7, bottom=2),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.Container(height=8),
                        self._today_tasks(),
                        ft.Container(expand=True),
                        ghost_btn("모두 보기",
                                  on_click=lambda _: self.navigate("todo"),
                                  icon="\ue5c8"),
                    ],
                    spacing=0,
                ),
                padding=14,
            ),
            height=ROW1_H, expand=2,
        )

        pomodoro_card = ft.Container(
            content=card(
                ft.Column(
                    controls=[
                        ft.Text("뽀모도로", size=13, color=TEXT_PRI, font_family=FONT),
                        ft.Container(expand=1),
                        ft.Text("25:00", size=34, color=ACCENT, font_family=FONT,
                                text_align=ft.TextAlign.CENTER),
                        ft.Text("세션 준비됨", size=11, color=TEXT_MUT,
                                font_family=FONT, text_align=ft.TextAlign.CENTER),
                        ft.Container(expand=1),
                        accent_btn("시작하기",
                                   on_click=lambda _: self.navigate("pomodoro"),
                                   icon="\ue037"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                ),
                padding=14,
            ),
            height=ROW1_H, expand=1,
        )

        row1 = ft.Row(
            controls=[
                posture_card,
                ft.Container(width=10),
                todo_card,
                ft.Container(width=10),
                pomodoro_card,
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        # ── 2행: 차트 컬럼 / 랭킹 카드 (height=ROW2_H 고정) ─────
        days         = ["월", "화", "수", "목", "금", "토", "일"]
        focus_vals   = [85, 92, 67, 88, 95, 40, 0]
        posture_vals = [78, 88, 70, 82, 91, 55, 0]
        MAX_H = 52
        MIN_H = 12

        def _bar_col(d, val, color, is_today):
            if val == 0:
                h = 4
            else:
                h = int(MIN_H + (val / 100) * (MAX_H - MIN_H))
            # 바를 아래 정렬: 고정 높이 컨테이너 안에서 바닥에 붙임
            return ft.Column(
                controls=[
                    ft.Container(
                        width=22,
                        height=MAX_H,
                        content=ft.Column(
                            controls=[
                                ft.Container(expand=True),  # 위 빈공간
                                ft.Container(
                                    width=22, height=h,
                                    bgcolor=color if is_today
                                            else (color + "88" if val > 0 else BORDER),
                                    border_radius=4,
                                    shadow=ft.BoxShadow(
                                        blur_radius=4, color=color + "44",
                                        offset=ft.Offset(0, 2)
                                    ) if is_today else None,
                                ),
                            ],
                            spacing=0,
                        ),
                    ),
                    ft.Text(d, size=10,
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

        CHART_H = (ROW2_H - 10) // 2 - 20  # 차트 하나의 높이

        def _chart(title, avg, bars):
            return ft.Container(
                content=card(
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(title, size=13, color=TEXT_PRI, font_family=FONT),
                                    ft.Container(
                                        content=ft.Text(avg, size=11, color=ACCENT,
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
                    _chart("이번 주 집중도",    "평균 78점", focus_bars),
                    ft.Container(height=10),
                    _chart("이번 주 자세 점수", "평균 81점", posture_bars),
                ],
                spacing=0,
            ),
            height=ROW2_H, expand=2,
        )

        def _rank_row(medal, name, val, color):
            return ft.Row(
                controls=[
                    ft.Text(medal, size=13),
                    ft.Container(
                        content=ft.Text(name[0], size=10, color="#FFFFFF",
                                        font_family=FONT),
                        width=22, height=22, border_radius=11,
                        bgcolor=color, alignment=ft.Alignment(0, 0),
                    ),
                    ft.Text(name, size=12, color=TEXT_PRI,
                            font_family=FONT, expand=True),
                    ft.Text(val, size=12, color=color, font_family=FONT),
                ],
                spacing=7,
            )

        rank_card = ft.Container(
            content=card(
                ft.Column(
                    controls=[
                        ft.Text("친구 랭킹", size=13, color=TEXT_PRI, font_family=FONT),
                        ft.Container(height=4),
                        ft.Text("⏱ 집중 순위", size=11, color=TEXT_SEC, font_family=FONT),
                        ft.Container(height=2),
                        _rank_row("🥇", "김철수", "4h 32m", ACCENT),
                        _rank_row("🥈", "이영희", "3h 55m", PURPLE),
                        _rank_row("🥉", "나",    "3h 20m", DANGER),
                        ft.Divider(color=BORDER, height=8),
                        ft.Text("🧘 자세 순위", size=11, color=TEXT_SEC, font_family=FONT),
                        ft.Container(height=2),
                        _rank_row("🥇", "한소희", "91점", "#34D399"),
                        _rank_row("🥈", "김철수", "88점", ACCENT),
                        _rank_row("🥉", "이영희", "85점", PURPLE),
                        ft.Container(expand=True),
                        ghost_btn("전체 보기",
                                  on_click=lambda _: self.navigate("ranking"),
                                  icon="\ue5c8"),
                    ],
                    spacing=4,
                ),
                padding=14,
            ),
            height=ROW2_H, expand=1,
        )

        row2 = ft.Row(
            controls=[
                charts_col,
                ft.Container(width=10),
                rank_card,
            ],
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    header,
                    ft.Container(height=10),
                    row1,
                    ft.Container(height=10),
                    row2,
                ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
            padding=ft.padding.only(left=22, top=14, right=22, bottom=14),
            bgcolor=BG_BASE,
        )
