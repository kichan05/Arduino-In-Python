import datetime
import sqlite3
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, "game_history.db")

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS history (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                player_name TEXT, 
                                reaction_time REAL, 
                                played_at TEXT,
                                game_mode TEXT,
                                score INTEGER
                                )''')
        self.conn.commit()

    def save_record(self, game_mode, name, r_time, score):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute(
            f"""INSERT INTO history
                    (game_mode, player_name, reaction_time, score, played_at)
                VALUES
                    (?, ?, ?, ?, ?)
            """,
            (game_mode, name, r_time * 1000, score, now)
        )
        self.conn.commit()

    def get_stats_by_player(self, game_mode, player_name):
        self.cursor.execute(
            """SELECT
                played_at, score
            FROM
                history
            WHERE
                game_mode = ? AND player_name = ?
            """,
            (game_mode, player_name)
        )
        return self.cursor.fetchall()

    def get_all_player_names(self):
        self.cursor.execute(
            """
                SELECT
                    DISTINCT player_name
                FROM
                    history
                ORDER BY
                    player_name ASC
            """
        )
        return [row[0] for row in self.cursor.fetchall()]

    def close(self):
        self.conn.close();
