import random
import threading
import time
import tkinter as tk
import pyttsx3
from .typography import Typography


class Game3Page(tk.Frame):
    def __init__(self, parent, controller: 'ReactionGameApp'):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.canvas = tk.Canvas(self, width=controller.w, height=controller.h, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.center_text = self.canvas.create_text(controller.cx, controller.cy, text="", font=Typography.FONT_GAME_STATUS,
                                                   fill="white")
        self.colors = {"RED": "#FF0000", "YELLOW": "#FFFF00", "GREEN": "#00FF00", "BLUE": "#0000FF"}
        self.color_keys = list(self.colors.keys())

    def on_show(self):
        self.canvas.config(bg="black")
        self.canvas.itemconfig(self.center_text, text="READY...", fill="white")
        delay = random.randint(2000, 5000)
        self.controller.root.after(delay, self.go_signal)

    def go_signal(self):
        v_color = random.choice(self.color_keys)
        a_color = random.choice(self.color_keys)
        self.canvas.config(bg=self.colors[v_color])
        self.canvas.itemconfig(self.center_text, text="")
        self.controller.game_target = (v_color == a_color)

        if self.controller.tts_engine:
            threading.Thread(target=self.play_sound, args=(a_color,)).start()

        self.controller.start_time = time.perf_counter()
        self.controller.is_waiting = True

    def play_sound(self, text):
        try:
            engine = pyttsx3.init()
            engine.say(text)
            engine.runAndWait()
        except:
            pass
