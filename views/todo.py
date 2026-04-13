import flet as ft
from components.ui import card, accent_btn

BG_DARK = "#080B10"
BG_CARD = "#0D1117"
BG_CARD2 = "#131920"
ACCENT = "#00E5CC"
ACCENT2 = "#FF6B6B"
PURPLE = "#A78BFA"
TEXT_PRIMARY = "#E8EDF3"
TEXT_MUTED = "#4A5568"
BORDER = "#1A2332"

PRIORITY_COLORS = {
    "높음": ACCENT2,
    "보통": "#FFA500",
    "낮음": ACCENT,
}
CATEGORY_COLORS = {
    "업무": ACCENT,
    "개인": PURPLE,
    "건강": "#34D399",
    "학습": "#FFA500",
}


class TodoView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.tasks = [
            {"title": "프로젝트 기획서 작성", "done": True,  "priority": "높음", "cat": "업무",  "note": "3페이지 분량"},
            {"title": "팀 미팅 준비",         "done": True,  "priority": "높음", "cat": "업무",  "note": ""},
            {"title": "코드 리뷰",             "done": False, "priority": "보통", "cat": "업무",  "note": "PR #42"},
            {"title": "문서화 작업",           "done": False, "priority": "낮음", "cat": "업무",  "note": ""},
            {"title": "운동 30분",             "done": False, "priority": "보통", "cat": "건강",  "note": "스트레칭 포함"},
            {"title": "독서 20페이지",         "done": False, "priority": "낮음", "cat": "학습",  "note": ""},
        ]
        self.filter_cat = "전체"
        self.new_text = ft.TextField(
            hint_text="새 할 일을 입력하세요...",
            bgcolor=BG_CARD2,
            border_color=BORDER,
            focused_border_color=ACCENT,
            color=TEXT_PRIMARY,
            hint_style=ft.TextStyle(color=TEXT_MUTED),
            cursor_color=ACCENT,
            border_radius=10,
            expand=True,
        )
        self.task_col_ref = ft.Ref()
        self.stats_ref = ft.Ref()

    def _task_tile(self, task: dict, idx: int) -> ft.Container:
        done = task["done"]
        pcolor = PRIORITY_COLORS.get(task["priority"], ACCENT)
        ccolor = CATEGORY_COLORS.get(task["cat"], ACCENT)

        def toggle(_):
            task["done"] = not task["done"]
            self._refresh()

        def delete(_):
            self.tasks.pop(idx)
            self._refresh()

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            "\ue876" if done else "",
                            font_family="Material Icons",
                            size=14,
                            color=ACCENT if done else "transparent",
                        ),
                        width=24, height=24,
                        border_radius=6,
                        border=ft.border.all(1, ACCENT if done else "#2A3A4C"),
                        bgcolor="#0A1F1C" if done else "transparent",
                        alignment=ft.Alignment(0, 0),
                        on_click=toggle,
                    ),
                    ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        task["title"],
                                        size=14,
                                        color=TEXT_MUTED if done else TEXT_PRIMARY,
                                        font_family="Pretendard",
                                        weight=ft.FontWeight.W_500,
                                        expand=True,
                                        spans=[
                                            ft.TextSpan(
                                                style=ft.TextStyle(
                                                    decoration=ft.TextDecoration.LINE_THROUGH
                                                )
                                            )
                                        ] if done else [],
                                    ),
                                ],
                            ),
                            ft.Row(
                                controls=[
                                    ft.Container(
                                        content=ft.Text(task["cat"], size=10, color=ccolor,
                                                        font_family="Pretendard"),
                                        bgcolor=ccolor + "20",
                                        border_radius=4,
                                        padding=ft.padding.only(left=6, top=2, right=6, bottom=2),
                                    ),
                                    ft.Container(
                                        content=ft.Text(task["priority"], size=10,
                                                        color=pcolor, font_family="Pretendard"),
                                        bgcolor=pcolor + "20",
                                        border_radius=4,
                                        padding=ft.padding.only(left=6, top=2, right=6, bottom=2),
                                    ),
                                    *(
                                        [ft.Text(task["note"], size=11, color=TEXT_MUTED,
                                                 font_family="Pretendard")]
                                        if task["note"] else []
                                    ),
                                ],
                                spacing=6,
                            ),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.Text("\ue872", font_family="Material Icons",
                                       size=16, color=TEXT_MUTED),
                        on_click=delete,
                        padding=4,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=BG_CARD,
            border_radius=12,
            padding=ft.padding.only(left=16, top=12, right=16, bottom=12),
            border=ft.border.all(1, BORDER),
            animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
        )

    def _refresh(self):
        if self.task_col_ref.current:
            tasks = [t for t in self.tasks
                     if self.filter_cat == "전체" or t["cat"] == self.filter_cat]
            self.task_col_ref.current.controls = [
                self._task_tile(t, self.tasks.index(t)) for t in tasks
            ]
        self.page.update()

    def _add_task(self, _):
        text = self.new_text.value.strip()
        if not text:
            return
        self.tasks.append({
            "title": text, "done": False,
            "priority": "보통", "cat": "업무", "note": "",
        })
        self.new_text.value = ""
        self._refresh()

    def _filter_btn(self, label: str) -> ft.Container:
        is_active = self.filter_cat == label
        color = CATEGORY_COLORS.get(label, ACCENT) if label != "전체" else ACCENT

        def on_click(_):
            self.filter_cat = label
            self._refresh()

        return ft.Container(
            content=ft.Text(label, size=12, weight=ft.FontWeight.W_600,
                            color=color if is_active else TEXT_MUTED,
                            font_family="Pretendard"),
            bgcolor=color + "20" if is_active else "transparent",
            border=ft.border.all(1, color if is_active else BORDER),
            border_radius=8,
            padding=ft.padding.only(left=14, top=6, right=14, bottom=6),
            on_click=on_click,
        )

    def build(self) -> ft.Container:
        done_count = sum(1 for t in self.tasks if t["done"])
        total_count = len(self.tasks)

        # Stats bar
        stats_bar = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(str(total_count), size=28, weight=ft.FontWeight.W_900,
                                color=TEXT_PRIMARY, font_family="Pretendard"),
                        ft.Text("전체", size=11, color=TEXT_MUTED, font_family="Pretendard"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Column(
                    controls=[
                        ft.Text(str(done_count), size=28, weight=ft.FontWeight.W_900,
                                color=ACCENT, font_family="Pretendard"),
                        ft.Text("완료", size=11, color=TEXT_MUTED, font_family="Pretendard"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Column(
                    controls=[
                        ft.Text(str(total_count - done_count), size=28,
                                weight=ft.FontWeight.W_900,
                                color=ACCENT2, font_family="Pretendard"),
                        ft.Text("남음", size=11, color=TEXT_MUTED, font_family="Pretendard"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(expand=True),
                ft.Column(
                    controls=[
                        ft.Text(f"{int(done_count / total_count * 100) if total_count else 0}%",
                                size=28, weight=ft.FontWeight.W_900,
                                color="#A78BFA", font_family="Pretendard"),
                        ft.Text("달성률", size=11, color=TEXT_MUTED, font_family="Pretendard"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=32,
        )

        progress = ft.ProgressBar(
            value=done_count / total_count if total_count else 0,
            color=ACCENT, bgcolor="#1A2332", height=6, border_radius=3,
        )

        # Filter chips
        cats = ["전체", "업무", "개인", "건강", "학습"]
        filter_row = ft.Row(
            controls=[self._filter_btn(c) for c in cats],
            spacing=8,
        )

        # Add input
        add_row = ft.Row(
            controls=[
                self.new_text,
                ft.Container(
                    content=ft.Text("\ue145", font_family="Material Icons",
                                   size=20, color="#080B10"),
                    bgcolor=ACCENT,
                    border_radius=10,
                    width=44, height=44,
                    alignment=ft.Alignment(0, 0),
                    on_click=self._add_task,
                ),
            ],
            spacing=10,
        )

        tasks_to_show = [t for t in self.tasks
                         if self.filter_cat == "전체" or t["cat"] == self.filter_cat]

        task_list = ft.Column(
            ref=self.task_col_ref,
            controls=[self._task_tile(t, self.tasks.index(t)) for t in tasks_to_show],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("할 일 메모", size=26, weight=ft.FontWeight.W_900,
                                            color=TEXT_PRIMARY, font_family="Pretendard"),
                                    ft.Text("오늘 할 일을 관리해보세요",
                                            size=13, color=TEXT_MUTED, font_family="Pretendard"),
                                ],
                                spacing=2,
                            ),
                        ],
                    ),
                    ft.Container(height=16),
                    card(
                        ft.Column(
                            controls=[stats_bar, ft.Container(height=10), progress],
                            spacing=0,
                        ),
                        padding=ft.padding.only(left=20, top=16, right=20, bottom=16),
                    ),
                    ft.Container(height=12),
                    add_row,
                    ft.Container(height=8),
                    filter_row,
                    ft.Container(height=12),
                    task_list,
                ],
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
            expand=True,
            padding=ft.padding.only(left=28, top=24, right=28, bottom=24),
            bgcolor="#080B10",
        )
