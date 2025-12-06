import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import pyfirmata2
import time
import random
from database_manager import DatabaseManager
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import sys
import cv2
import mediapipe as mp
from scipy.spatial import distance as dist
import pyttsx3
import threading
from typing import Optional

# 폰트 설정
FONT_FAMILY = "Consolas"

FONT_NORMAL = (FONT_FAMILY, 20, "bold")
FONT_HOVER = (FONT_FAMILY, 25, "bold")
FONT_TITLE = (FONT_FAMILY, 60, "bold")
FONT_GAME_STATUS = (FONT_FAMILY, 80, "bold")
FONT_BLINK = (FONT_FAMILY, 15, "bold")

FONT_RESULT_TITLE = (FONT_FAMILY, 70, "bold")
FONT_RESULT_VAL = (FONT_FAMILY, 60, "bold")
FONT_RESULT_SCORE = (FONT_FAMILY, 40, "bold", "italic")
FONT_MAIN_MENU = (FONT_FAMILY, 40, "bold")
FONT_MAIN_MENU_HOVER = (FONT_FAMILY, 45, "bold")

FONT_ENTRY = (FONT_FAMILY, 30, "bold")
FONT_DESC = (FONT_FAMILY, 20, "bold")
FONT_STATS_TAB = (FONT_FAMILY, 22, "bold")
FONT_STATS_TAB_HOVER = (FONT_FAMILY, 26, "bold")


# 점수 계산
def calculate_score(reaction_time_sec):
    ms = reaction_time_sec * 1000
    if ms < 180:
        return 0
    elif ms < 200:
        return 3
    elif ms < 225:
        return 2
    elif ms < 250:
        return 1
    else:
        return 0


# OpenCV 텍스트 외곽선 그리기
def draw_text_with_outline(img, text, pos, font_scale, font_thickness, text_color=(255, 255, 255),
                           outline_color=(0, 0, 0)):
    x, y = pos
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, outline_color, font_thickness + 3, cv2.LINE_AA)
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, font_thickness, cv2.LINE_AA)


# GAME 2 : AI 눈 깜빡임 게임 로직
def run_ai_blink_game(board, root):
    if board is None:
        messagebox.showerror("Error", "Arduino Not Connected")
        return None, None

    try:
        buzzer = board.get_pin('d:3:o')
        buzzer.write(1)
    except Exception as e:
        print(f"Pin Setup Failed: {e}")
        return None, None

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True)
    LEFT_EYE = [362, 385, 387, 263, 373, 380]
    RIGHT_EYE = [33, 160, 158, 133, 153, 144]

    def calculate_ear(eye_points, landmarks):
        A = dist.euclidean(landmarks[eye_points[1]], landmarks[eye_points[5]])
        B = dist.euclidean(landmarks[eye_points[2]], landmarks[eye_points[4]])
        C = dist.euclidean(landmarks[eye_points[0]], landmarks[eye_points[3]])
        ear = (A + B) / (2.0 * C)
        return ear

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Error", "Camera Not Found")
        return None, None

    window_name = 'Blink Game'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    win_w, win_h = 800, 600
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    pos_x = (screen_w - win_w) // 2
    pos_y = (screen_h - win_h) // 2

    cv2.resizeWindow(window_name, win_w, win_h)
    cv2.moveWindow(window_name, pos_x, pos_y)

    root.withdraw()

    game_state = "WAITING"
    start_time = 0
    beep_start_time = 0
    random_wait = random.uniform(2, 5)
    wait_start = time.time()

    final_reaction = None
    final_score = 0

    # 게임 루프
    try:
        while True:
            ret, frame = cap.read()
            if not ret: break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_frame)
            h, w, _ = frame.shape

            current_ear = 0
            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0].landmark
                mesh_points = [(int(pt.x * w), int(pt.y * h)) for pt in landmarks]
                left_ear = calculate_ear(LEFT_EYE, mesh_points)
                right_ear = calculate_ear(RIGHT_EYE, mesh_points)
                current_ear = (left_ear + right_ear) / 2.0

            center_x = w // 2
            center_y = h // 2

            # 게임 시작 시
            if game_state == "WAITING":
                draw_text_with_outline(frame, "WAIT FOR SOUND...", (30, 50), 1.0, 2)

                if time.time() - wait_start > random_wait:
                    buzzer.write(0)
                    start_time = time.time()
                    beep_start_time = time.time()
                    game_state = "BEEPING"

            elif game_state == "BEEPING":
                draw_text_with_outline(frame, "WAIT FOR SOUND...", (30, 50), 1.0, 2)
                if time.time() - beep_start_time > 0.1:
                    buzzer.write(1)
                    game_state = "MEASURING"
            # 반응속도 측정 시
            elif game_state == "MEASURING":
                draw_text_with_outline(frame, "BLINK NOW!", (center_x - 150, center_y), 2.0, 4, text_color=(0, 0, 255))

                if current_ear < 0.22 and current_ear > 0.0:
                    end_time = time.time()
                    reaction_sec = end_time - start_time
                    buzzer.write(1)

                    final_score = calculate_score(reaction_sec)
                    final_reaction = reaction_sec

                    # 결과 대기 문구 표시
                    ret, frame = cap.read()
                    frame = cv2.flip(frame, 1)

                    wait_msg = "PLEASE WAIT FOR RESULT..."

                    font_scale = 1.0
                    thickness = 2
                    text_size = cv2.getTextSize(wait_msg, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
                    text_w, text_h = text_size

                    # 화면 중앙 좌표
                    text_x = (w - text_w) // 2
                    text_y = (h + text_h) // 2

                    # 대기 문구
                    draw_text_with_outline(frame, wait_msg, (text_x, text_y), font_scale, thickness,
                                           text_color=(0, 255, 255))
                    cv2.imshow(window_name, frame)
                    cv2.waitKey(1500)
                    break

            cv2.imshow(window_name, frame)

            if cv2.waitKey(1) == 27:
                final_reaction = None
                break

    finally:
        try:
            buzzer.write(1)
        except:
            pass
        cap.release()
        cv2.destroyAllWindows()
        for i in range(10): cv2.waitKey(1)

    return final_reaction, final_score


# 메인 메뉴
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
        self.setup_arduino()

        try:
            self.tts_engine = pyttsx3.init()
        except:
            self.tts_engine = None

        self.player_name = "PLAYER"
        self.results = {}
        self.game_scores = {}
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

        # 페이지 초기화
        for F in (StartPage, PlayerEntryPage, Game1Page, Game2Page, Game3Page, ResultPage, StatsPage):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage")

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
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, "on_show"): frame.on_show()

    # 입력 처리
    def handle_input(self, pin_num, data):
        if data is not None and data < 0.2 and self.is_waiting:
            if self.current_game_mode == "GAME1":
                self.is_waiting = False
                r_time = time.perf_counter() - self.start_time
                is_correct = (pin_num == self.game_target)
                score = calculate_score(r_time)
                if not is_correct or r_time * 1000 < 180:
                    score = 0
                    r_time = 9999
                self.results = {0: r_time}
                self.game_scores = {0: score}
                self.root.after(0, lambda: self._game_finished("GAME1", r_time, score))

            elif self.current_game_mode == "GAME3":
                self.is_waiting = False
                r_time = time.perf_counter() - self.start_time
                user_guess = True if pin_num == 1 else False
                is_correct = (user_guess == self.game_target)
                score = calculate_score(r_time)
                if not is_correct or r_time * 1000 < 180:
                    score = 0
                    r_time = 9999
                self.results = {0: r_time}
                self.game_scores = {0: score}
                self.root.after(0, lambda: self._game_finished("GAME3", r_time, score))

    # 게임 종료 처리
    def _game_finished(self, game_mode, r_time, score):
        self.database_manager.save_record(game_mode, self.player_name, r_time, score)
        self.show_frame("ResultPage")

# 시작 페이지
class StartPage(tk.Frame):
    def __init__(self, parent, controller: 'ReactionGameApp'):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.canvas = tk.Canvas(self, width=controller.w, height=controller.h, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.bg_id = self.canvas.create_image(0, 0, anchor="nw")

        cx, cy = controller.cx, controller.cy
        self.canvas.create_text(cx, cy * 0.3, text="REACTION SPEED GAME", font=FONT_TITLE, fill="white")

        # 메뉴 버튼 생성
        def create_menu_btn(text, x, y, command):
            btn = self.canvas.create_text(x, y, text=text, font=FONT_NORMAL, fill="white", justify="center")

            def on_enter(e):
                self.canvas.itemconfig(btn, fill="yellow", font=FONT_HOVER)
                self.canvas.config(cursor="hand2")

            def on_leave(e):
                self.canvas.itemconfig(btn, fill="white", font=FONT_NORMAL)
                self.canvas.config(cursor="")

            self.canvas.tag_bind(btn, "<Enter>", on_enter)
            self.canvas.tag_bind(btn, "<Leave>", on_leave)
            self.canvas.tag_bind(btn, "<Button-1>", lambda e: command())

        spacing = 250
        create_menu_btn("GAME 1\n(NUMBERS)", cx - spacing, cy, lambda: self.go_to_entry("GAME1"))
        create_menu_btn("GAME 2\n(BLINK)", cx, cy, lambda: self.go_to_entry("GAME2"))
        create_menu_btn("GAME 3\n(COLOR/SOUND)", cx + spacing, cy, lambda: self.go_to_entry("GAME3"))

        create_menu_btn("STATS", cx, cy + 200, lambda: controller.show_frame("StatsPage"))
        create_menu_btn("EXIT", cx, cy + 300, lambda: controller.on_closing())

    def on_show(self):
        if self.controller.images.get("main"):
            self.canvas.itemconfig(self.bg_id, image=self.controller.images["main"])
        else:
            self.canvas.config(bg="#202020")

    # 게임 모드 선택 후 닉네임 입력 페이지로 이동
    def go_to_entry(self, mode):
        self.controller.current_game_mode = mode
        self.controller.show_frame("PlayerEntryPage")


# 닉네임 입력 페이지
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

        self.canvas.create_text(cx, cy * 0.3, text="ENTER NICKNAME", font=FONT_TITLE, fill="white")

        self.bg_color = "black"

        self.entry = tk.Entry(self, font=FONT_ENTRY, width=15, justify="center",
                              bd=0, highlightthickness=0, bg=self.bg_color, fg="white",
                              insertbackground="white", relief="flat")
        self.entry_win = self.canvas.create_window(cx, cy, window=self.entry)

        self.canvas.create_line(cx - 150, cy + 20, cx + 150, cy + 20, fill="white", width=3)

        self.desc_text = self.canvas.create_text(cx, cy + 180, text="", font=FONT_DESC, fill="#00FF00",
                                                 justify="center")

        self.start_btn = self.canvas.create_text(cx, controller.h * 0.85, text="START", font=FONT_TITLE, fill="white")

        def on_enter_go(e):
            self.canvas.itemconfig(self.start_btn, fill="yellow", text="GO >>>")
            self.canvas.config(cursor="hand2")

        def on_leave_go(e):
            self.canvas.itemconfig(self.start_btn, fill="white", text="START")
            self.canvas.config(cursor="")

        self.canvas.tag_bind(self.start_btn, "<Button-1>", lambda e: self.start_game())
        self.canvas.tag_bind(self.start_btn, "<Enter>", on_enter_go)
        self.canvas.tag_bind(self.start_btn, "<Leave>", on_leave_go)

        back = self.canvas.create_text(120, 80, text="< BACK", font=FONT_NORMAL, fill="white")

        def on_enter_back(e):
            self.canvas.itemconfig(back, fill="yellow", font=FONT_HOVER)
            self.canvas.config(cursor="hand2")

        def on_leave_back(e):
            self.canvas.itemconfig(back, fill="white", font=FONT_NORMAL)
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


# GAME 1 페이지
class Game1Page(tk.Frame):
    def __init__(self, parent, controller: 'ReactionGameApp'):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.canvas = tk.Canvas(self, width=controller.w, height=controller.h, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.center_text = self.canvas.create_text(controller.cx, controller.cy, text="", font=FONT_GAME_STATUS,
                                                   fill="white")

    def on_show(self):
        self.canvas.config(bg="black")
        self.canvas.itemconfig(self.center_text, text="READY...", font=FONT_GAME_STATUS, fill="white")
        delay = random.randint(2000, 5000)
        self.controller.root.after(delay, self.go_signal)

    def go_signal(self):
        target = random.randint(1, 3)
        self.controller.game_target = target
        self.canvas.config(bg="green")
        self.canvas.itemconfig(self.center_text, text=str(target), font=("Courier New", 200, "bold"), fill="white")

        self.controller.start_time = time.perf_counter()
        self.controller.is_waiting = True


# GAME 2 페이지
class Game2Page(tk.Frame):
    def __init__(self, parent, controller: 'ReactionGameApp'):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.canvas = tk.Canvas(self, width=controller.w, height=controller.h, highlightthickness=0, bg="black")
        self.canvas.pack(fill="both", expand=True)
        self.center_text = self.canvas.create_text(controller.cx, controller.cy, text="READY...", font=FONT_GAME_STATUS,
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


# GAME 3 페이지
class Game3Page(tk.Frame):
    def __init__(self, parent, controller: 'ReactionGameApp'):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.canvas = tk.Canvas(self, width=controller.w, height=controller.h, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.center_text = self.canvas.create_text(controller.cx, controller.cy, text="", font=FONT_GAME_STATUS,
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


# 결과 페이지
class ResultPage(tk.Frame):
    def __init__(self, parent, controller: 'ReactionGameApp'):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.canvas = tk.Canvas(self, width=controller.w, height=controller.h, highlightthickness=0, bg="#202020")
        self.canvas.pack(fill="both", expand=True)
        self.bg_id = self.canvas.create_image(0, 0, anchor="nw")

        cx, cy = controller.cx, controller.cy

        self.canvas.create_text(cx, cy * 0.3, text="RESULT", font=FONT_RESULT_TITLE, fill="white")

        self.res_text = self.canvas.create_text(cx, cy - 30, text="", font=FONT_RESULT_VAL, fill="yellow",
                                                justify="center")

        self.score_text = self.canvas.create_text(cx, cy + 50, text="", font=FONT_RESULT_SCORE, fill="white")

        self.home_btn = self.canvas.create_text(cx, controller.h * 0.9, text="MAIN MENU", font=FONT_MAIN_MENU,
                                                fill="white")

        def on_enter(e):
            self.canvas.itemconfig(self.home_btn, fill="yellow", text="MAIN MENU", font=FONT_MAIN_MENU_HOVER)
            self.canvas.config(cursor="hand2")

        def on_leave(e):
            self.canvas.itemconfig(self.home_btn, fill="white", text="MAIN MENU", font=FONT_MAIN_MENU)
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


# 통계 페이지
class StatsPage(tk.Frame):
    def __init__(self, parent, controller: 'ReactionGameApp'):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.canvas = tk.Canvas(self, width=controller.w, height=controller.h, highlightthickness=0, bg="white")
        self.canvas.pack(fill="both", expand=True)

        self.chart_widget = None
        self.selected_game = tk.StringVar(value="GAME1")

    def on_show(self):
        self.canvas.delete("ui")
        if self.chart_widget:
            self.chart_widget.destroy()
            self.chart_widget = None
        self.draw_ui()
        self.load_player_list()

    def draw_ui(self):
        cx = self.controller.cx

        modes = [("GAME 1", "GAME1"), ("GAME 2", "GAME2"), ("GAME 3", "GAME3")]

        self.canvas.create_text(cx - 100, 80, text="|", font=FONT_STATS_TAB, fill="black", tags="ui")
        self.canvas.create_text(cx + 100, 80, text="|", font=FONT_STATS_TAB, fill="black", tags="ui")

        positions = [(cx - 200, "GAME 1", "GAME1"), (cx, "GAME 2", "GAME2"), (cx + 200, "GAME 3", "GAME3")]

        # 통계 탭 생성
        for x, text, mode in positions:
            is_selected = (self.selected_game.get() == mode)
            color = "blue" if is_selected else "black"
            font = FONT_STATS_TAB_HOVER if is_selected else FONT_STATS_TAB

            btn = self.canvas.create_text(x, 80, text=text, font=font, fill=color, tags="ui")

            def on_enter(e, item=btn, m=mode):
                self.canvas.itemconfig(item, fill="blue", font=FONT_STATS_TAB_HOVER)
                self.canvas.config(cursor="hand2")

            def on_leave(e, item=btn, m=mode):
                if self.selected_game.get() == m:
                    self.canvas.itemconfig(item, fill="blue", font=FONT_STATS_TAB_HOVER)
                else:
                    self.canvas.itemconfig(item, fill="black", font=FONT_STATS_TAB)
                self.canvas.config(cursor="")

            self.canvas.tag_bind(btn, "<Button-1>", lambda e, m=mode: self.change_mode(m))
            self.canvas.tag_bind(btn, "<Enter>", lambda e, b=btn, m=mode: on_enter(e, b, m))
            self.canvas.tag_bind(btn, "<Leave>", lambda e, b=btn, m=mode: on_leave(e, b, m))

        back = self.canvas.create_text(120, 80, text="< BACK", font=FONT_NORMAL, fill="black", tags="ui")

        def on_enter_back(e):
            self.canvas.itemconfig(back, fill="#CCCC00", font=FONT_HOVER)
            self.canvas.config(cursor="hand2")

        def on_leave_back(e):
            self.canvas.itemconfig(back, fill="black", font=FONT_NORMAL)
            self.canvas.config(cursor="")

        self.canvas.tag_bind(back, "<Button-1>", lambda e: self.controller.show_frame("StartPage"))
        self.canvas.tag_bind(back, "<Enter>", on_enter_back)
        self.canvas.tag_bind(back, "<Leave>", on_leave_back)

        self.canvas.create_text(300, 200, text="NICKNAME:", font=FONT_NORMAL, fill="black", anchor="e", tags="ui")

        self.entry = tk.Entry(self, font=FONT_NORMAL, width=15, bg="white", fg="black",
                              bd=0, highlightthickness=0, relief="flat")
        self.canvas.create_window(450, 200, window=self.entry, tags="ui")

        self.canvas.create_line(350, 220, 550, 220, fill="black", width=2, tags="ui")

        search_btn = self.canvas.create_text(600, 200, text="🔍", font=FONT_NORMAL, fill="black", tags="ui")
        self.canvas.tag_bind(search_btn, "<Button-1>", lambda e: self.draw_graph(self.entry.get()))

    def change_mode(self, mode):
        self.selected_game.set(mode)
        self.on_show()

    # 그래프
    def load_player_list(self):
        names = self.controller.database_manager.get_all_player_names()
        list_frame = tk.Frame(self)
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        lb = tk.Listbox(list_frame, height=15, width=20, font=("Arial", 12), yscrollcommand=scrollbar.set)
        lb.pack(side="left", fill="both")
        scrollbar.config(command=lb.yview)
        for n in names: lb.insert(tk.END, n)
        lb.bind('<<ListboxSelect>>', lambda e: self.on_select(lb))
        self.canvas.create_window(200, 500, window=list_frame, tags="ui")

    def on_select(self, lb):
        if lb.curselection():
            name = lb.get(lb.curselection())
            self.entry.delete(0, tk.END)
            self.entry.insert(0, name)
            self.draw_graph(name)

    def draw_graph(self, name):
        if not name: return
        if self.chart_widget: self.chart_widget.destroy()

        mode = self.selected_game.get()
        data = self.controller.database_manager.get_stats_by_player(mode, name)

        if not data:
            messagebox.showinfo("Info", "No data found for this player.")
            return

        dates = []
        scores = []
        cumulative_score = 0

        for row in data:
            dt_str = row[0]
            score = row[1]
            try:
                dt_obj = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                date_key = dt_obj.strftime("%m/%d")
            except:
                date_key = dt_str

            cumulative_score += score
            dates.append(date_key)
            scores.append(cumulative_score)

        self.canvas.create_text(self.controller.cx + 100, 250, text=f"TOTAL SCORE : {cumulative_score}",
                                font=("Courier New", 30, "bold"), fill="black", tags="ui")

        fig = plt.Figure(figsize=(8, 5), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(dates, scores, marker='o', linestyle='-', color='blue')
        ax.set_title(f"{name}'s Progress")
        ax.set_ylabel("Total Score")
        ax.grid(True)

        canvas = FigureCanvasTkAgg(fig, self)
        self.chart_widget = canvas.get_tk_widget()
        self.canvas.create_window(self.controller.w * 0.35, 300, window=self.chart_widget, anchor="nw", tags="ui")


# 메인 실행
if __name__ == "__main__":
    root = tk.Tk()
    app = ReactionGameApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
