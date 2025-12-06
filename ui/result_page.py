import tkinter as tk

from .typography import Typography


class ResultPage(tk.Frame):
    def __init__(self, parent, controller: 'ReactionGameApp'):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.canvas = tk.Canvas(self, width=controller.w, height=controller.h, highlightthickness=0, bg="#202020")
        self.canvas.pack(fill="both", expand=True)
        self.bg_id = self.canvas.create_image(0, 0, anchor="nw")

        cx, cy = controller.cx, controller.cy

        self.canvas.create_text(cx, cy * 0.3, text="RESULT", font=Typography.FONT_RESULT_TITLE, fill="white")

        self.res_text = self.canvas.create_text(cx, cy - 30, text="", font=Typography.FONT_RESULT_VAL, fill="yellow",
                                                justify="center")

        self.score_text = self.canvas.create_text(cx, cy + 50, text="", font=Typography.FONT_RESULT_SCORE, fill="white")

        self.home_btn = self.canvas.create_text(cx, controller.h * 0.9, text="MAIN MENU", font=Typography.FONT_MAIN_MENU,
                                                fill="white")

        def on_enter(e):
            self.canvas.itemconfig(self.home_btn, fill="yellow", text="MAIN MENU", font=Typography.FONT_MAIN_MENU_HOVER)
            self.canvas.config(cursor="hand2")

        def on_leave(e):
            self.canvas.itemconfig(self.home_btn, fill="white", text="MAIN MENU", font=Typography.FONT_MAIN_MENU)
            self.canvas.config(cursor="")

        self.canvas.tag_bind(self.home_btn, "<Button-1>", lambda e: controller.show_frame("StartPage"))
        self.canvas.tag_bind(self.home_btn, "<Enter>", on_enter)
        self.canvas.tag_bind(self.home_btn, "<Leave>", on_leave)

    def on_show(self):
        if self.controller.images.get("main"):
            self.canvas.itemconfig(self.bg_id, image=self.controller.images["main"])
        else:
            self.canvas.config(bg="#202020")

        r_time = self.controller.results.get(0, 9999)
        score = self.controller.game_scores.get(0, 0)

        if r_time == 9999:
            txt = "DISQUALIFIED"
            color = "red"
            s_txt = "0 pts"
        else:
            ms = r_time * 1000
            txt = f"{ms:.1f} MS"
            color = "yellow"
            s_txt = f"{score} pts"

        self.canvas.itemconfig(self.res_text, text=txt, fill=color)
        self.canvas.itemconfig(self.score_text, text=s_txt)
