import tkinter as tk
from .typography import Typography


class StartPage(tk.Frame):
    def __init__(self, parent, controller: 'ReactionGameApp'):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.canvas = tk.Canvas(self, width=controller.w, height=controller.h, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.bg_id = self.canvas.create_image(0, 0, anchor="nw")

        cx, cy = controller.cx, controller.cy
        self.canvas.create_text(cx, cy * 0.3, text="REACTION SPEED GAME", font=Typography.FONT_TITLE, fill="white")

        # 메뉴 버튼 생성
        def create_menu_btn(text, x, y, command):
            btn = self.canvas.create_text(x, y, text=text, font=Typography.FONT_NORMAL, fill="white", justify="center")

            def on_enter(e):
                self.canvas.itemconfig(btn, fill="yellow", font=Typography.FONT_HOVER)
                self.canvas.config(cursor="hand2")

            def on_leave(e):
                self.canvas.itemconfig(btn, fill="white", font=Typography.FONT_NORMAL)
                self.canvas.config(cursor="")

            self.canvas.tag_bind(btn, "<Enter>", on_enter)
            self.canvas.tag_bind(btn, "<Leave>", on_leave)
            self.canvas.tag_bind(btn, "<Button-1>", lambda e: command())

        spacing = 250
        create_menu_btn("GAME 1\n(NUMBERS)", cx - spacing, cy, lambda: self.go_to_entry("GAME1"))
        create_menu_btn("GAME 2\n(BLINK)", cx, cy, lambda: self.go_to_entry("GAME2"))
        create_menu_btn("GAME 3\n(COLOR/SOUND)", cx + spacing, cy, lambda: self.go_to_entry("GAME3"))

        create_menu_btn("STATS", cx, cy + 200, lambda: controller.show_frame("StatsPage"))
        create_menu_btn("EXIT", cx, cy + 300, lambda: controller.on_closing())

    def on_show(self):
        if self.controller.images.get("main"):
            self.canvas.itemconfig(self.bg_id, image=self.controller.images["main"])
        else:
            self.canvas.config(bg="#202020")

    # 게임 모드 선택 후 닉네임 입력 페이지로 이동
    def go_to_entry(self, mode):
        self.controller.current_game_mode = mode
        self.controller.show_frame("PlayerEntryPage")
