import random
import time
import tkinter as tk
from .typography import Typography


class Game1Page(tk.Frame):
    def __init__(self, parent, controller: 'ReactionGameApp'):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.canvas = tk.Canvas(self, width=controller.w, height=controller.h, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.center_text = self.canvas.create_text(controller.cx, controller.cy, text="", font=Typography.FONT_GAME_STATUS,
                                                   fill="white")

        # --- New state for rounds ---
        self.num_rounds = 5
        self.current_round = 0
        self.all_r_times = []
        self.all_scores = []

    def on_show(self):
        # Reset game state when page is shown
        self.current_round = 0
        self.all_r_times.clear()
        self.all_scores.clear()
        self.start_next_round()

    def start_next_round(self):
        self.current_round += 1
        if self.current_round > self.num_rounds:
            self.finish_game()
            return

        self.canvas.config(bg="black")
        # Combine ROUND and READY text
        combined_text = f"ROUND {self.current_round}/{self.num_rounds}\n\nREADY..."
        self.canvas.itemconfig(self.center_text, text=combined_text, font=Typography.FONT_GAME_STATUS, fill="white",
                               justify="center")

        # Reduced and single delay
        delay = random.randint(1500, 3000)
        self.controller.root.after(delay, self.go_signal)

    def go_signal(self):
        target = random.randint(1, 3)
        self.controller.game_target = target
        self.canvas.config(bg="green")
        self.canvas.itemconfig(self.center_text, text=str(target), font=("Courier New", 200, "bold"), fill="white")

        self.controller.start_time = time.perf_counter()
        self.controller.is_waiting = True

    def on_round_completed(self, r_time, score):
        self.all_r_times.append(r_time)
        self.all_scores.append(score)

        # Show feedback for the round
        self.controller.is_waiting = False
        self.canvas.config(bg="black")
        feedback_text = ""
        if r_time == 9999:
            feedback_text = "FAIL"
        else:
            feedback_text = f"{r_time*1000:.1f} ms"
        
        self.canvas.itemconfig(self.center_text, text=feedback_text, font=Typography.FONT_GAME_STATUS, fill="yellow")

        # After a delay, start the next round
        self.controller.root.after(2000, self.start_next_round)

    def finish_game(self):
        self.controller.finalize_and_show_results("GAME1", self.all_r_times, self.all_scores)
