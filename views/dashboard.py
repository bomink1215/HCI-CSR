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

ROW1_H = 250
ROW2_H = 340

POMO_LABELS = {"focus": "Focus Session", "rest": "Break Session"}
POMO_COLORS = {"focus": ACCENT,          "rest": PURPLE}


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

    def update_pomodoro(self, remaining: int, total: int, mode: str, running: bool):
        mins, secs = remaining // 60, remaining % 60
        time_str = f"{mins:02d}:{secs:02d}"
        color = POMO_COLORS.get(mode, ACCENT)
        if running:
            status = POMO_LABELS.get(mode, "")
        elif remaining == 0:
            status = "Session Complete"
        elif remaining < total:
            status = "Paused"
        else:
            status = "Session Ready"
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
                                ft.Text("Posture", size=11, color=TEXT_MUT,
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
            ("Write project proposal", True),
            ("Prepare team meeting", True),
            ("Code review", False),
            ("Documentation work", False),
        ]
        rows = []
        for label, done in tasks:
            rows.append(
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Icon(ft.Icons.DONE, size=11, color="#FFFFFF" if done else "transparent"),
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
            "Good morning! ☀️" if now.hour < 12
            else "Have you had lunch? 🍱" if now.hour < 18
            else "Great work today! 🌙"
        )

        # ── Header ───────────────────────────────────────────────────
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(greeting, size=12, color=TEXT_SEC, font_family=FONT),
                            ft.Text("Today's Overview", size=20, color=TEXT_PRI, font_family=FONT),
                            ft.Text(now.strftime("%B %d, %Y"),
                                    size=11, color=TEXT_MUT, font_family=FONT),
                        ],
                        spacing=2, expand=True,
                    ),
                    ft.Column(
                        controls=[
                            mascot_widget(44),
                            ft.Text("ZZOOK", size=9, color=TEXT_MUT,
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

        # ── Row 1: Posture / Tasks / Pomodoro ────────────────────────
        posture_card = ft.Container(
            content=card(
                ft.Column(
                    controls=[
                        ft.Container(expand=1),
                        ft.Row(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Text("Today's Posture", size=11,
                                                color=TEXT_MUT, font_family=FONT),
                                        ft.Container(height=6),
                                        ft.Text("Good 👍", size=20,
                                                color=ACCENT, font_family=FONT),
                                        ft.Container(height=4),
                                        ft.Text("Avg 78pts", size=12,
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
                        ft.Container(
                            content=ft.Row(
                                controls=[
                                    ft.Container(width=6, height=6,
                                                 bgcolor=ACCENT, border_radius=3),
                                    ft.Text("Live Detection On", size=10,
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
                                ft.Text("Today's Tasks", size=13,
                                        color=TEXT_PRI, font_family=FONT),
                                ft.Container(
                                    content=ft.Text("4 items", size=11, color=ACCENT,
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
                        ghost_btn("View All",
                                  on_click=lambda _: self.navigate("todo"),
                                  icon=ft.Icons.ARROW_FORWARD),
                    ],
                    spacing=0,
                ),
                padding=14,
            ),
            height=ROW1_H, expand=2,
        )

        RING_SZ = 110
        BTN_SZ  = 34

        play_btn = ft.Container(
            ref=self.pomo_play_btn_ref,
            content=ft.Icon(
                ref=self.pomo_play_icon_ref,
                icon=ft.Icons.PLAY_ARROW,
                size=20, color="#FFFFFF",
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
                        ft.Row(
                            controls=[
                                ft.Text("Pomodoro", size=13, color=TEXT_PRI, font_family=FONT),
                            ],
                            alignment=ft.MainAxisAlignment.START,
                        ),
                        ft.Container(height=2),
                        ft.Container(
                            content=ft.Stack(
                                controls=[
                                    ft.ProgressRing(
                                        ref=self.pomo_ring_ref,
                                        value=1.0, width=RING_SZ, height=RING_SZ,
                                        stroke_width=8, color=ACCENT, bgcolor=BORDER,
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
                            alignment=ft.Alignment(0, 0),
                        ),
                        ft.Container(expand=True),
                        ft.Text(
                            ref=self.pomo_status_ref,
                            value="Session Ready", size=11, color=TEXT_MUT,
                            font_family=FONT, text_align=ft.TextAlign.CENTER,
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
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=0,
                ),
                padding=14,
            ),
            on_click=lambda _: self.navigate("pomodoro"),
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

        # ── Row 2: Charts / Ranking ──────────────────────────────────
        days         = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        focus_vals   = [85, 92, 67, 88, 95, 40, 0]
        posture_vals = [78, 88, 70, 82, 91, 55, 0]
        MAX_H = 52
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

        CHART_H = (ROW2_H - 10) // 2 - 20

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
                    _chart("Weekly Focus Score",   "Avg 78pts", focus_bars),
                    ft.Container(height=10),
                    _chart("Weekly Posture Score", "Avg 81pts", posture_bars),
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
                        ft.Text("Friend Ranking", size=13, color=TEXT_PRI, font_family=FONT),
                        ft.Container(height=4),
                        ft.Text("⏱ Focus Ranking", size=11, color=TEXT_SEC, font_family=FONT),
                        ft.Container(height=2),
                        _rank_row("🥇", "Chulsoo K.", "4h 32m", ACCENT),
                        _rank_row("🥈", "Younghee L.", "3h 55m", PURPLE),
                        _rank_row("🥉", "Me",          "3h 20m", DANGER),
                        ft.Divider(color=BORDER, height=8),
                        ft.Text("🧘 Posture Ranking", size=11, color=TEXT_SEC, font_family=FONT),
                        ft.Container(height=2),
                        _rank_row("🥇", "Sohee H.", "91pts", "#34D399"),
                        _rank_row("🥈", "Chulsoo K.", "88pts", ACCENT),
                        _rank_row("🥉", "Younghee L.", "85pts", PURPLE),
                        ft.Container(expand=True),
                        ghost_btn("View All",
                                  on_click=lambda _: self.navigate("ranking"),
                                  icon=ft.Icons.ARROW_FORWARD),
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
