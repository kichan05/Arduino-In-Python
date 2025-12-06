import tkinter as tk
from game.game2 import run_ai_blink_game
from .typography import Typography

class Game2Page(tk.Frame):
    def __init__(self, parent, controller: 'ReactionGameApp'):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.canvas = tk.Canvas(self, width=controller.w, height=controller.h, highlightthickness=0, bg="black")
        self.canvas.pack(fill="both", expand=True)
        self.center_text = self.canvas.create_text(controller.cx, controller.cy, text="READY...", font=Typography.FONT_GAME_STATUS,
                                                   fill="white")

    def on_show(self):
        self.canvas.config(bg="black")
        self.canvas.itemconfig(self.center_text, text="READY...")
        self.controller.root.update()
        self.after(2000, self.start_and_finish_game)

    def start_and_finish_game(self):
        self.controller.root.withdraw()
        reaction, score = run_ai_blink_game(self.controller.board, self.controller.root)
        self.controller.root.deiconify()
        self.controller.root.update()

        if reaction is not None:
            self.controller.results = {0: reaction}
            self.controller.game_scores = {0: score}
            self.controller.database_manager.save_record("GAME2", self.controller.player_name, reaction, score)
            self.controller.show_frame("ResultPage")
        else:
            self.controller.show_frame("StartPage")
