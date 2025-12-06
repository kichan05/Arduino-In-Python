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

        self.canvas.create_text(cx, cy * 0.2, text="RESULT", font=Typography.FONT_RESULT_TITLE, fill="white")

        self.best_time_text = self.canvas.create_text(cx, cy - 80, text="", font=Typography.FONT_RESULT_VAL,
                                                      fill="white")
        self.avg_time_text = self.canvas.create_text(cx, cy, text="", font=Typography.FONT_RESULT_VAL,
                                                     fill="white")
        self.total_score_text = self.canvas.create_text(cx, cy + 80, text="", font=Typography.FONT_RESULT_SCORE,
                                                        fill="yellow")

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

        r_times = self.controller.results
        scores = self.controller.game_scores

        if not r_times:
            # Handle case with no results
            self.canvas.itemconfig(self.best_time_text, text="NO RESULTS")
            self.canvas.itemconfig(self.avg_time_text, text="")
            self.canvas.itemconfig(self.total_score_text, text="")
            return

        successful_r_times = [t for t in r_times if t != 9999]
        total_score = sum(scores)

        if not successful_r_times:
            best_time_ms = "N/A"
            avg_time_ms = "N/A"
        else:
            best_time_ms = f"{min(successful_r_times) * 1000:.1f} MS"
            avg_time_ms = f"{(sum(successful_r_times) / len(successful_r_times)) * 1000:.1f} MS"
        
        total_score_str = f"{total_score} pts"

        self.canvas.itemconfig(self.best_time_text, text=f"BEST: {best_time_ms}")
        self.canvas.itemconfig(self.avg_time_text, text=f"AVG: {avg_time_ms}")
        self.canvas.itemconfig(self.total_score_text, text=f"TOTAL SCORE: {total_score_str}")
