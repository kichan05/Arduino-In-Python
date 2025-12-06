import tkinter as tk
from tkinter import messagebox
from .typography import Typography


class PlayerEntryPage(tk.Frame):
    def __init__(self, parent, controller: 'ReactionGameApp'):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.canvas = tk.Canvas(self, width=controller.w, height=controller.h, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.bg_id = self.canvas.create_image(0, 0, anchor="nw")

        self.blink_id = None
        self.is_text_visible = True

        cx, cy = controller.cx, controller.cy

        self.canvas.create_text(cx, cy * 0.3, text="ENTER NICKNAME", font=Typography.FONT_TITLE, fill="white")

        self.bg_color = "black"

        self.entry = tk.Entry(self, font=Typography.FONT_ENTRY, width=15, justify="center",
                              bd=0, highlightthickness=0, bg=self.bg_color, fg="white",
                              insertbackground="white", relief="flat")
        self.entry_win = self.canvas.create_window(cx, cy, window=self.entry)

        self.canvas.create_line(cx - 150, cy + 20, cx + 150, cy + 20, fill="white", width=3)

        self.desc_text = self.canvas.create_text(cx, cy + 180, text="", font=Typography.FONT_DESC, fill="#00FF00",
                                                 justify="center")

        self.start_btn = self.canvas.create_text(cx, controller.h * 0.85, text="START", font=Typography.FONT_TITLE, fill="white")

        def on_enter_go(e):
            self.canvas.itemconfig(self.start_btn, fill="yellow", text="GO >>>")
            self.canvas.config(cursor="hand2")

        def on_leave_go(e):
            self.canvas.itemconfig(self.start_btn, fill="white", text="START")
            self.canvas.config(cursor="")

        self.canvas.tag_bind(self.start_btn, "<Button-1>", lambda e: self.start_game())
        self.canvas.tag_bind(self.start_btn, "<Enter>", on_enter_go)
        self.canvas.tag_bind(self.start_btn, "<Leave>", on_leave_go)

        back = self.canvas.create_text(120, 80, text="< BACK", font=Typography.FONT_NORMAL, fill="white")

        def on_enter_back(e):
            self.canvas.itemconfig(back, fill="yellow", font=Typography.FONT_HOVER)
            self.canvas.config(cursor="hand2")

        def on_leave_back(e):
            self.canvas.itemconfig(back, fill="white", font=Typography.FONT_NORMAL)
            self.canvas.config(cursor="")

        self.canvas.tag_bind(back, "<Button-1>", lambda e: controller.show_frame("StartPage"))
        self.canvas.tag_bind(back, "<Enter>", on_enter_back)
        self.canvas.tag_bind(back, "<Leave>", on_leave_back)

    def on_show(self):
        if self.controller.images.get("main"):
            self.canvas.itemconfig(self.bg_id, image=self.controller.images["main"])
        else:
            self.canvas.config(bg="#202020")

        self.entry.delete(0, tk.END)
        self.entry.focus_set()

        # 설명 표기
        mode = self.controller.current_game_mode
        if mode == "GAME1":
            desc = "화면의 숫자와 동일한 버튼을 누르세요!"
        elif mode == "GAME2":
            desc = "부저가 울리면 눈을 깜빡이세요!"
        elif mode == "GAME3":
            desc = "배경과 소리가 동일하면 A1, 다르면 A2를 누르세요!"
        else:
            desc = ""
        self.canvas.itemconfig(self.desc_text, text=desc.upper())

        self.start_blinking()

    # 텍스트 깜빡이기
    def start_blinking(self):
        if self.blink_id: self.after_cancel(self.blink_id)
        self.blink_loop()

    def blink_loop(self):
        if self.is_text_visible:
            self.canvas.itemconfig(self.desc_text, state="normal")
        else:
            self.canvas.itemconfig(self.desc_text, state="hidden")
        self.is_text_visible = not self.is_text_visible
        self.blink_id = self.after(1000, self.blink_loop)

        # 게임 시작

    def start_game(self):
        name = self.entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a nickname!")
            return

        if self.blink_id: self.after_cancel(self.blink_id)
        self.controller.player_name = name.upper()

        mode = self.controller.current_game_mode
        if mode == "GAME1":
            self.controller.show_frame("Game1Page")
        elif mode == "GAME2":
            self.controller.show_frame("Game2Page")
        elif mode == "GAME3":
            self.controller.show_frame("Game3Page")
