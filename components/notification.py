import flet as ft

ACCENT = "#00E5CC"
ACCENT2 = "#FF6B6B"
BG_CARD = "#0D1117"


class PostureAlert:
    def __init__(self, page: ft.Page, score: int):
        self.page = page
        self.score = score
        self._dialog = None

    def show(self):
        score = self.score
        color = ACCENT2 if score < 50 else "#FFA500"
        msg = "Turtle neck risk! Please correct your posture now." if score < 50 else "Your posture is slightly off. Straighten your back."
        emoji = "🚨" if score < 50 else "⚠️"

        def close(_):
            self._dialog.open = False
            self.page.update()

        self._dialog = ft.AlertDialog(
            modal=False,
            bgcolor=BG_CARD,
            shape=ft.RoundedRectangleBorder(radius=16),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(emoji, size=40),
                        ft.Text("Posture Alert", size=18, weight=ft.FontWeight.W_800,
                                color=color, font_family="DOSSaemmul"),
                        ft.Text(msg, size=13, color="#A0AEC0",
                                text_align=ft.TextAlign.CENTER, font_family="DOSSaemmul"),
                        ft.Container(height=4),
                        ft.Row(
                            controls=[
                                ft.Text("Posture Score", size=12, color="#4A5568"),
                                ft.Text(f"{score}pts", size=14, weight=ft.FontWeight.W_700,
                                        color=color),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.ProgressBar(value=score / 100, color=color,
                                       bgcolor="#1A2332", height=6,
                                       border_radius=3),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                ),
                padding=20,
                width=280,
            ),
            actions=[
                ft.TextButton(
                    "Fix Posture",
                    style=ft.ButtonStyle(color=ACCENT),
                    on_click=close,
                ),
                ft.TextButton(
                    "Remind in 5 min",
                    style=ft.ButtonStyle(color="#4A5568"),
                    on_click=close,
                ),
            ],
        )

        self.page.dialog = self._dialog
        self._dialog.open = True
        self.page.update()
