import flet as ft
from components.ui import card, ghost_btn

BG_DARK = "#080B10"
BG_CARD = "#0D1117"
BG_CARD2 = "#131920"
ACCENT = "#00E5CC"
ACCENT2 = "#FF6B6B"
PURPLE = "#A78BFA"
YELLOW = "#F59E0B"
TEXT_PRIMARY = "#E8EDF3"
TEXT_MUTED = "#4A5568"
BORDER = "#1A2332"

FRIENDS = [
    {"name": "김철수",  "sessions": 18, "focus": "4h 32m", "streak": 12, "score": 97,  "avatar": "#00E5CC", "me": False},
    {"name": "이영희",  "sessions": 16, "focus": "3h 55m", "streak": 9,  "score": 89,  "avatar": "#A78BFA", "me": False},
    {"name": "나 (박지수)", "sessions": 14, "focus": "3h 20m", "streak": 5, "score": 82, "avatar": "#FF6B6B", "me": True},
    {"name": "최민준",  "sessions": 12, "focus": "2h 50m", "streak": 3,  "score": 75,  "avatar": "#F59E0B", "me": False},
    {"name": "한소희",  "sessions": 10, "focus": "2h 10m", "streak": 7,  "score": 68,  "avatar": "#34D399", "me": False},
    {"name": "정우성",  "sessions": 8,  "focus": "1h 45m", "streak": 2,  "score": 55,  "avatar": "#60A5FA", "me": False},
]

MEDALS = ["🥇", "🥈", "🥉"]


class RankingView:
    def __init__(self, page: ft.Page):
        self.page = page

    def _podium(self) -> ft.Row:
        top3 = FRIENDS[:3]
        podium_heights = [80, 110, 60]  # 2nd, 1st, 3rd
        orders = [1, 0, 2]  # visual order: 2nd, 1st, 3rd

        cols = []
        for visual_pos, rank_idx in enumerate(orders):
            f = top3[rank_idx]
            h = podium_heights[visual_pos]
            medal = MEDALS[rank_idx]
            bar_color = [PURPLE, ACCENT, ACCENT2][rank_idx]

            cols.append(
                ft.Column(
                    controls=[
                        ft.Text(medal, size=28, text_align=ft.TextAlign.CENTER),
                        ft.Container(
                            content=ft.Text(f["name"][0], size=18,
                                            color="#080B10", font_family="Pretendard",
                                            weight=ft.FontWeight.W_900),
                            width=48, height=48,
                            border_radius=24,
                            bgcolor=f["avatar"],
                            alignment=ft.Alignment(0, 0),
                        ),
                        ft.Text(f["name"], size=12, color=TEXT_PRIMARY,
                                font_family="Pretendard",
                                text_align=ft.TextAlign.CENTER,
                                weight=ft.FontWeight.W_600),
                        ft.Text(f["focus"], size=11, color=TEXT_MUTED,
                                font_family="JetBrains",
                                text_align=ft.TextAlign.CENTER),
                        ft.Container(
                            width=80, height=h,
                            bgcolor=bar_color + "30",
                            border=ft.border.all(1, bar_color + "60"),
                            border_radius=ft.BorderRadius(8, 8, 0, 0),
                            alignment=ft.Alignment(0, 0),
                            content=ft.Text(f"#{rank_idx + 1}", size=16,
                                            color=bar_color,
                                            weight=ft.FontWeight.W_900,
                                            font_family="Pretendard"),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=6,
                )
            )

        return ft.Row(
            controls=cols,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
            vertical_alignment=ft.CrossAxisAlignment.END,
        )

    def _rank_row(self, rank: int, friend: dict) -> ft.Container:
        is_me = friend["me"]
        medal = MEDALS[rank - 1] if rank <= 3 else f"#{rank}"

        bar_w_pct = friend["score"] / 100

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(medal, size=14 if rank <= 3 else 12,
                                                color=ACCENT if is_me else TEXT_MUTED,
                                                font_family="Pretendard",
                                                weight=ft.FontWeight.W_700),
                                width=36,
                                alignment=ft.Alignment(0, 0),
                            ),
                            ft.Container(
                                content=ft.Text(friend["name"][0], size=13,
                                                color="#080B10", font_family="Pretendard"),
                                width=32, height=32,
                                border_radius=16,
                                bgcolor=friend["avatar"],
                                alignment=ft.Alignment(0, 0),
                            ),
                            ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Text(friend["name"], size=13,
                                                    color=ACCENT if is_me else TEXT_PRIMARY,
                                                    font_family="Pretendard",
                                                    weight=ft.FontWeight.W_600 if is_me else ft.FontWeight.W_400),
                                            *(
                                                [ft.Container(
                                                    content=ft.Text("나", size=9, color="#080B10",
                                                                    font_family="Pretendard"),
                                                    bgcolor=ACCENT, border_radius=4,
                                                    padding=ft.padding.only(left=5, top=1, right=5, bottom=1),
                                                )]
                                                if is_me else []
                                            ),
                                        ],
                                        spacing=6,
                                    ),
                                    ft.Row(
                                        controls=[
                                            ft.Text(f"🔥 {friend['streak']}일", size=11,
                                                    color=TEXT_MUTED, font_family="Pretendard"),
                                            ft.Text(f"세션 {friend['sessions']}회", size=11,
                                                    color=TEXT_MUTED, font_family="Pretendard"),
                                        ],
                                        spacing=10,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.Column(
                                controls=[
                                    ft.Text(friend["focus"], size=14,
                                            color=ACCENT if is_me else TEXT_PRIMARY,
                                            font_family="JetBrains",
                                            weight=ft.FontWeight.W_700),
                                    ft.Text("집중시간", size=10, color=TEXT_MUTED,
                                            font_family="Pretendard"),
                                ],
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                                spacing=2,
                            ),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(
                        content=ft.ProgressBar(
                            value=bar_w_pct, color=ACCENT if is_me else "#1E3A3A",
                            bgcolor="#111820", height=4, border_radius=2,
                        ),
                        padding=ft.padding.only(left=36, top=0, right=0, bottom=0),
                    ),
                ],
                spacing=8,
            ),
            bgcolor=ACCENT + "08" if is_me else BG_CARD,
            border_radius=14,
            padding=ft.padding.only(left=14, top=12, right=14, bottom=12),
            border=ft.border.all(1, ACCENT + "40" if is_me else BORDER),
        )

    def build(self) -> ft.Container:
        my_rank = next((i + 1 for i, f in enumerate(FRIENDS) if f["me"]), None)
        my_data = next(f for f in FRIENDS if f["me"])

        my_card = card(
            ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(my_data["name"][0], size=22,
                                        color="#080B10", font_family="Pretendard",
                                        weight=ft.FontWeight.W_900),
                        width=56, height=56,
                        border_radius=28,
                        bgcolor=my_data["avatar"],
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(my_data["name"], size=16, weight=ft.FontWeight.W_700,
                                    color=TEXT_PRIMARY, font_family="Pretendard"),
                            ft.Text(f"현재 #{my_rank}위", size=13, color=ACCENT,
                                    font_family="Pretendard"),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(my_data["focus"], size=22, weight=ft.FontWeight.W_900,
                                    color=ACCENT, font_family="JetBrains"),
                            ft.Text("오늘 집중 시간", size=11, color=TEXT_MUTED,
                                    font_family="Pretendard"),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                        spacing=2,
                    ),
                ],
                spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.padding.only(left=20, top=16, right=20, bottom=16),
        )

        podium_card = card(
            ft.Column(
                controls=[
                    ft.Text("이번 주 TOP 3", size=15, weight=ft.FontWeight.W_700,
                            color=TEXT_PRIMARY, font_family="Pretendard",
                            text_align=ft.TextAlign.CENTER),
                    ft.Container(height=16),
                    self._podium(),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=24,
        )

        rank_list = ft.Column(
            controls=[self._rank_row(i + 1, f) for i, f in enumerate(FRIENDS)],
            spacing=8,
        )

        # Period tabs
        period_row = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(label, size=12, weight=ft.FontWeight.W_600,
                                    color=ACCENT if i == 0 else TEXT_MUTED,
                                    font_family="Pretendard"),
                    bgcolor=ACCENT + "20" if i == 0 else "transparent",
                    border=ft.border.all(1, ACCENT if i == 0 else BORDER),
                    border_radius=8,
                    padding=ft.padding.only(left=16, top=7, right=16, bottom=7),
                )
                for i, label in enumerate(["오늘", "이번 주", "이번 달", "전체"])
            ],
            spacing=8,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("친구 랭킹", size=26, weight=ft.FontWeight.W_900,
                                            color=TEXT_PRIMARY, font_family="Pretendard"),
                                    ft.Text("오늘 누가 가장 집중했을까요?",
                                            size=13, color=TEXT_MUTED, font_family="Pretendard"),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ghost_btn("친구 추가", icon="\ue7fe"),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=16),
                    my_card,
                    ft.Container(height=12),
                    ft.Row(
                        controls=[
                            ft.Container(content=podium_card, expand=1),
                            ft.Container(width=16),
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        period_row,
                                        ft.Container(height=12),
                                        rank_list,
                                    ],
                                    spacing=0,
                                ),
                                expand=2,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            expand=True,
            padding=ft.padding.only(left=28, top=24, right=28, bottom=24),
            bgcolor="#080B10",
        )
