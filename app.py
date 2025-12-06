import os
import sys
import time
import tkinter as tk
import pyfirmata2
import pyttsx3
from PIL import Image, ImageTk
from model.database_manager import DatabaseManager
from ui.game1_page import Game1Page
from ui.game2_page import Game2Page
from ui.game3_page import Game3Page
from ui.player_enter_page import PlayerEntryPage
from ui.result_page import ResultPage
from ui.start_page import StartPage
from ui.stats_page import StatsPage
from util import calculate_score


class ReactionGameApp:
    def __init__(self, root):
        self.root = root
        self.database_manager = DatabaseManager()
        self.root.title("Reaction Speed Game")

        self.w = self.root.winfo_screenwidth()
        self.h = self.root.winfo_screenheight()
        self.cx = self.w // 2
        self.cy = self.h // 2

        self.root.geometry(f"{self.w}x{self.h}")
        self.root.attributes('-fullscreen', True)
        self.root.bind("<Escape>", lambda event: self.on_closing())

        self.board = None
        self.tts_engine = None

        self.player_name = None
        self.results = []
        self.game_scores = []
        self.current_page = None
        self.start_time = 0
        self.is_waiting = False
        self.current_game_mode = None
        self.game_target = None

        self.images = {}
        self.pil_images = {}
        self.load_images()

        self.container = tk.Frame(self.root, bg="black")
        self.container.pack(fill="both", expand=True)

        self.frames = {}

        # UI가 먼저 그려진 후, 하드웨어 초기화 실행
        self.root.after(100, self.deferred_init)

        # 페이지 초기화
        for F in (StartPage, PlayerEntryPage, Game1Page, Game2Page, Game3Page, ResultPage, StatsPage):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("PlayerEntryPage")

    def deferred_init(self):
        self.setup_arduino()
        try:
            self.tts_engine = pyttsx3.init()
            print("TTS Engine Initialized.")
        except Exception as e:
            print(f"TTS Engine Error: {e}")
            self.tts_engine = None

    # 종료 처리
    def on_closing(self):
        if self.board:
            self.board.exit()

        self.database_manager.close()
        self.root.destroy()
        sys.exit()

    # 이미지 로드
    def load_images(self):
        img_files = {"main": "bg_main.png"}
        script_dir = os.path.dirname(__file__)
        for key, filename in img_files.items():
            try:
                path = os.path.join(script_dir, filename)
                img = Image.open(path)
                img = img.resize((self.w, self.h), Image.Resampling.LANCZOS)
                self.pil_images[key] = img
                self.images[key] = ImageTk.PhotoImage(img)
            except:
                self.images[key] = None
                self.pil_images[key] = None

    # Arduino 설정
    def setup_arduino(self):
        try:
            self.board = pyfirmata2.Arduino(pyfirmata2.Arduino.AUTODETECT)
            self.board.samplingOn(10)
            self.board.get_pin('a:1:i').register_callback(lambda d: self.handle_input(1, d))
            self.board.get_pin('a:2:i').register_callback(lambda d: self.handle_input(2, d))
            self.board.get_pin('a:3:i').register_callback(lambda d: self.handle_input(3, d))
            print("Arduino Connected!")
        except Exception as e:
            print(f"Arduino Error: {e}")
            self.board = None

    # 페이지 전환
    def show_frame(self, page_name):
        self.current_page = self.frames[page_name]
        self.current_page.tkraise()
        if hasattr(self.current_page, "on_show"):
            self.current_page.on_show()

    # 입력 처리
    def handle_input(self, pin_num, data):
        if data is not None and data < 0.2 and self.is_waiting:
            r_time = time.perf_counter() - self.start_time
            score = calculate_score(r_time)

            if self.current_game_mode == "GAME1":
                self.is_waiting = False
                is_correct = (pin_num == self.game_target)
                if not is_correct or r_time * 1000 < 180:
                    score = 0
                    r_time = 9999
                
                if self.current_page:
                    self.current_page.on_round_completed(r_time, score)

            elif self.current_game_mode == "GAME3":
                self.is_waiting = False
                user_guess = True if pin_num == 1 else False
                is_correct = (user_guess == self.game_target)
                if not is_correct or r_time * 1000 < 180:
                    score = 0
                    r_time = 9999

                if self.current_page:
                    self.current_page.on_round_completed(r_time, score)

    # 게임 종료 처리
    def finalize_and_show_results(self, game_mode, r_times, scores):
        self.results = r_times
        self.game_scores = scores
        for r_time, score in zip(r_times, scores):
            self.database_manager.save_record(game_mode, self.player_name, r_time, score)
        self.show_frame("ResultPage")
