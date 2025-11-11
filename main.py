import numpy as np
from arduino import Arduino

if __name__ == '__main__':
    uno = Arduino(PORT="COM6")

    click_count = np.array([0, 0, 0])


    def a1u_click_callback(index: int):
        global click_count, uno
        click_count[index] += 1
        print(f"{click_count}번 클릭")

        if(click_count[0] > 10):
            uno.lef_blink(uno.LED_PINS, 5, 0.2)


    uno.add_on_click_event("a:1:u", lambda: a1u_click_callback(0))

    input()
