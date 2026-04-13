import flet as ft
from components.ui import card, accent_btn
from datetime import datetime, date

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

PRIORITY_COLORS = {
    "높음": DANGER,
    "보통": WARNING,
    "낮음": ACCENT,
}
CATEGORY_COLORS = {
    "업무": ACCENT,
    "개인": PURPLE,
    "건강": "#34D399",
    "학습": WARNING,
}


class TodoView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.tasks = [
            {"title": "프로젝트 기획서 작성", "done": True,  "priority": "높음", "cat": "업무",
             "note": "3페이지 분량", "due": "2025-04-15"},
            {"title": "팀 미팅 준비",         "done": True,  "priority": "높음", "cat": "업무",
             "note": "", "due": "2025-04-14"},
            {"title": "코드 리뷰",             "done": False, "priority": "보통", "cat": "업무",
             "note": "PR #42", "due": "2025-04-16"},
            {"title": "문서화 작업",           "done": False, "priority": "낮음", "cat": "업무",
             "note": "", "due": ""},
            {"title": "운동 30분",             "done": False, "priority": "보통", "cat": "건강",
             "note": "스트레칭 포함", "due": "2025-04-14"},
            {"title": "독서 20페이지",         "done": False, "priority": "낮음", "cat": "학습",
             "note": "", "due": ""},
        ]
        self.filter_cat = "전체"
        self.new_text = ft.TextField(
            hint_text="새 할 일을 입력하세요...",
            bgcolor=BG_CARD,
            border_color=BORDER,
            focused_border_color=ACCENT,
            color=TEXT_PRI,
            hint_style=ft.TextStyle(color=TEXT_MUT),
            cursor_color=ACCENT,
            border_radius=10,
            expand=True,
        )
        self.task_col_ref = ft.Ref()

    def _due_label(self, due_str: str) -> ft.Container | None:
        if not due_str:
            return None
        try:
            due = date.fromisoformat(due_str)
            today = date.today()
            delta = (due - today).days
            if delta < 0:
                color = DANGER
                label = f"D+{-delta} 지남"
            elif delta == 0:
                color = WARNING
                label = "오늘 마감"
            elif delta <= 3:
                color = WARNING
                label = f"D-{delta}"
            else:
                color = TEXT_MUT
                label = f"D-{delta}"
            return ft.Container(
                content=ft.Text(label, size=10, color=color, font_family="Galmuri"),
                bgcolor=color + "18",
                border_radius=4,
                padding=ft.padding.only(left=6, top=2, right=6, bottom=2),
            )
        except Exception:
            return None

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

        def change_priority(_):
            opts = list(PRIORITY_COLORS.keys())
            cur = opts.index(task["priority"]) if task["priority"] in opts else 0
            task["priority"] = opts[(cur + 1) % len(opts)]
            self._refresh()

        # 마감일 표시
        due_chip = self._due_label(task.get("due", ""))
        chips = [
            ft.Container(
                content=ft.Text(task["cat"], size=10, color=ccolor,
                                font_family="Galmuri"),
                bgcolor=ccolor + "18",
                border_radius=4,
                padding=ft.padding.only(left=6, top=2, right=6, bottom=2),
            ),
            ft.Container(
                content=ft.Text(task["priority"], size=10, color=pcolor,
                                font_family="Galmuri"),
                bgcolor=pcolor + "18",
                border_radius=4,
                padding=ft.padding.only(left=6, top=2, right=6, bottom=2),
                on_click=change_priority,  # 클릭으로 우선순위 순환
                tooltip="클릭해서 우선순위 변경",
            ),
        ]
        if due_chip:
            chips.append(due_chip)
        if task["note"]:
            chips.append(ft.Text(task["note"], size=11, color=TEXT_MUT,
                                 font_family="Galmuri"))

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            "\ue876" if done else "",
                            font_family="Material Icons",
                            size=13,
                            color="#FFFFFF" if done else "transparent",
                        ),
                        width=24, height=24,
                        border_radius=7,
                        border=ft.border.all(1.5, ACCENT if done else BORDER),
                        bgcolor=ACCENT if done else "transparent",
                        alignment=ft.Alignment(0, 0),
                        on_click=toggle,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                task["title"],
                                size=14,
                                color=TEXT_MUT if done else TEXT_PRI,
                                font_family="Galmuri",
                                weight=ft.FontWeight.W_400,
                                expand=True,
                                spans=[
                                    ft.TextSpan(
                                        style=ft.TextStyle(
                                            decoration=ft.TextDecoration.LINE_THROUGH
                                        )
                                    )
                                ] if done else [],
                            ),
                            ft.Row(controls=chips, spacing=6, wrap=True),
                        ],
                        spacing=4,
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.Text("\ue872", font_family="Material Icons",
                                       size=16, color=TEXT_MUT),
                        on_click=delete,
                        padding=4,
                        tooltip="삭제",
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=BG_CARD,
            border_radius=12,
            padding=ft.padding.only(left=16, top=12, right=14, bottom=12),
            border=ft.border.all(1, BORDER),
            shadow=ft.BoxShadow(blur_radius=4, color="#00000008", offset=ft.Offset(0, 1)),
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
            "priority": "보통", "cat": "업무", "note": "", "due": "",
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
            content=ft.Text(label, size=12, weight=ft.FontWeight.W_400,
                            color=color if is_active else TEXT_MUT,
                            font_family="Galmuri"),
            bgcolor=color + "18" if is_active else BG_CARD,
            border=ft.border.all(1.5, color if is_active else BORDER),
            border_radius=8,
            padding=ft.padding.only(left=14, top=6, right=14, bottom=6),
            on_click=on_click,
        )

    def build(self) -> ft.Container:
        done_count = sum(1 for t in self.tasks if t["done"])
        total_count = len(self.tasks)

        stats_bar = ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(str(total_count), size=26, weight=ft.FontWeight.W_400,
                                color=TEXT_PRI, font_family="Galmuri"),
                        ft.Text("전체", size=11, color=TEXT_MUT, font_family="Galmuri"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Column(
                    controls=[
                        ft.Text(str(done_count), size=26, weight=ft.FontWeight.W_400,
                                color=ACCENT, font_family="Galmuri"),
                        ft.Text("완료", size=11, color=TEXT_MUT, font_family="Galmuri"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Column(
                    controls=[
                        ft.Text(str(total_count - done_count), size=26,
                                weight=ft.FontWeight.W_400, color=DANGER,
                                font_family="Galmuri"),
                        ft.Text("남음", size=11, color=TEXT_MUT, font_family="Galmuri"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(expand=True),
                ft.Column(
                    controls=[
                        ft.Text(f"{int(done_count / total_count * 100) if total_count else 0}%",
                                size=26, weight=ft.FontWeight.W_400,
                                color=PURPLE, font_family="Galmuri"),
                        ft.Text("달성률", size=11, color=TEXT_MUT, font_family="Galmuri"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            spacing=32,
        )

        progress = ft.ProgressBar(
            value=done_count / total_count if total_count else 0,
            color=ACCENT, bgcolor=BORDER, height=6, border_radius=3,
        )

        cats = ["전체", "업무", "개인", "건강", "학습"]
        filter_row = ft.Row(controls=[self._filter_btn(c) for c in cats], spacing=8)

        add_row = ft.Row(
            controls=[
                self.new_text,
                ft.Container(
                    content=ft.Text("\ue145", font_family="Material Icons",
                                   size=20, color="#FFFFFF"),
                    bgcolor=ACCENT,
                    border_radius=10,
                    width=44, height=44,
                    alignment=ft.Alignment(0, 0),
                    on_click=self._add_task,
                    shadow=ft.BoxShadow(blur_radius=8, color=ACCENT + "44",
                                        offset=ft.Offset(0, 3)),
                ),
            ],
            spacing=10,
        )

        tasks_to_show = [t for t in self.tasks
                         if self.filter_cat == "전체" or t["cat"] == self.filter_cat]

        # 우선순위 정렬: 높음 → 보통 → 낮음, 완료 항목은 뒤로
        order = {"높음": 0, "보통": 1, "낮음": 2}
        tasks_to_show = sorted(tasks_to_show,
                               key=lambda t: (t["done"], order.get(t["priority"], 1)))

        task_list = ft.Column(
            ref=self.task_col_ref,
            controls=[self._task_tile(t, self.tasks.index(t)) for t in tasks_to_show],
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
        )

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("할 일 메모", size=26, weight=ft.FontWeight.W_400,
                            color=TEXT_PRI, font_family="Galmuri"),
                    ft.Text("오늘 할 일을 관리해보세요",
                            size=13, color=TEXT_SEC, font_family="Galmuri"),
                    ft.Container(height=14),
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
            bgcolor=BG_BASE,
        )
