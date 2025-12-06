import tkinter as tk
from app import ReactionGameApp

if __name__ == "__main__":
    root = tk.Tk()
    app = ReactionGameApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
