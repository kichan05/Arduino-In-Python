import tkinter as tk
import threading
import cv2
import mediapipe as mp
from .typography import Typography
from game.game2 import run_game2_engine


class Game2Page(tk.Frame):
    def __init__(self, parent, controller: 'ReactionGameApp'):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.canvas = tk.Canvas(self, width=controller.w, height=controller.h, highlightthickness=0, bg="black")
        self.canvas.pack(fill="both", expand=True)
        self.center_text = self.canvas.create_text(controller.cx, controller.cy, text="", font=Typography.FONT_GAME_STATUS,
                                                   fill="white")

        # --- Game State & Resources ---
        self.num_rounds = 5
        self.game_thread = None
        self.buzzer = None
        self.cap = None
        self.face_mesh = None

    def on_show(self):
        # Initialize resources once per game session
        if self.cap is None:
            self.cap = cv2.VideoCapture(0)
        if self.face_mesh is None:
            mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)

        if self.controller.board and self.buzzer is None:
            try:
                self.buzzer = self.controller.board.get_pin('d:3:o')
            except Exception as e:
                print(f"Buzzer pin setup failed in Game2Page: {e}")
        
        # UI shows a brief "STARTING" message
        self.canvas.itemconfig(self.center_text, text="STARTING GAME...", fill="white")
        self.controller.root.after(500, self.run_game_thread)

    def run_game_thread(self):
        # Hide the main Tkinter window before starting the OpenCV game
        self.controller.root.withdraw()
        
        # Start the OpenCV game engine in a separate thread
        self.game_thread = threading.Thread(target=self._run_game_engine)
        self.game_thread.start()

    def _run_game_engine(self):
        # This function runs in a separate thread and executes the entire game
        all_r_times, all_scores = run_game2_engine(
            self.buzzer,
            self.cap,
            self.face_mesh,
            self.num_rounds,
            self.controller.w,
            self.controller.h
        )
        
        # Schedule the result processing back on the main UI thread
        self.controller.root.after(0, lambda: self._on_game_finished(all_r_times, all_scores))

    def _on_game_finished(self, all_r_times, all_scores):
        # Show the main Tkinter window again
        self.controller.root.deiconify()
        
        # Release camera resource now that the entire game is over
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None
            self.face_mesh = None # Also clear face mesh for re-init next time

        # Pass the final results to the controller
        self.controller.finalize_and_show_results("GAME2", all_r_times, all_scores)
