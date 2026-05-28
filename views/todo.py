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
    "High":   DANGER,
    "Medium": WARNING,
    "Low":    ACCENT,
}
CATEGORY_COLORS = {
    "Work":    ACCENT,
    "Personal": PURPLE,
    "Health":  "#34D399",
    "Study":   WARNING,
}


class TodoView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.tasks = [
            {"title": "Write project proposal", "done": True,  "priority": "High",   "cat": "Work",
             "note": "3 pages",     "due": "2025-04-15"},
            {"title": "Prepare team meeting",   "done": True,  "priority": "High",   "cat": "Work",
             "note": "",            "due": "2025-04-14"},
            {"title": "Code review",            "done": False, "priority": "Medium", "cat": "Work",
             "note": "PR #42",      "due": "2025-04-16"},
            {"title": "Documentation work",     "done": False, "priority": "Low",    "cat": "Work",
             "note": "",            "due": ""},
            {"title": "Exercise 30 min",        "done": False, "priority": "Medium", "cat": "Health",
             "note": "Incl. stretch", "due": "2025-04-14"},
            {"title": "Read 20 pages",          "done": False, "priority": "Low",    "cat": "Study",
             "note": "",            "due": ""},
        ]
        self.filter_cat = "All"
        self.new_text = ft.TextField(
            hint_text="Enter a new task...",
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
                label = f"D+{-delta} overdue"
            elif delta == 0:
                color = WARNING
                label = "Due today"
            elif delta <= 3:
                color = WARNING
                label = f"D-{delta}"
            else:
                color = TEXT_MUT
                label = f"D-{delta}"
            return ft.Container(
                content=ft.Text(label, size=10, color=color, font_family="DOSSaemmul"),
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

        due_chip = self._due_label(task.get("due", ""))
        chips = [
            ft.Container(
                content=ft.Text(task["cat"], size=10, color=ccolor,
                                font_family="DOSSaemmul"),
                bgcolor=ccolor + "18",
                border_radius=4,
                padding=ft.padding.only(left=6, top=2, right=6, bottom=2),
            ),
            ft.Container(
                content=ft.Text(task["priority"], size=10, color=pcolor,
                                font_family="DOSSaemmul"),
                bgcolor=pcolor + "18",
                border_radius=4,
                padding=ft.padding.only(left=6, top=2, right=6, bottom=2),
                on_click=change_priority,
                tooltip="Click to change priority",
            ),
        ]
        if due_chip:
            chips.append(due_chip)
        if task["note"]:
            chips.append(ft.Text(task["note"], size=11, color=TEXT_MUT,
                                 font_family="DOSSaemmul"))

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(ft.Icons.DONE, size=13, color="#FFFFFF" if done else "transparent"),
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
                                font_family="DOSSaemmul",
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
                        content=ft.Icon(ft.Icons.DELETE, size=16, color=TEXT_MUT),
                        on_click=delete,
                        padding=4,
                        tooltip="Delete",
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
                     if self.filter_cat == "All" or t["cat"] == self.filter_cat]
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
            "priority": "Medium", "cat": "Work", "note": "", "due": "",
        })
        self.new_text.value = ""
        self._refresh()

    def _filter_btn(self, label: str) -> ft.Container:
        is_active = self.filter_cat == label
        color = CATEGORY_COLORS.get(label, ACCENT) if label != "All" else ACCENT

        def on_click(_):
            self.filter_cat = label
            self._refresh()

        return ft.Container(
            content=ft.Text(label, size=12, weight=ft.FontWeight.W_400,
                            color=color if is_active else TEXT_MUT,
                            font_family="DOSSaemmul"),
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
                                color=TEXT_PRI, font_family="DOSSaemmul"),
                        ft.Text("Total", size=11, color=TEXT_MUT, font_family="DOSSaemmul"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Column(
                    controls=[
                        ft.Text(str(done_count), size=26, weight=ft.FontWeight.W_400,
                                color=ACCENT, font_family="DOSSaemmul"),
                        ft.Text("Done", size=11, color=TEXT_MUT, font_family="DOSSaemmul"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Column(
                    controls=[
                        ft.Text(str(total_count - done_count), size=26,
                                weight=ft.FontWeight.W_400, color=DANGER,
                                font_family="DOSSaemmul"),
                        ft.Text("Remaining", size=11, color=TEXT_MUT, font_family="DOSSaemmul"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(expand=True),
                ft.Column(
                    controls=[
                        ft.Text(f"{int(done_count / total_count * 100) if total_count else 0}%",
                                size=26, weight=ft.FontWeight.W_400,
                                color=PURPLE, font_family="DOSSaemmul"),
                        ft.Text("Completion", size=11, color=TEXT_MUT, font_family="DOSSaemmul"),
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

        cats = ["All", "Work", "Personal", "Health", "Study"]
        filter_row = ft.Row(controls=[self._filter_btn(c) for c in cats], spacing=8)

        add_row = ft.Row(
            controls=[
                self.new_text,
                ft.Container(
                    content=ft.Icon(ft.Icons.ADD, size=20, color="#FFFFFF"),
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
                         if self.filter_cat == "All" or t["cat"] == self.filter_cat]

        order = {"High": 0, "Medium": 1, "Low": 2}
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
                    ft.Text("To-Do", size=26, weight=ft.FontWeight.W_400,
                            color=TEXT_PRI, font_family="DOSSaemmul"),
                    ft.Text("Manage your tasks for today",
                            size=13, color=TEXT_SEC, font_family="DOSSaemmul"),
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
