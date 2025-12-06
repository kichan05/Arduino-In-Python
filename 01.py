import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import pyfirmata2
import time
import random
import sqlite3
import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import sys

# 디자인/글꼴 설정
FONT_NORMAL = ("Courier New", 20, "bold")
FONT_HOVER = ("Courier New", 25, "bold")
FONT_TITLE = ("Courier New", 60, "bold")
FONT_GAME_STATUS = ("Courier New", 80, "bold")
FONT_BLINK = ("Courier New", 15, "bold")

FONT_BIG_RESULT = ("Courier New", 60, "bold")
FONT_MID_RESULT = ("Courier New", 35, "bold")


class ReactionGameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Reaction Speed Game")  # 제목

        # 화면 크기 설정
        self.w = self.root.winfo_screenwidth()
        self.h = self.root.winfo_screenheight()
        self.cx = self.w // 2
        self.cy = self.h // 2

        self.root.geometry(f"{self.w}x{self.h}")
        self.root.attributes('-fullscreen', True)
        self.root.bind("<Escape>", lambda event: self.on_closing())  # ESC키 종료

        # 아두이노 및 DB 초기화
        self.board = None
        self.setup_arduino()
        self.init_db()

        self.players = []
        self.results = {}
        self.start_time = 0
        self.is_waiting = False

        # 배경 이미지 업로드
        self.images = {}
        self.pil_images = {}
        self.load_images()

        self.container = tk.Frame(self.root)
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        for F in (StartPage, PlayerEntryPage, GamePage, ResultPage, StatsPage):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("StartPage")

    # 종료 처리
    def on_closing(self):
        if self.board: self.board.exit()
        try:
            self.conn.close()
        except:
            pass
        self.root.destroy()
        sys.exit()

    def load_images(self):
        img_files = {
            "main": "bg_main.png",
            "ready": "bg_ready.png",
            "go": "bg_go.png",
            "stats": "bg_stats.png"
        }
        script_dir = os.path.dirname(__file__)
        for key, filename in img_files.items():
            try:
                path = os.path.join(script_dir, filename)
                img = Image.open(path)
                img = img.resize((self.w, self.h), Image.Resampling.LANCZOS)
                self.pil_images[key] = img
                self.images[key] = ImageTk.PhotoImage(img)
                print(f"[{filename}] 업로드 완료")  # 이미지 업로드 확인용
            except:
                self.images[key] = None
                self.pil_images[key] = None

    def setup_arduino(self):
        print("아두이노 연결 시도 중...")
        try:
            self.board = pyfirmata2.Arduino(pyfirmata2.Arduino.AUTODETECT)

            # 통신 주기 설정
            self.board.samplingOn(10)
            self.pins = []

            # A1 (Player 1)
            p1 = self.board.get_pin('a:1:i')
            p1.register_callback(lambda data: self.handle_input(0, data))
            self.pins.append(p1)

            # A2 (Player 2)
            p2 = self.board.get_pin('a:2:i')
            p2.register_callback(lambda data: self.handle_input(1, data))
            self.pins.append(p2)

            # A3 (Player 3)
            p3 = self.board.get_pin('a:3:i')
            p3.register_callback(lambda data: self.handle_input(2, data))
            self.pins.append(p3)

            print("arduino connected successfully!")

        except Exception as e:
            print(f"ERROR: {e}")
            self.board = None

    # 데이터베이스 초기화
    def init_db(self):
        self.conn = sqlite3.connect("game_history.db", check_same_thread=False)  # DB 연결
        self.cursor = self.conn.cursor()  # 커서 생성
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS history (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                player_name TEXT, reaction_time REAL, played_at TEXT)''')  # 테이블 생성
        self.conn.commit()

    # 화면 전환
    def show_frame(self, page_name):
        frame = self.frames[page_name]  # 현재 프레임 가져오기
        frame.tkraise()  # 프레임 올리기
        # 화면 전환시 on_show 메서드 호출
        if hasattr(frame, "on_show"):  # 페이지별 on_show 메서드 호출
            frame.on_show()

    # 게임 로직 시작
    def start_game_logic(self):
        count = len(self.players)  # player 수
        self.results = {i: None for i in range(count)}  # 결과 초기화
        self.is_waiting = False  # 입력 대기 상태 초기화

        game_page = self.frames["GamePage"]  # 게임 페이지 프레임
        game_page.set_status("ready")  # 준비 상태 설정
        delay = random.randint(2000, 5000)  # 2~5초 랜덤으로 대기
        self.root.after(delay, self.go_signal)  # 대기 후 GO 신호

    # GO 신호
    def go_signal(self):
        self.frames["GamePage"].set_status("go")  # GO 상태 설정
        self.start_time = time.perf_counter()  # 시간 기록 시작
        self.is_waiting = True  # 입력 대기 상태 설정

    # 입력 처리
    def handle_input(self, player_idx, data):

        if data is not None and data < 0.5:
            print(f"[DEBUG] Pin A{player_idx + 1} 눌림 감지! 값: {data}")

        if player_idx >= len(self.players):
            return

        if data < 0.2 and self.is_waiting:

            if self.results[player_idx] is None:
                reaction = time.perf_counter() - self.start_time
                self.results[player_idx] = reaction

                print(f"🎉 Player {player_idx + 1} 성공! 기록: {reaction * 1000:.1f}ms")

                # UI 업데이트
                self.root.after(0, lambda: self._update_ui_after_input(player_idx, reaction))

    # UI 업데이트 및 결과 확인
    def _update_ui_after_input(self, player_idx, reaction):
        self.save_record(self.players[player_idx], reaction)  # 기록 저장
        self.frames["GamePage"].update_player_text(player_idx, reaction)  # UI 업데이트
        active_results = [self.results[i] for i in range(len(self.players))]  # 모든 플레이어 결과 확인
        if all(val is not None for val in active_results):  # 모든 플레이어가 입력했는지 확인
            self.is_waiting = False  # 입력 대기 상태 해제
            self.root.after(1000, lambda: self.show_frame("ResultPage"))  # 1초 후 결과 페이지로 이동

    # 기록 저장
    def save_record(self, name, r_time):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 현재 시간
        self.cursor.execute("INSERT INTO history (player_name, reaction_time, played_at) VALUES (?, ?, ?)",
                            (name, r_time * 1000, now))  # ms 단위로 저장
        self.conn.commit()

    # 통계 데이터 가져오기
    def get_stats(self, name):
        self.cursor.execute("SELECT played_at, reaction_time FROM history WHERE player_name = ?", (name,))  # 데이터 조회
        return self.cursor.fetchall()  # 결과 반환하기

    # 모든 플레이어 이름 가져오기
    def get_all_player_names(self):
        self.cursor.execute("SELECT DISTINCT player_name FROM history ORDER BY player_name ASC")  # 이름 검색하기
        return [row[0] for row in self.cursor.fetchall()]  # 이름 리스트 반환하기


# 각 페이지 클래스 정의
class StartPage(tk.Frame):
    def __init__(self, parent, controller):  # StartPage 초기화
        tk.Frame.__init__(self, parent)  # 프레임 초기화
        self.controller = controller  # 컨트롤러 저장

        self.canvas = tk.Canvas(self, width=controller.w, height=controller.h, highlightthickness=0)  # 캔버스 생성
        self.canvas.pack(fill="both", expand=True)  # 캔버스 채우기

        if controller.images.get("main"):  # 배경 이미지 설정
            self.canvas.create_image(0, 0, image=controller.images["main"], anchor="nw")
        else:
            self.canvas.config(bg="#202020")  # 배경색 설정

        cx, cy = controller.cx, controller.cy  # 중앙 좌표

        self.canvas.create_text(cx, cy * 0.4, text="REACTION SPEED GAME", font=FONT_TITLE, fill="white")  # 타이틀 텍스트

        # 메뉴 아이템 생성
        def create_menu_item(text, y_pos, command):
            item = self.canvas.create_text(cx, y_pos, text=text, font=FONT_NORMAL, fill="white", activefill="#cccccc")

            def on_enter(event):
                self.canvas.itemconfig(item, text=f"> {text} <", font=FONT_HOVER, fill="yellow")
                self.canvas.config(cursor="hand2")

            def on_leave(event):
                self.canvas.itemconfig(item, text=text, font=FONT_NORMAL, fill="white")
                self.canvas.config(cursor="")

            self.canvas.tag_bind(item, "<Enter>", on_enter)  # 호버 효과
            self.canvas.tag_bind(item, "<Leave>", on_leave)
            self.canvas.tag_bind(item, "<Button-1>", lambda e: command())  # 클릭 이벤트 바인딩

        create_menu_item("GAME START", cy * 1.1, lambda: controller.show_frame("PlayerEntryPage"))  # Game Start
        create_menu_item("STATS", cy * 1.3, lambda: controller.show_frame("StatsPage"))  # Stats
        create_menu_item("EXIT", cy * 1.5, lambda: controller.on_closing())  # Exit


# 플레이어 입력 페이지
class PlayerEntryPage(tk.Frame):
    # 초기화
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.entry_widgets = []
        self.canvas_items = []

        self.canvas = tk.Canvas(self, width=controller.w, height=controller.h, highlightthickness=0)  # 캔버스 생성
        self.canvas.pack(fill="both", expand=True)
        self.bg_id = self.canvas.create_image(0, 0, anchor="nw")  # 배경 이미지

        self.canvas.create_text(controller.cx, controller.cy * 0.35, text="PLAYER ENTRY", font=FONT_TITLE, fill="white")

        self.add_btn = self.canvas.create_text(controller.w - 250, 100, text="+ ADD PLAYER", font=FONT_NORMAL,
                                               fill="white")

        def on_enter_add(e):
            self.canvas.itemconfig(self.add_btn, fill="yellow")
            self.canvas.config(cursor="hand2")

        def on_leave_add(e):
            self.canvas.itemconfig(self.add_btn, fill="white")
            self.canvas.config(cursor="")

        self.canvas.tag_bind(self.add_btn, "<Button-1>", lambda e: self.add_player_field())
        self.canvas.tag_bind(self.add_btn, "<Enter>", on_enter_add)
        self.canvas.tag_bind(self.add_btn, "<Leave>", on_leave_add)

        self.go_btn = self.canvas.create_text(controller.cx, controller.h * 0.85, text="GO >", font=FONT_TITLE,
                                              fill="white")
        self.canvas.tag_bind(self.go_btn, "<Button-1>", lambda e: self.start_game())

        def on_enter_go(e):
            self.canvas.itemconfig(self.go_btn, fill="yellow", text="GO >>>")
            self.canvas.config(cursor="hand2")

        def on_leave_go(e):
            self.canvas.itemconfig(self.go_btn, fill="white", text="GO >")
            self.canvas.config(cursor="")

        self.canvas.tag_bind(self.go_btn, "<Enter>", on_enter_go)
        self.canvas.tag_bind(self.go_btn, "<Leave>", on_leave_go)

        back_btn = self.canvas.create_text(150, 100, text="< BACK", font=FONT_NORMAL, fill="white")

        def on_enter_back(e):
            self.canvas.itemconfig(back_btn, fill="yellow", text="<< BACK")
            self.canvas.config(cursor="hand2")

        def on_leave_back(e):
            self.canvas.itemconfig(back_btn, fill="white", text="< BACK")
            self.canvas.config(cursor="")

        self.canvas.tag_bind(back_btn, "<Button-1>", lambda e: controller.show_frame("StartPage"))
        self.canvas.tag_bind(back_btn, "<Enter>", on_enter_back)
        self.canvas.tag_bind(back_btn, "<Leave>", on_leave_back)

    # 페이지 표시할 경우 초기화
    def on_show(self):
        if self.controller.images.get("main"):
            self.canvas.itemconfig(self.bg_id, image=self.controller.images["main"])
        else:
            self.canvas.config(bg="#202020")

        self.reset_inputs()
        self.add_player_field()  # 최소 1명 입력창

    # 입력 공간 초기화
    def reset_inputs(self):
        for item in self.canvas_items:
            self.canvas.delete(item)
        self.canvas_items = []
        self.entry_widgets = []

    # 플레이어 입력창 추가
    def add_player_field(self):
        count = len(self.entry_widgets)
        if count >= 3:
            messagebox.showinfo("Info", "Maximum 3 players allowed.")
            return

        cx, cy = self.controller.cx, self.controller.cy
        start_y = cy * 0.55
        gap_y = 120
        current_y = start_y + (count * gap_y)

        lbl_id = self.canvas.create_text(cx - 200, current_y, text=f"Player {count + 1}:", font=FONT_NORMAL,
                                         fill="white", anchor="e")
        self.canvas_items.append(lbl_id)

        entry_bg = "#202020"
        if self.controller.pil_images.get("main"):
            try:
                pil_img = self.controller.pil_images["main"]
                px, py = int(cx), int(current_y)
                if 0 <= px < pil_img.width and 0 <= py < pil_img.height:
                    r, g, b = pil_img.getpixel((px, py))
                    entry_bg = f"#{r:02x}{g:02x}{b:02x}"
            except:
                pass

        entry = tk.Entry(self, font=FONT_NORMAL, width=20, bd=0, relief="flat",
                         bg=entry_bg, fg="white", insertbackground="white")

        # 엔터키를 누르면 플레이어 추가
        entry.bind("<Return>", lambda e: self.add_player_field())

        win_id = self.canvas.create_window(cx - 150, current_y, window=entry, anchor="w")
        line_id = self.canvas.create_line(cx - 150, current_y + 20, cx + 150, current_y + 20, fill="white", width=2)

        self.canvas_items.append(win_id)
        self.canvas_items.append(line_id)
        self.entry_widgets.append(entry)

        entry.focus_set()

    # 게임 시작
    def start_game(self):
        names = []
        for e in self.entry_widgets:  # 입력값 수집
            name = e.get().strip()
            if not name:
                messagebox.showerror("ERROR", "nickname cannot be empty.")
                return
            names.append(name)
        self.controller.players = names  # 플레이어 이름 설정
        self.controller.show_frame("GamePage")


# 게임 페이지
class GamePage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        self.canvas = tk.Canvas(self, width=controller.w, height=controller.h, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.bg_item = self.canvas.create_image(0, 0, anchor="nw")

        self.status_text = self.canvas.create_text(controller.cx, controller.cy, text="", font=FONT_GAME_STATUS,
                                                   fill="white")
        self.player_text_ids = []

    def on_show(self):
        for tid in self.player_text_ids:
            self.canvas.delete(tid)
        self.player_text_ids = []

        p_count = len(self.controller.players)  # 플레이어 수
        section_w = self.controller.w // p_count  # \
        text_y = self.controller.h * 0.8

        for i in range(p_count):  # 플레이어별 텍스트 아이디 생성
            pos_x = (section_w * i) + (section_w // 2)
            tid = self.canvas.create_text(pos_x, text_y, text="", font=FONT_NORMAL, fill="white")
            self.player_text_ids.append(tid)

        self.controller.start_game_logic()

    # 상태 설정
    def set_status(self, status):
        img_key = "ready" if status == "ready" else "go"
        text_str = "Ready..." if status == "ready" else "GO!!!"
        text_col = "black" if status == "ready" else "white"

        if self.controller.images.get(img_key):  # 배경 이미지 설정
            self.canvas.itemconfig(self.bg_item, image=self.controller.images[img_key])
        else:
            self.canvas.config(bg="yellow" if status == "ready" else "green")
            self.canvas.itemconfig(self.bg_item, image="")
        self.canvas.itemconfig(self.status_text, text=text_str, fill=text_col)

    # 플레이어 텍스트 업데이트
    def update_player_text(self, idx, time_val):
        ms = time_val * 1000  # ms 변환
        self.canvas.itemconfig(self.player_text_ids[idx], text=f"{self.controller.players[idx]}\n{ms:.1f}ms",
                               fill="yellow")


# 결과 페이지
class ResultPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        self.canvas = tk.Canvas(self, width=controller.w, height=controller.h, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.bg_id = self.canvas.create_image(0, 0, anchor="nw")

        cx, cy = controller.cx, controller.cy

        self.canvas.create_text(cx, cy * 0.35, text="FINAL RESULT", font=FONT_TITLE, fill="white")
        self.rank_ids = []

        home_btn = self.canvas.create_text(cx, controller.h * 0.85, text="MAIN MENU", font=FONT_TITLE, fill="white")

        def on_enter(e): self.canvas.itemconfig(home_btn, fill="yellow", text="> MAIN MENU <")

        def on_leave(e): self.canvas.itemconfig(home_btn, fill="white", text="MAIN MENU")

        self.canvas.tag_bind(home_btn, "<Button-1>", lambda e: controller.show_frame("StartPage"))
        self.canvas.tag_bind(home_btn, "<Enter>", on_enter)
        self.canvas.tag_bind(home_btn, "<Leave>", on_leave)

    # 페이지 표시 시 결과 업데이트
    def on_show(self):
        if self.controller.images.get("main"):
            self.canvas.itemconfig(self.bg_id, image=self.controller.images["main"])

        for tid in self.rank_ids: self.canvas.delete(tid)  # `이전 결과 삭제
        self.rank_ids = []  # 결과 아이디 초기화

        results = self.controller.results  # 결과 가져오기
        players = self.controller.players  # 플레이어 이름 가져오기

        valid = []
        for idx in range(len(players)):  # 결과 정리
            t = results.get(idx)
            if t is not None:
                valid.append((t, players[idx]))
            else:
                valid.append((9999, players[idx] + "(Fail)"))
        valid.sort()

        cx, cy = self.controller.cx, self.controller.cy

        if len(valid) > 0:  # 1등
            t, n = valid[0]
            txt = f"🥇 {n}\n{t * 1000:.1f}ms" if t != 9999 else f"🥇 {n}"
            tid = self.canvas.create_text(cx, cy * 0.8, text=txt, font=FONT_BIG_RESULT, fill="gold")
            self.rank_ids.append(tid)

        if len(valid) > 1:  # 2등
            t, n = valid[1]
            txt = f"🥈 {n}\n{t * 1000:.1f}ms" if t != 9999 else f"🥈 {n}"
            tid = self.canvas.create_text(cx - 400, cy + 150, text=txt, font=FONT_MID_RESULT, fill="silver")
            self.rank_ids.append(tid)

        if len(valid) > 2:  # 3등
            t, n = valid[2]
            txt = f"🥉 {n}\n{t * 1000:.1f}ms" if t != 9999 else f"🥉 {n}"
            tid = self.canvas.create_text(cx + 400, cy + 150, text=txt, font=FONT_MID_RESULT, fill="#cd7f32")
            self.rank_ids.append(tid)


# 통계 페이지
class StatsPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller

        self.canvas = tk.Canvas(self, width=controller.w, height=controller.h, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.bg_id = self.canvas.create_image(0, 0, anchor="nw")

        self.chart_widget = None

    def on_show(self):
        if self.controller.images.get("stats"):
            self.canvas.itemconfig(self.bg_id, image=self.controller.images["stats"])
        else:
            self.canvas.config(bg="white")
            self.canvas.itemconfig(self.bg_id, image="")

        self.canvas.delete("ui")
        if self.chart_widget:
            self.chart_widget.destroy()
            self.chart_widget = None

        self.draw_interface()
        self.load_player_list()

    def draw_interface(self):
        left_margin = self.controller.w * 0.1
        top_margin = self.controller.h * 0.15

        back_btn = self.canvas.create_text(self.controller.w - 150, top_margin, text="BACK", font=FONT_NORMAL,
                                           fill="black", tags="ui")

        def on_enter_back(e):
            self.canvas.itemconfig(back_btn, text="> BACK <", fill="gray")

        def on_leave_back(e):
            self.canvas.itemconfig(back_btn, text="BACK", fill="black")

        self.canvas.tag_bind(back_btn, "<Button-1>", lambda e: self.controller.show_frame("StartPage"))
        self.canvas.tag_bind(back_btn, "<Enter>", on_enter_back)
        self.canvas.tag_bind(back_btn, "<Leave>", on_leave_back)

        self.canvas.create_text(left_margin, top_margin, text="NICKNAME:", font=FONT_NORMAL, fill="black", anchor="w",
                                tags="ui")

        entry_bg = "#ffffff"
        entry_x = int(left_margin)
        entry_y = int(top_margin + 50)

        # 배경 이미지에서 색상 추출 (닉네임 입력창 배경을 투명으로 보이게 하기 위함)
        if self.controller.pil_images.get("stats"):
            try:
                pil_img = self.controller.pil_images["stats"]
                if 0 <= entry_x < pil_img.width and 0 <= entry_y < pil_img.height:
                    r, g, b = pil_img.getpixel((entry_x, entry_y))
                    entry_bg = f"#{r:02x}{g:02x}{b:02x}"
            except:
                pass

        self.search_entry = tk.Entry(self, font=FONT_NORMAL, width=15, bd=0, relief="flat",
                                     bg=entry_bg, fg="black", insertbackground="black")

        self.canvas.create_window(left_margin, entry_y, window=self.search_entry, anchor="w", tags="ui")
        self.canvas.create_line(left_margin, entry_y + 20, left_margin + 200, entry_y + 20, fill="black", width=2,
                                tags="ui")

        # 엔터키 바인딩
        self.search_entry.bind("<Return>", lambda e: self.on_search())

        # 돋보기 버튼
        search_label = tk.Label(self, text="🔍", font=("Arial", 20), bg=entry_bg, fg="black", cursor="hand2")
        self.canvas.create_window(left_margin + 220, entry_y, window=search_label, tags="ui")
        search_label.bind("<Button-1>", lambda e: self.on_search())

    # 플레이어 리스트 업로드
    def load_player_list(self):
        names = self.controller.get_all_player_names()

        list_frame = tk.Frame(self, bg="white")
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        # listbox 생성
        self.listbox = tk.Listbox(list_frame, font=("Courier New", 15), bg="white", fg="black",
                                  height=20, width=20, bd=1, highlightthickness=0,
                                  selectbackground="#e0e0e0", selectforeground="black",
                                  yscrollcommand=scrollbar.set)
        self.listbox.pack(side="left", fill="both")
        scrollbar.config(command=self.listbox.yview)

        for name in names:  # 이름 추가
            self.listbox.insert(tk.END, name)

        self.listbox.bind('<<ListboxSelect>>', self.on_list_select)

        list_y = self.controller.h * 0.15 + 100
        self.canvas.create_window(self.controller.w * 0.1, list_y, window=list_frame, anchor="nw", tags="ui")

    # 검색 처리
    def on_search(self):
        name = self.search_entry.get().strip()  # 입력값 가져오기
        self.draw_graph(name)  # 그래프 그리기

    # 리스트 선택 처리
    def on_list_select(self, event):
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            name = event.widget.get(index)
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, name)
            self.draw_graph(name)

    # 그래프 그리기
    def draw_graph(self, name):
        if not name: return

        if self.chart_widget:  # 이전 그래프 삭제
            self.chart_widget.destroy()

        data = self.controller.get_stats(name)  # 데이터 가져오기
        if not data:
            messagebox.showinfo("INFO", "No data found.")
            return

        x_labels = []
        y_values = []
        date_counts = {}

        for row in data:  # 데이터 처리
            dt_str = row[0]
            try:  # 날짜 형식 변환
                dt_obj = datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
                date_key = dt_obj.strftime("%m.%d")
            except:
                date_key = dt_str

            if date_key not in date_counts:  # 중복 날짜 카운트
                date_counts[date_key] = 1
            else:
                date_counts[date_key] += 1

            label = f"{date_key}({date_counts[date_key]})"
            x_labels.append(label)
            y_values.append(row[1])

        fig = plt.Figure(figsize=(8, 5), dpi=100)
        ax = fig.add_subplot(111)

        ax.plot(x_labels, y_values, marker='o', linestyle='-', color='black', linewidth=2)
        ax.set_title(f"{name}'s History", fontsize=15)
        ax.set_ylabel("Time (ms)", fontsize=12)
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, linestyle='--', alpha=0.5)

        fig.tight_layout()

        chart_canvas = FigureCanvasTkAgg(fig, self)
        self.chart_widget = chart_canvas.get_tk_widget()

        self.canvas.create_window(self.controller.w * 0.35, self.controller.h * 0.25, window=self.chart_widget,
                                  anchor="nw", tags="ui")


if __name__ == "__main__":
    root = tk.Tk()
    app = ReactionGameApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()  # 메인 루프 실행