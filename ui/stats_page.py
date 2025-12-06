import datetime
import tkinter as tk
from tkinter import messagebox

from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .typography import Typography


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

        self.canvas.create_text(cx - 100, 80, text="|", font=Typography.FONT_STATS_TAB, fill="black", tags="ui")
        self.canvas.create_text(cx + 100, 80, text="|", font=Typography.FONT_STATS_TAB, fill="black", tags="ui")

        positions = [(cx - 200, "GAME 1", "GAME1"), (cx, "GAME 2", "GAME2"), (cx + 200, "GAME 3", "GAME3")]

        # 통계 탭 생성
        for x, text, mode in positions:
            is_selected = (self.selected_game.get() == mode)
            color = "blue" if is_selected else "black"
            font = Typography.FONT_STATS_TAB_HOVER if is_selected else Typography.FONT_STATS_TAB

            btn = self.canvas.create_text(x, 80, text=text, font=font, fill=color, tags="ui")

            def on_enter(e, item=btn, m=mode):
                self.canvas.itemconfig(item, fill="blue", font=Typography.FONT_STATS_TAB_HOVER)
                self.canvas.config(cursor="hand2")

            def on_leave(e, item=btn, m=mode):
                if self.selected_game.get() == m:
                    self.canvas.itemconfig(item, fill="blue", font=Typography.FONT_STATS_TAB_HOVER)
                else:
                    self.canvas.itemconfig(item, fill="black", font=Typography.FONT_STATS_TAB)
                self.canvas.config(cursor="")

            self.canvas.tag_bind(btn, "<Button-1>", lambda e, m=mode: self.change_mode(m))
            self.canvas.tag_bind(btn, "<Enter>", lambda e, b=btn, m=mode: on_enter(e, b, m))
            self.canvas.tag_bind(btn, "<Leave>", lambda e, b=btn, m=mode: on_leave(e, b, m))

        back = self.canvas.create_text(120, 80, text="< BACK", font=Typography.FONT_NORMAL, fill="black", tags="ui")

        def on_enter_back(e):
            self.canvas.itemconfig(back, fill="#CCCC00", font=Typography.FONT_HOVER)
            self.canvas.config(cursor="hand2")

        def on_leave_back(e):
            self.canvas.itemconfig(back, fill="black", font=Typography.FONT_NORMAL)
            self.canvas.config(cursor="")

        self.canvas.tag_bind(back, "<Button-1>", lambda e: self.controller.show_frame("StartPage"))
        self.canvas.tag_bind(back, "<Enter>", on_enter_back)
        self.canvas.tag_bind(back, "<Leave>", on_leave_back)

        self.canvas.create_text(300, 200, text="NICKNAME:", font=Typography.FONT_NORMAL, fill="black", anchor="e", tags="ui")

        self.entry = tk.Entry(self, font=Typography.FONT_NORMAL, width=15, bg="white", fg="black",
                              bd=0, highlightthickness=0, relief="flat")
        self.canvas.create_window(450, 200, window=self.entry, tags="ui")

        self.canvas.create_line(350, 220, 550, 220, fill="black", width=2, tags="ui")

        search_btn = self.canvas.create_text(600, 200, text="🔍", font=Typography.FONT_NORMAL, fill="black", tags="ui")
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
