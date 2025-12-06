import random
import time
import tkinter as tk

# from app import ReactionGameApp
from .typography import Typography


class Game1Page(tk.Frame):
    def __init__(self, parent, controller: 'ReactionGameApp'):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.canvas = tk.Canvas(self, width=controller.w, height=controller.h, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.center_text = self.canvas.create_text(controller.cx, controller.cy, text="", font=Typography.FONT_GAME_STATUS,
                                                   fill="white")

    def on_show(self):
        self.canvas.config(bg="black")
        self.canvas.itemconfig(self.center_text, text="READY...", font=Typography.FONT_GAME_STATUS, fill="white")
        delay = random.randint(2000, 5000)
        self.controller.root.after(delay, self.go_signal)

    def go_signal(self):
        target = random.randint(1, 3)
        self.controller.game_target = target
        self.canvas.config(bg="green")
        self.canvas.itemconfig(self.center_text, text=str(target), font=("Courier New", 200, "bold"), fill="white")

        self.controller.start_time = time.perf_counter()
        self.controller.is_waiting = True
