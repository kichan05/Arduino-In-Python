import time
import matplotlib.pyplot as plt
import numpy as np
from arduino import Arduino
import curses
from typing import List


class Unit:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def die(self):
        del self


def main(stdscr: curses.window):
    FPS = 0.016
    uno = Arduino(PORT="COM6", FPS=FPS)
    curses.curs_set(0)
    curses.start_color()

    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_BLACK)

    stdscr.nodelay(True)

    bullet_list: List[dict[str, int]] = []
    x, y = 0, 20

    while True:
        stdscr.clear()

        stdscr.addstr(0, 0, "Game controller with Arduino")
        stdscr.addstr(2, 0, f"Position : X={x}, Y={y}\t Bullet count : {len(bullet_list)}")

        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(y, x, "*")
        stdscr.attroff(curses.color_pair(2))

        for b in bullet_list:
            if (b["y"] <= 0):
                del b
                continue

            b["y"] -= 1
            stdscr.attron(curses.color_pair(1))
            stdscr.addch(b["y"], b["x"], "+")
            stdscr.attroff(curses.color_pair(1))

        if (uno.is_button_press("a:1:u")):
            if (x - 5 >= 0):
                x -= 1
        if (uno.is_button_press("a:3:u")):
            x += 1

        if (uno.is_button_pressed("a:2:u")):
            bullet_list.append({"x": x, "y": y})
            # uno.buzzer_dot()

        stdscr.refresh()
        time.sleep(FPS)


curses.wrapper(main)
