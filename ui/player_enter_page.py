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

        cx, cy = controller.cx, controller.cy

        self.canvas.create_text(cx, cy * 0.3, text="ENTER NICKNAME", font=Typography.FONT_TITLE, fill="white")

        self.bg_color = "black"

        self.entry = tk.Entry(self, font=Typography.FONT_ENTRY, width=15, justify="center",
                              bd=0, highlightthickness=0, bg=self.bg_color, fg="white",
                              insertbackground="white", relief="flat")
        self.entry_win = self.canvas.create_window(cx, cy, window=self.entry)

        self.canvas.create_line(cx - 150, cy + 20, cx + 150, cy + 20, fill="white", width=3)

        self.confirm_btn = self.canvas.create_text(cx, controller.h * 0.85, text="CONFIRM",
                                                  font=Typography.FONT_TITLE, fill="white")

        def on_enter_go(e):
            self.canvas.itemconfig(self.confirm_btn, fill="yellow", text="OK")
            self.canvas.config(cursor="hand2")

        def on_leave_go(e):
            self.canvas.itemconfig(self.confirm_btn, fill="white", text="CONFIRM")
            self.canvas.config(cursor="")

        self.canvas.tag_bind(self.confirm_btn, "<Button-1>", lambda e: self.confirm_name())
        self.canvas.tag_bind(self.confirm_btn, "<Enter>", on_enter_go)
        self.canvas.tag_bind(self.confirm_btn, "<Leave>", on_leave_go)

    def on_show(self):
        if self.controller.images.get("main"):
            self.canvas.itemconfig(self.bg_id, image=self.controller.images["main"])
        else:
            self.canvas.config(bg="#202020")

        self.entry.delete(0, tk.END)
        self.entry.focus_set()

    def confirm_name(self):
        name = self.entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a nickname!")
            return

        self.controller.player_name = name.upper()
        # 입력 위젯에서 포커스를 해제하여 UI 멈춤 현상 방지
        self.focus_set()
        self.controller.show_frame("StartPage")
