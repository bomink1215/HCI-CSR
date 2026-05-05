import flet as ft
import json, os
from components.ui import card, ghost_btn

BG_BASE   = "#FFFFFF"
BG_CARD   = "#F4F6F8"
BG_CARD2  = "#EAECEF"
ACCENT    = "#00C9A7"
ACCENT_LT = "#D6F5EF"
DANGER    = "#FF5C5C"
WARNING   = "#FFB347"
PURPLE    = "#9B8FFF"
TEXT_PRI  = "#1A1D23"
TEXT_SEC  = "#5A6375"
TEXT_MUT  = "#9DA8B7"
BORDER    = "#E2E6EC"

# ── 로컬 JSON 데이터 구조 ───────────────────────────────────────
DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "friends.json")

DEFAULT_FRIENDS = [
    {"name": "김철수",    "sessions": 18, "focus_min": 272, "streak": 12, "score": 97,  "posture_avg": 91, "avatar": "#00C9A7", "me": False},
    {"name": "이영희",    "sessions": 16, "focus_min": 235, "streak": 9,  "score": 89,  "posture_avg": 85, "avatar": "#9B8FFF", "me": False},
    {"name": "나 (박지수)", "sessions": 14, "focus_min": 200, "streak": 5, "score": 82, "posture_avg": 78, "avatar": "#FF5C5C", "me": True},
    {"name": "최민준",    "sessions": 12, "focus_min": 170, "streak": 3,  "score": 75,  "posture_avg": 72, "avatar": "#FFB347", "me": False},
    {"name": "한소희",    "sessions": 10, "focus_min": 130, "streak": 7,  "score": 68,  "posture_avg": 88, "avatar": "#34D399", "me": False},
    {"name": "정우성",    "sessions": 8,  "focus_min": 105, "streak": 2,  "score": 55,  "posture_avg": 60, "avatar": "#60A5FA", "me": False},
]

MEDALS = ["🥇", "🥈", "🥉"]


def _fmt_min(minutes: int) -> str:
    h = minutes // 60
    m = minutes % 60
    if h > 0:
        return f"{h}h {m:02d}m"
    return f"{m}m"


def _load_friends() -> list:
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    # 없으면 기본값 저장
    _save_friends(DEFAULT_FRIENDS)
    return DEFAULT_FRIENDS


def _save_friends(friends: list):
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(friends, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def add_focus_session(minutes: int = 25):
    """뽀모도로 완료 시 호출 → 내 데이터에 세션 추가"""
    friends = _load_friends()
    for f in friends:
        if f.get("me"):
            f["sessions"] = f.get("sessions", 0) + 1
            f["focus_min"] = f.get("focus_min", 0) + minutes
            f["score"] = min(100, f.get("score", 0) + 2)
            break
    # 점수 기준 재정렬
    friends.sort(key=lambda x: x["score"], reverse=True)
    _save_friends(friends)


class RankingView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.friends = _load_friends()
        self.period = "오늘"

    def _reload(self):
        self.friends = _load_friends()

    def _podium(self) -> ft.Row:
        top3 = self.friends[:3]
        visual_order = [1, 0, 2]  # 2등, 1등, 3등 시각 순서
        heights = [70, 100, 50]
        rank_colors = [PURPLE, ACCENT, DANGER]

        cols = []
        for vi, ri in enumerate(visual_order):
            if ri >= len(top3):
                continue
            f = top3[ri]
            medal = MEDALS[ri]
            bar_color = rank_colors[ri]
            h = heights[vi]

            cols.append(
                ft.Column(
                    controls=[
                        ft.Text(medal, size=26, text_align=ft.TextAlign.CENTER),
                        ft.Container(
                            content=ft.Text(f["name"][0], size=16,
                                            color="#FFFFFF", font_family="DOSSaemmul",
                                            weight=ft.FontWeight.W_400),
                            width=44, height=44,
                            border_radius=22,
                            bgcolor=f["avatar"],
                            alignment=ft.Alignment(0, 0),
                            shadow=ft.BoxShadow(blur_radius=8, color=f["avatar"] + "55",
                                                offset=ft.Offset(0, 2)),
                        ),
                        ft.Text(f["name"].split("(")[0].strip(), size=11, color=TEXT_PRI,
                                font_family="DOSSaemmul",
                                text_align=ft.TextAlign.CENTER,
                                weight=ft.FontWeight.W_400),
                        ft.Text(_fmt_min(f["focus_min"]), size=10, color=TEXT_MUT,
                                font_family="DOSSaemmul",
                                text_align=ft.TextAlign.CENTER),
                        ft.Container(
                            width=72, height=h,
                            bgcolor=bar_color + "18",
                            border=ft.border.all(1.5, bar_color + "50"),
                            border_radius=ft.BorderRadius(8, 8, 0, 0),
                            alignment=ft.Alignment(0, 0),
                            content=ft.Text(f"#{ri + 1}", size=15,
                                            color=bar_color,
                                            weight=ft.FontWeight.W_400,
                                            font_family="DOSSaemmul"),
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
        focus_pct   = min(friend["focus_min"] / 300, 1.0)
        posture_avg = friend.get("posture_avg", 0)
        posture_pct = posture_avg / 100
        posture_color = (ACCENT if posture_avg >= 70 else (WARNING if posture_avg >= 50 else DANGER))

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.Text(medal, size=13 if rank <= 3 else 11,
                                                color=ACCENT if is_me else TEXT_MUT,
                                                font_family="DOSSaemmul",
                                                weight=ft.FontWeight.W_400),
                                width=34,
                                alignment=ft.Alignment(0, 0),
                            ),
                            ft.Container(
                                content=ft.Text(friend["name"][0], size=12,
                                                color="#FFFFFF", font_family="DOSSaemmul"),
                                width=30, height=30,
                                border_radius=15,
                                bgcolor=friend["avatar"],
                                alignment=ft.Alignment(0, 0),
                            ),
                            ft.Column(
                                controls=[
                                    ft.Row(
                                        controls=[
                                            ft.Text(friend["name"], size=13,
                                                    color=ACCENT if is_me else TEXT_PRI,
                                                    font_family="DOSSaemmul",
                                                    weight=ft.FontWeight.W_400),
                                            *(
                                                [ft.Container(
                                                    content=ft.Text("나", size=9, color="#FFFFFF",
                                                                    font_family="DOSSaemmul"),
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
                                                    color=TEXT_MUT, font_family="DOSSaemmul"),
                                            ft.Text(f"세션 {friend['sessions']}회", size=11,
                                                    color=TEXT_MUT, font_family="DOSSaemmul"),
                                        ],
                                        spacing=10,
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            # 집중시간 + 자세점수 나란히
                            ft.Row(
                                controls=[
                                    ft.Column(
                                        controls=[
                                            ft.Text(_fmt_min(friend["focus_min"]), size=12,
                                                    color=ACCENT if is_me else TEXT_PRI,
                                                    font_family="DOSSaemmul",
                                                    weight=ft.FontWeight.W_400),
                                            ft.Text("집중", size=10, color=TEXT_MUT,
                                                    font_family="DOSSaemmul"),
                                        ],
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        spacing=1,
                                    ),
                                    ft.Container(width=1, height=28, bgcolor=BORDER),
                                    ft.Column(
                                        controls=[
                                            ft.Text(f"{posture_avg}점", size=12,
                                                    color=posture_color,
                                                    font_family="DOSSaemmul",
                                                    weight=ft.FontWeight.W_400),
                                            ft.Text("자세", size=10, color=TEXT_MUT,
                                                    font_family="DOSSaemmul"),
                                        ],
                                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                        spacing=1,
                                    ),
                                ],
                                spacing=10,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    # 집중 + 자세 이중 바
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Container(width=34),
                                    ft.Text("집중", size=9, color=TEXT_MUT,
                                            font_family="DOSSaemmul", width=22),
                                    ft.Container(
                                        content=ft.ProgressBar(
                                            value=focus_pct,
                                            color=ACCENT if is_me else BG_CARD2,
                                            bgcolor=BORDER, height=4, border_radius=2,
                                        ),
                                        expand=True,
                                    ),
                                ],
                                spacing=6,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Row(
                                controls=[
                                    ft.Container(width=34),
                                    ft.Text("자세", size=9, color=TEXT_MUT,
                                            font_family="DOSSaemmul", width=22),
                                    ft.Container(
                                        content=ft.ProgressBar(
                                            value=posture_pct,
                                            color=posture_color,
                                            bgcolor=BORDER, height=4, border_radius=2,
                                        ),
                                        expand=True,
                                    ),
                                ],
                                spacing=6,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        spacing=4,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=ACCENT_LT if is_me else BG_CARD,
            border_radius=14,
            padding=ft.padding.only(left=14, top=12, right=14, bottom=12),
            border=ft.border.all(1.5, ACCENT + "50" if is_me else BORDER),
            shadow=ft.BoxShadow(blur_radius=4, color="#00000008",
                                offset=ft.Offset(0, 1)),
        )

    def build(self) -> ft.Container:
        self._reload()
        my_rank = next((i + 1 for i, f in enumerate(self.friends) if f["me"]), None)
        my_data = next(f for f in self.friends if f["me"])

        my_card = card(
            ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(my_data["name"][0], size=20,
                                        color="#FFFFFF", font_family="DOSSaemmul",
                                        weight=ft.FontWeight.W_400),
                        width=52, height=52,
                        border_radius=26,
                        bgcolor=my_data["avatar"],
                        alignment=ft.Alignment(0, 0),
                        shadow=ft.BoxShadow(blur_radius=10, color=my_data["avatar"] + "55",
                                            offset=ft.Offset(0, 3)),
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(my_data["name"], size=15, weight=ft.FontWeight.W_400,
                                    color=TEXT_PRI, font_family="DOSSaemmul"),
                            ft.Text(f"현재 #{my_rank}위", size=13, color=ACCENT,
                                    font_family="DOSSaemmul"),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(_fmt_min(my_data["focus_min"]), size=20,
                                    weight=ft.FontWeight.W_400,
                                    color=ACCENT, font_family="DOSSaemmul"),
                            ft.Text("오늘 집중 시간", size=11, color=TEXT_MUT,
                                    font_family="DOSSaemmul"),
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

        podium_card = card(
            ft.Column(
                controls=[
                    ft.Text("이번 주 TOP 3", size=14, weight=ft.FontWeight.W_400,
                            color=TEXT_PRI, font_family="DOSSaemmul",
                            text_align=ft.TextAlign.CENTER),
                    ft.Container(height=14),
                    self._podium(),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20,
        )

        rank_list = ft.Column(
            controls=[self._rank_row(i + 1, f) for i, f in enumerate(self.friends)],
            spacing=8,
        )

        period_tabs = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(label, size=12, weight=ft.FontWeight.W_400,
                                    color=ACCENT if label == self.period else TEXT_MUT,
                                    font_family="DOSSaemmul"),
                    bgcolor=ACCENT_LT if label == self.period else BG_CARD,
                    border=ft.border.all(1.5, ACCENT if label == self.period else BORDER),
                    border_radius=8,
                    padding=ft.padding.only(left=14, top=6, right=14, bottom=6),
                )
                for label in ["오늘", "이번 주", "이번 달", "전체"]
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
                                    ft.Text("친구 랭킹", size=26, weight=ft.FontWeight.W_400,
                                            color=TEXT_PRI, font_family="DOSSaemmul"),
                                    ft.Text("오늘 누가 가장 집중했을까요?",
                                            size=13, color=TEXT_SEC, font_family="DOSSaemmul"),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ghost_btn("친구 추가", icon="\ue7fe"),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(height=14),
                    my_card,
                    ft.Container(height=10),
                    ft.Row(
                        controls=[
                            ft.Container(content=podium_card, expand=1),
                            ft.Container(width=16),
                            ft.Container(
                                content=ft.Column(
                                    controls=[
                                        period_tabs,
                                        ft.Container(height=10),
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
            bgcolor=BG_BASE,
        )
