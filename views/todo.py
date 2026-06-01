import flet as ft
import calendar as _cal
from components.ui import card
from datetime import date
from utils import todo_store

BG_BASE   = "#F0F9F8"
BG_CARD   = "#F4F6F8"
BG_CARD2  = "#EAECEF"
ACCENT    = "#7AC3B8"
ACCENT_LT = "#D6F5EF"
DANGER    = "#FF5C5C"
WARNING   = "#FFB347"
PINK      = "#F3A2BE"
TEXT_PRI  = "#1A1D23"
TEXT_SEC  = "#5A6375"
TEXT_MUT  = "#9DA8B7"
BORDER    = "#E2E6EC"

BLUE = "#60A5FA"

PRIORITY_COLORS = {
    "High":   DANGER,
    "Medium": WARNING,
    "Low":    BLUE,
}
CATEGORY_COLORS = {
    "Work":     BLUE,     # 파랑
    "Personal": ACCENT,   # 민트
    "Health":   WARNING,     # 노랑
    "Study":    PINK,  # 핑크
}
CATS       = ["Work", "Personal", "Health", "Study"]
PRIORITIES = ["High", "Medium", "Low"]


class TodoView:
    def __init__(self, page: ft.Page):
        self.page         = page
        self.new_cat      = "Work"
        self.new_priority = "Medium"

        self.new_text = ft.TextField(
            hint_text="What do you need to do?",
            bgcolor="transparent",
            border_color="transparent",
            focused_border_color="transparent",
            color=TEXT_PRI,
            hint_style=ft.TextStyle(color=TEXT_MUT, size=14),
            text_style=ft.TextStyle(color=TEXT_PRI, size=14),
            cursor_color=ACCENT,
            border_radius=0,
            expand=True,
            on_submit=self._add_task,
            content_padding=ft.padding.symmetric(horizontal=4, vertical=8),
        )

        self.due_field = ft.TextField(
            hint_text="MM-DD",
            hint_style=ft.TextStyle(color=TEXT_PRI, size=11, font_family="DOSSaemmul"),
            text_style=ft.TextStyle(color=TEXT_PRI, size=11, font_family="DOSSaemmul"),
            bgcolor="transparent",
            border_color="transparent",
            focused_border_color="transparent",
            cursor_color=ACCENT,
            border_radius=0,
            width=50,
            height=24,
            content_padding=ft.padding.symmetric(horizontal=2, vertical=0),
        )

        self.task_col_ref       = ft.Ref()
        self.cat_row_ref        = ft.Ref()
        self.priority_row_ref   = ft.Ref()
        self.stat_total_ref     = ft.Ref()
        self.stat_done_ref      = ft.Ref()
        self.stat_remaining_ref = ft.Ref()
        self.stat_pct_ref       = ft.Ref()
        self.progress_ref       = ft.Ref()

    # ── 달력 팝업 ────────────────────────────────────────────────────
    def _open_calendar(self, _=None):
        today = date.today()
        view  = {"year": today.year, "month": today.month}

        cal_col_ref  = ft.Ref()
        title_ref    = ft.Ref()
        dlg          = ft.Ref()

        DAY_HEADERS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

        def build_grid():
            weeks = _cal.monthcalendar(view["year"], view["month"])
            rows  = [
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(h, size=9, color=TEXT_MUT,
                                            font_family="DOSSaemmul",
                                            text_align=ft.TextAlign.CENTER),
                            width=34, alignment=ft.Alignment(0, 0),
                        )
                        for h in DAY_HEADERS
                    ],
                    spacing=2,
                )
            ]
            for week in weeks:
                day_cells = []
                for day in week:
                    if day == 0:
                        day_cells.append(ft.Container(width=34, height=34))
                    else:
                        d        = date(view["year"], view["month"], day)
                        is_today = d == today
                        is_past  = d < today

                        def on_day(e, sel=d):
                            self.due_field.value = f"{sel.month}/{sel.day}"
                            self.due_field.update()
                            dlg.current.open = False
                            self.page.update()

                        day_cells.append(
                            ft.Container(
                                content=ft.Text(
                                    str(day), size=12,
                                    color="#F0F9F8" if is_today else (TEXT_MUT + "55" if is_past else TEXT_PRI),
                                    font_family="DOSSaemmul",
                                    text_align=ft.TextAlign.CENTER,
                                ),
                                width=34, height=34,
                                border_radius=8,
                                bgcolor=ACCENT if is_today else "transparent",
                                border=None if is_past or is_today else ft.border.all(1, ACCENT + "60"),
                                alignment=ft.Alignment(0, 0),
                                on_click=None if is_past else on_day,
                                ink=not is_past,
                            )
                        )
                rows.append(ft.Row(controls=day_cells, spacing=2))
            return rows

        def go_prev(_):
            if view["month"] == 1:
                view["month"] = 12; view["year"] -= 1
            else:
                view["month"] -= 1
            _update()

        def go_next(_):
            if view["month"] == 12:
                view["month"] = 1; view["year"] += 1
            else:
                view["month"] += 1
            _update()

        def _update():
            title_ref.current.value = (
                f"{_cal.month_name[view['month']]} {view['year']}"
            )
            title_ref.current.update()
            cal_col_ref.current.controls = build_grid()
            cal_col_ref.current.update()

        dialog = ft.AlertDialog(
            ref=dlg,
            modal=True,
            bgcolor=BG_BASE,
            shape=ft.RoundedRectangleBorder(radius=16),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.IconButton(
                                    ft.Icons.CHEVRON_LEFT,
                                    on_click=go_prev,
                                    icon_color=TEXT_PRI,
                                    icon_size=18,
                                    style=ft.ButtonStyle(padding=ft.padding.all(4)),
                                ),
                                ft.Text(
                                    ref=title_ref,
                                    value=f"{_cal.month_name[today.month]} {today.year}",
                                    size=13, color=TEXT_PRI, font_family="DOSSaemmul",
                                    expand=True, text_align=ft.TextAlign.CENTER,
                                ),
                                ft.IconButton(
                                    ft.Icons.CHEVRON_RIGHT,
                                    on_click=go_next,
                                    icon_color=TEXT_PRI,
                                    icon_size=18,
                                    style=ft.ButtonStyle(padding=ft.padding.all(4)),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        ft.Column(
                            ref=cal_col_ref,
                            controls=build_grid(),
                            spacing=2,
                            tight=True,
                        ),
                    ],
                    spacing=10,
                    tight=True,
                ),
                width=280,
                padding=ft.padding.all(16),
            ),
        )

        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    # ── 날짜 파싱 ────────────────────────────────────────────────────
    def _parse_due(self) -> str:
        text = (self.due_field.value or "").strip()
        if not text:
            return ""
        try:
            date.fromisoformat(text)
            return text
        except Exception:
            pass
        try:
            parts = text.replace("/", "-").split("-")
            if len(parts) == 2:
                m, d = int(parts[0]), int(parts[1])
                return date(date.today().year, m, d).isoformat()
        except Exception:
            pass
        return ""

    # ── 날짜 뱃지 ────────────────────────────────────────────────────
    def _due_label(self, due_str: str):
        if not due_str:
            return None
        try:
            d     = date.fromisoformat(due_str)
            today = date.today()
            delta = (d - today).days
            label = f"{d.month}/{d.day}"
            if delta < 0:
                color = DANGER;   label = f"{label} !"
            elif delta == 0:
                color = WARNING;  label = "Today"
            elif delta <= 3:
                color = WARNING
            else:
                color = TEXT_MUT
            border_color = DANGER if delta == 0 else ACCENT
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CALENDAR_TODAY_OUTLINED, size=9, color=border_color),
                        ft.Text(label, size=10, color=border_color, font_family="DOSSaemmul"),
                    ],
                    spacing=3,
                    tight=True,
                ),
                bgcolor="transparent",
                border=ft.border.all(1.5, border_color),
                border_radius=4,
                padding=ft.padding.only(left=5, top=2, right=6, bottom=2),
            )
        except Exception:
            return None

    # ── 태스크 타일 ──────────────────────────────────────────────────
    def _task_tile(self, task: dict) -> ft.Container:
        done   = task["done"]
        pcolor = PRIORITY_COLORS.get(task["priority"], ACCENT)
        ccolor = CATEGORY_COLORS.get(task["cat"], TEXT_MUT)

        def toggle(_):
            todo_store.toggle_task(task)
            self._refresh()

        def delete(_):
            todo_store.delete_task(task)
            self._refresh()

        def change_priority(_):
            todo_store.cycle_priority(task)
            self._refresh()

        due_chip = self._due_label(task.get("due", ""))
        chips = [
            ft.Container(
                content=ft.Text(task["priority"], size=10, color=pcolor,
                                font_family="DOSSaemmul"),
                bgcolor="transparent",
                border=ft.border.all(1.5, pcolor),
                border_radius=4,
                padding=ft.padding.only(left=6, top=2, right=6, bottom=2),
                on_click=change_priority,
                tooltip="Click to change priority",
            ),
        ]
        if due_chip:
            chips.append(due_chip)

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(ft.Icons.DONE, size=12,
                                        color="#F0F9F8" if done else "transparent"),
                        width=20, height=20,
                        border_radius=5,
                        border=ft.border.all(1.5, ACCENT if done else BORDER),
                        bgcolor=ACCENT if done else "transparent",
                        alignment=ft.Alignment(0, 0),
                        on_click=toggle,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                task["title"],
                                size=13,
                                color=TEXT_MUT if done else TEXT_PRI,
                                font_family="DOSSaemmul",
                                expand=True,
                                spans=[ft.TextSpan(
                                    style=ft.TextStyle(
                                        decoration=ft.TextDecoration.LINE_THROUGH)
                                )] if done else [],
                            ),
                            ft.Row(controls=chips, spacing=6, wrap=True),
                        ],
                        spacing=3,
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.Icon(ft.Icons.DELETE_OUTLINE, size=14, color=TEXT_MUT),
                        on_click=delete,
                        padding=4,
                        tooltip="Delete",
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=BG_BASE,
            border_radius=10,
            padding=ft.padding.only(left=12, top=10, right=10, bottom=10),
            border=ft.border.only(
                left=ft.BorderSide(3, ccolor if not done else BORDER),
                top=ft.BorderSide(1, BORDER),
                right=ft.BorderSide(1, BORDER),
                bottom=ft.BorderSide(1, BORDER),
            ),
            shadow=ft.BoxShadow(blur_radius=4, color="#00000008", offset=ft.Offset(0, 1)),
        )

    # ── 카테고리 칩 (테두리만) ───────────────────────────────────────
    def _cat_chip(self, label: str) -> ft.Container:
        is_active = self.new_cat == label
        color = CATEGORY_COLORS.get(label, ACCENT)

        def on_click(_):
            self.new_cat = label
            if self.cat_row_ref.current:
                self.cat_row_ref.current.controls = [self._cat_chip(c) for c in CATS]
                self.cat_row_ref.current.update()

        return ft.Container(
            content=ft.Text(label, size=11,
                            color=color if is_active else TEXT_MUT,
                            font_family="DOSSaemmul"),
            bgcolor="transparent",
            border=ft.border.all(1.5, color if is_active else "transparent"),
            border_radius=6,
            padding=ft.padding.only(left=8, top=3, right=8, bottom=3),
            on_click=on_click,
        )

    # ── 중요도 칩 (테두리만) ─────────────────────────────────────────
    def _priority_chip(self, label: str) -> ft.Container:
        is_active = self.new_priority == label
        color = PRIORITY_COLORS.get(label, ACCENT)

        def on_click(_):
            self.new_priority = label
            if self.priority_row_ref.current:
                self.priority_row_ref.current.controls = [
                    self._priority_chip(p) for p in PRIORITIES
                ]
                self.priority_row_ref.current.update()

        return ft.Container(
            content=ft.Text(label, size=11,
                            color=color if is_active else TEXT_MUT,
                            font_family="DOSSaemmul"),
            bgcolor="transparent",
            border=ft.border.all(1.5, color if is_active else "transparent"),
            border_radius=6,
            padding=ft.padding.only(left=8, top=3, right=8, bottom=3),
            on_click=on_click,
        )

    # ── 카테고리별 섹션 ──────────────────────────────────────────────
    def _build_sections(self) -> list:
        tasks = todo_store.get_tasks()
        if not tasks:
            return [
                ft.Container(
                    content=ft.Text("No tasks yet. Add one above!",
                                    size=13, color=TEXT_MUT, font_family="DOSSaemmul",
                                    text_align=ft.TextAlign.CENTER),
                    alignment=ft.Alignment(0, 0),
                    padding=ft.padding.only(top=32),
                )
            ]

        order = {"High": 0, "Medium": 1, "Low": 2}
        sections = []

        for cat in CATS:
            cat_tasks = [t for t in tasks if t["cat"] == cat]
            if not cat_tasks:
                continue

            color = CATEGORY_COLORS.get(cat, ACCENT)
            sorted_tasks = sorted(cat_tasks,
                                  key=lambda t: (t["done"], order.get(t["priority"], 1), t.get("due", "9999")))
            done_n = sum(1 for t in cat_tasks if t["done"])

            sections.append(
                ft.Row(
                    controls=[
                        ft.Container(width=3, height=13, bgcolor=color, border_radius=2),
                        ft.Text(cat, size=12, color=color, font_family="DOSSaemmul",
                                weight=ft.FontWeight.W_600),
                        ft.Text(f"{done_n}/{len(cat_tasks)}", size=10, color=TEXT_MUT,
                                font_family="DOSSaemmul"),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )
            for task in sorted_tasks:
                sections.append(self._task_tile(task))
            sections.append(ft.Container(height=4))

        # 기타
        known   = set(CATS)
        others  = [t for t in tasks if t["cat"] not in known]
        if others:
            sections.append(ft.Row(controls=[
                ft.Container(width=3, height=13, bgcolor=TEXT_MUT, border_radius=2),
                ft.Text("Other", size=12, color=TEXT_MUT, font_family="DOSSaemmul"),
            ], spacing=8))
            for task in sorted(others, key=lambda t: (t["done"], order.get(t["priority"], 1))):
                sections.append(self._task_tile(task))

        return sections

    # ── 아카이브 보기 다이얼로그 ─────────────────────────────────────
    def _show_archive(self, _=None):
        archives = todo_store.get_archives()
        dlg_ref  = ft.Ref()

        def _row(task: dict) -> ft.Container:
            due   = task.get("due", "")
            label = due[5:].replace("-", "/") if len(due) >= 7 else ""
            reason_color = ACCENT if task.get("reason") == "done" else DANGER
            reason_text  = "✓ Done" if task.get("reason") == "done" else "⏰ Expired"
            at = task.get("archived_at", "")
            at_label = at[5:].replace("-", "/") if len(at) >= 7 else at
            pcolor = PRIORITY_COLORS.get(task.get("priority", ""), TEXT_MUT)
            ccolor = CATEGORY_COLORS.get(task.get("cat", ""), TEXT_MUT)
            return ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Container(width=3, bgcolor=ccolor, border_radius=2,
                                     height=36, alignment=ft.Alignment(0, 0)),
                        ft.Column(
                            controls=[
                                ft.Text(task["title"], size=12, color=TEXT_PRI,
                                        font_family="DOSSaemmul",
                                        spans=[ft.TextSpan(style=ft.TextStyle(
                                            decoration=ft.TextDecoration.LINE_THROUGH
                                        ))] if task.get("done") else []),
                                ft.Row(
                                    controls=[
                                        ft.Text(reason_text, size=10, color=reason_color,
                                                font_family="DOSSaemmul"),
                                        ft.Text(f"due {label}" if label else "",
                                                size=10, color=TEXT_MUT, font_family="DOSSaemmul"),
                                        ft.Text(f"archived {at_label}",
                                                size=10, color=TEXT_MUT, font_family="DOSSaemmul"),
                                    ],
                                    spacing=8,
                                ),
                            ],
                            spacing=2, expand=True,
                        ),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=BG_BASE,
                border_radius=8,
                border=ft.border.all(1, BORDER),
                padding=ft.padding.only(left=6, top=8, right=12, bottom=8),
            )

        rows = [_row(t) for t in archives] if archives else [
            ft.Text("No archived tasks yet.", size=13, color=TEXT_MUT,
                    font_family="DOSSaemmul", text_align=ft.TextAlign.CENTER)
        ]

        dialog = ft.AlertDialog(
            ref=dlg_ref,
            modal=True,
            bgcolor=BG_BASE,
            shape=ft.RoundedRectangleBorder(radius=16),
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.ARCHIVE_OUTLINED, size=18, color=PINK),
                    ft.Text("Archive", size=15, color=TEXT_PRI, font_family="DOSSaemmul"),
                    ft.Container(expand=True),
                    ft.IconButton(
                        ft.Icons.CLOSE, icon_size=16, icon_color=TEXT_MUT,
                        on_click=lambda _: (setattr(dlg_ref.current, "open", False),
                                            self.page.update()),
                        style=ft.ButtonStyle(padding=ft.padding.all(4)),
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            content=ft.Container(
                content=ft.Column(
                    controls=rows,
                    spacing=6,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=420,
                height=360,
                padding=ft.padding.only(top=4, bottom=4),
            ),
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    # ── 새 태스크 추가 ───────────────────────────────────────────────
    def _add_task(self, _=None):
        text = self.new_text.value.strip()
        if not text:
            return
        todo_store.add_task({
            "title": text, "done": False,
            "priority": self.new_priority,
            "cat": self.new_cat,
            "note": "", "due": self._parse_due(),
        })
        self.new_text.value  = ""
        self.due_field.value = ""
        self._refresh()

    # ── 화면 갱신 ────────────────────────────────────────────────────
    def _refresh(self):
        todo_store.archive_completed_and_expired()  # 완료·기한초과 자동 아카이브
        tasks = todo_store.get_tasks()
        total = len(tasks)
        done  = sum(1 for t in tasks if t["done"])
        pct   = int(done / total * 100) if total else 0

        for ref, val in [
            (self.stat_total_ref,     str(total)),
            (self.stat_done_ref,      str(done)),
            (self.stat_remaining_ref, str(total - done)),
            (self.stat_pct_ref,       f"{pct}%"),
        ]:
            if ref.current:
                ref.current.value = val
                ref.current.update()

        if self.progress_ref.current:
            self.progress_ref.current.value = done / total if total else 0
            self.progress_ref.current.update()

        if self.task_col_ref.current:
            self.task_col_ref.current.controls = self._build_sections()
            self.task_col_ref.current.update()

        self.page.update()

    # ── 빌드 ────────────────────────────────────────────────────────
    def build(self) -> ft.Container:
        todo_store.archive_completed_and_expired()  # 앱 시작 시 자동 아카이브
        tasks = todo_store.get_tasks()
        total = len(tasks)
        done  = sum(1 for t in tasks if t["done"])
        pct   = int(done / total * 100) if total else 0

        stats_bar = ft.Row(
            controls=[
                ft.Column(controls=[
                    ft.Text(ref=self.stat_total_ref, value=str(total),
                            size=26, weight=ft.FontWeight.W_400,
                            color=TEXT_PRI, font_family="DOSSaemmul"),
                    ft.Text("Total", size=11, color=TEXT_MUT, font_family="DOSSaemmul"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Column(controls=[
                    ft.Text(ref=self.stat_done_ref, value=str(done),
                            size=26, weight=ft.FontWeight.W_400,
                            color=ACCENT, font_family="DOSSaemmul"),
                    ft.Text("Done", size=11, color=TEXT_MUT, font_family="DOSSaemmul"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Column(controls=[
                    ft.Text(ref=self.stat_remaining_ref, value=str(total - done),
                            size=26, weight=ft.FontWeight.W_400,
                            color=DANGER, font_family="DOSSaemmul"),
                    ft.Text("Remaining", size=11, color=TEXT_MUT, font_family="DOSSaemmul"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(expand=True),
                ft.Column(controls=[
                    ft.Text(ref=self.stat_pct_ref, value=f"{pct}%",
                            size=26, weight=ft.FontWeight.W_400,
                            color=PINK, font_family="DOSSaemmul"),
                    ft.Text("Completion", size=11, color=TEXT_MUT, font_family="DOSSaemmul"),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            ],
            spacing=32,
        )

        def _divider():
            return ft.Container(
                width=1, height=30,
                bgcolor=ACCENT + "40",
            )

        def _label(text):
            return ft.Text(text, size=10, color=TEXT_MUT, font_family="DOSSaemmul")

        # ── 입력 카드 ────────────────────────────────────────────────
        add_card = ft.Container(
            content=ft.Column(
                controls=[
                    # 텍스트 입력 줄
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.ADD_TASK_OUTLINED, size=16, color=ACCENT),
                                self.new_text,
                                ft.Container(
                                    content=ft.Icon(ft.Icons.ARROW_UPWARD,
                                                    size=14, color="#F0F9F8"),
                                    bgcolor=ACCENT,
                                    border_radius=8,
                                    width=32, height=32,
                                    alignment=ft.Alignment(0, 0),
                                    on_click=self._add_task,
                                    shadow=ft.BoxShadow(blur_radius=8, color=ACCENT + "55",
                                                        offset=ft.Offset(0, 2)),
                                ),
                            ],
                            spacing=8,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        bgcolor=BG_BASE,
                        border_radius=10,
                        border=ft.border.all(1.5, ACCENT + "80"),
                        padding=ft.padding.only(left=10, top=4, right=6, bottom=4),
                    ),
                    ft.Divider(height=1, thickness=1, color=ACCENT + "40"),
                    # 카테고리 | 중요도 | 날짜
                    ft.Row(
                        controls=[
                            # 카테고리
                            ft.Column(
                                controls=[
                                    _label("Category"),
                                    ft.Row(
                                        ref=self.cat_row_ref,
                                        controls=[self._cat_chip(c) for c in CATS],
                                        spacing=4,
                                    ),
                                ],
                                spacing=5,
                            ),
                            _divider(),
                            # 중요도
                            ft.Column(
                                controls=[
                                    _label("Priority"),
                                    ft.Row(
                                        ref=self.priority_row_ref,
                                        controls=[self._priority_chip(p) for p in PRIORITIES],
                                        spacing=4,
                                    ),
                                ],
                                spacing=5,
                            ),
                            _divider(),
                            # 날짜
                            ft.Column(
                                controls=[
                                    _label("Due Date"),
                                    ft.Container(
                                        content=ft.Row(
                                            controls=[
                                                ft.Icon(ft.Icons.CALENDAR_TODAY_OUTLINED,
                                                        size=11, color=TEXT_SEC),
                                                self.due_field,
                                            ],
                                            spacing=4,
                                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                        ),
                                        on_click=self._open_calendar,
                                        bgcolor=PINK,
                                        border_radius=6,
                                        padding=ft.padding.only(left=8, top=4, right=6, bottom=4),
                                        tooltip="Click to pick a date",
                                    ),
                                ],
                                spacing=5,
                            ),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                ],
                spacing=8,
            ),
            bgcolor="#FFFFFF",
            border_radius=14,
            border=ft.border.all(1.5, ACCENT + "55"),
            padding=ft.padding.only(left=14, top=12, right=14, bottom=12),
        )

        task_list = ft.Column(
            ref=self.task_col_ref,
            controls=self._build_sections(),
            spacing=8,
        )

        todo_store.add_listener(self._refresh)

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column(
                                controls=[
                                    ft.Text("To-Do", size=26, weight=ft.FontWeight.W_400,
                                            color=TEXT_PRI, font_family="DOSSaemmul"),
                                    ft.Text("Manage your tasks for today",
                                            size=13, color=TEXT_SEC, font_family="DOSSaemmul"),
                                ],
                                spacing=2, expand=True,
                            ),
                            # 아카이브 보기 버튼
                            ft.Container(
                                content=ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.ARCHIVE_OUTLINED,
                                                size=13, color=TEXT_SEC),
                                        ft.Text("Archive", size=11, color=TEXT_SEC,
                                                font_family="DOSSaemmul"),
                                    ],
                                    spacing=5,
                                    tight=True,
                                ),
                                bgcolor=BG_CARD,
                                border=ft.border.all(1.5, BORDER),
                                border_radius=8,
                                padding=ft.padding.only(left=10, top=6, right=10, bottom=6),
                                on_click=self._show_archive,
                                tooltip="View archived tasks",
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=14),
                    card(
                        ft.Column(
                            controls=[
                                stats_bar,
                                ft.Container(height=10),
                                ft.ProgressBar(
                                    ref=self.progress_ref,
                                    value=done / total if total else 0,
                                    color=ACCENT, bgcolor=BORDER,
                                    height=6, border_radius=3,
                                ),
                            ],
                            spacing=0,
                        ),
                        padding=ft.padding.only(left=20, top=16, right=20, bottom=16),
                    ),
                    ft.Container(height=12),
                    add_card,
                    ft.Container(height=16),
                    task_list,
                ],
                spacing=0,
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=True,
            alignment=ft.Alignment(-1, -1),
            padding=ft.padding.only(left=28, top=24, right=28, bottom=24),
            bgcolor=BG_BASE,
        )
