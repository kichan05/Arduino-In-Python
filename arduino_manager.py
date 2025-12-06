from typing import Callable
import time
import pyfirmata2


class ArduinoManager:
    DEBOUNCE_DELAY_MS = 200  # 200ms 이내의 클릭은 무시

    def __init__(self, PORT: str):
        self.PORT = PORT
        self.board = pyfirmata2.Arduino(PORT)

        self.SAMPLING_INTERVAL = 100
        self.LED_ON = 0
        self.LED_OFF = 1
        self.LED_PINS = [10, 11, 12, 13]

        self.BUZZER_PIN = 3

        self.board.samplingOn(self.SAMPLING_INTERVAL)

        self.__pin_callback: dict[str, Callable[[], None]] = {}
        self.__pin_click_time: dict[str, int] = {}

        pins_to_register = ['a:1:i', 'a:2:i', 'a:3:i']
        for pin in pins_to_register:
            self._register_internal_handler(pin)
            # self.__pin_callback[pin] = None
            self.__pin_click_time[pin] = 0


    def _register_internal_handler(self, pin: str):
        pin_obj = self.board.get_pin(pin)
        pin_obj.register_callback(lambda data: self._handle_input(pin, data))
        pin_obj.enable_reporting()

    def _handle_input(self, pin: str, v: float):
        if v > 0.5:
            return

        current_time_ms = int(time.time() * 1000)
        last_click_time_ms = self.__pin_click_time.get(pin, 0)

        if (current_time_ms - last_click_time_ms) > self.DEBOUNCE_DELAY_MS:
            self.__pin_click_time[pin] = current_time_ms
            if pin in self.__pin_callback and self.__pin_callback[pin] is not None:
                self.__pin_callback[pin]()

    def on_click(self, pin: str, callback: Callable[[], None]):
        self.__pin_callback[pin] = callback

    def close(self):
        if self.board:
            self.board.exit()