import time
from typing import Iterable

import pyfirmata2

class Arduino:
    def __init__(self, PORT: str, FPS: float):
        self.PORT = PORT
        self.FPS = FPS

        self.board = pyfirmata2.Arduino(PORT)

        self.SAMPLING_INTERVAL = 100
        self.LED_ON = 0
        self.LED_OFF = 1
        self.LED_PINS = [10, 11, 12, 13]

        self.BUZZER_PIN = 3

        self.board.samplingOn(self.SAMPLING_INTERVAL)

        self.__pin_states : dict[str, float] = {}

    def __del__(self):
        if (self.board):
            self.board.exit();

    def led_on(self, pins: Iterable[int], gap: float = 0):
        for i in pins:
            self.board.digital[i].write(self.LED_ON)
            time.sleep(gap)

    def led_off(self, pins: Iterable[int], gap: float = 0):
        for i in pins:
            self.board.digital[i].write(self.LED_OFF)
            time.sleep(gap)

    def all_led_on(self, gap: float = 0):
        self.led_on(pins=self.LED_PINS, gap=gap)

    def all_led_off(self, gap: float = 0):
        self.led_off(pins=self.LED_PINS, gap=gap)

    def lef_blink(self, pins: Iterable[int], repeat: int, gap: float):
        self.led_off(pins=pins)

        for _ in range(repeat):
            self.led_on(pins)
            time.sleep(gap)

            self.led_off(pins)
            time.sleep(gap)

    def __register_pin(self, pin : str):
        self.__pin_states[pin] = 0

        def on_change(value):
            if (value < 0.5):
                self.__pin_states[pin] = time.time()
            else:
                self.__pin_states[pin] = 0


        pin_obj = self.board.get_pin(pin)
        pin_obj.register_callback(on_change)
        pin_obj.enable_reporting()


    def is_button_press(self, pin: str) -> bool:
        if(pin not in self.__pin_states):
            self.__register_pin(pin)

        current_pin_state = self.__pin_states[pin]
        return current_pin_state != 0

    def is_button_pressed(self, pin: str) -> bool:
        if(pin not in self.__pin_states):
            self.__register_pin(pin)

        current_pin_state = self.__pin_states[pin]
        current_time = time.time()
        return current_time - current_pin_state <= self.FPS

    def buzzer_sound(self, length : float):
        self.board.digital[self.BUZZER_PIN].write(self.LED_ON)
        time.sleep(length)
        self.board.digital[self.BUZZER_PIN].write(self.LED_OFF)

    def buzzer_dot(self):
        self.buzzer_sound(0.1)

    def buzzer_dash(self):
        self.buzzer_sound(0.5)