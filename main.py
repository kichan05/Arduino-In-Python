import time
import matplotlib.pyplot as plt
import numpy as np
from arduino import Arduino
import curses
from typing import List

click_count = np.array([[0, 0, 0], [0, 0, 0], [0, 0, 0]])

if __name__ == '__main__':
    uno = Arduino(PORT="COM6", FPS=1000)

    start_time = time.time()

    while time.time() - start_time < 30:
        index = (time.time() - start_time) // 3

        if(uno.is_button_pressed("a:1:u")):
            click_count[index, 0] += 1

        if (uno.is_button_pressed("a:2:u")):
            click_count[index, 1] += 1

        if(uno.is_button_pressed("a:3:u")):
            click_count[index, 2] += 1

        print(click_count)
