import tkinter as tk

import pyfirmata2

from app import ReactionGameApp
from arduino_manager import ArduinoManager

if __name__ == "__main__":
    # root = tk.Tk()
    # app = ReactionGameApp(root)
    # root.protocol("WM_DELETE_WINDOW", app.on_closing)
    # root.mainloop()

    def on_click():
        print("Hello World")

    uno = ArduinoManager(PORT=pyfirmata2.Arduino.AUTODETECT)
    uno.on_click("a:1:i", on_click)

    input()