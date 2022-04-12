# import os.path
# import pickle

try:
    import RPi.GPIO as GPIO

except ImportError:
    print("USING GPIO EMULATOR, INSTALL Rpi.GPIO")
    import GPIOSim as GPIO

CONTROLLER_FILE_PATH = 'controllers.conf'


class ControllerChain:
    # P9813 based controller
    def __init__(self, clockPin: int = 27, dataPin: int = 17):
        self.controllers = []
        self.dataPin: int = dataPin
        self.clockPin: int = clockPin

        # Set GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.clockPin, GPIO.OUT)
        GPIO.setup(self.dataPin, GPIO.OUT)
        self.reset()

    def reset(self) -> None:
        # Begin data frame 4 bytes
        self._frame()
        # 4 bytes for each led (checksum, blue, green, red)
        for _i in self.controllers:
            self._write_byte(0xC0)
            for _j in range(3):
                self._write_byte(0)
        # End data frame 4 bytes
        self._frame()

    def write(self):
        # Begin data frame 4 bytes
        self._frame()

        # 4 bytes for each led (checksum, red, green, blue)
        for controller in self.controllers:
            self._write_color(*controller.color)

        # End data frame 4 bytes
        self._frame()

    def get_id(self, controller) -> int:
        return self.controllers.index(controller)

    def add_controller(self, name: str = 'Default name'):
        controller = LEDController(chain=self, name=name)
        self.controllers.append(controller)
        controller.cid = self.get_id(controller)
        return controller

    def delete_controller(self, cid: int) -> None:
        if len(self.controllers) <= 1:
            # Can't delete last controller
            return

        controller = self.controllers[cid]
        self.controllers.remove(controller)

    def check_id_is_valid(self, cid: int) -> bool:
        if 0 <= cid < len(self.controllers) and len(self.controllers) > 0:
            return True

        return False

    def __setitem__(self, index, controller):
        self.controllers[index] = controller
        controller.id = self.get_id(controller)

    def __getitem__(self, item):
        return self.controllers[item]

    def _frame(self):
        # Send 32x zeros
        GPIO.output(self.dataPin, 0)
        for i in range(32):
            self._clk()

    def _clk(self):
        GPIO.output(self.clockPin, 0)
        GPIO.output(self.clockPin, 1)

    def _write_byte(self, b):
        if b == 0:
            # Fast send 8x zeros
            GPIO.output(self.dataPin, 0)
            for i in range(8):
                self._clk()
        else:
            # Send each bit, MSB first
            for i in range(8):
                if (b & 0x80) != 0:
                    GPIO.output(self.dataPin, 1)
                else:
                    GPIO.output(self.dataPin, 0)
                self._clk()

                # On to the next bit
                b <<= 1

    def _write_color(self, r: int, g: int, b: int) -> None:
        # Send a checksum byte with the format "1 1 ~B7 ~B6 ~G7 ~G6 ~R7 ~R6"
        # The checksum colour bits should bitwise NOT the data colour bits
        checksum = 0xC0  # 0b11000000
        checksum |= (b >> 6 & 3) << 4
        checksum |= (g >> 6 & 3) << 2
        checksum |= (r >> 6 & 3)

        self._write_byte(checksum)

        # Send the 3 colours
        self._write_byte(b)
        self._write_byte(g)
        self._write_byte(r)


class LEDController:
    def __init__(self, chain, name: str = "Controller 1"):
        self._warmth = 100
        self.name = name
        self.red = 0
        self.green = 0
        self.blue = 0
        self.cid = -1
        self.chain = chain

    @property
    def color(self) -> tuple:
        return self.red, self.green, self.blue

    @color.setter
    def color(self, value: tuple) -> None:
        self.red, self.green, self.blue = value
        self.chain.write()

    @staticmethod
    def rgb2hex(r: int, g: int, b: int) -> str:
        return '#' + ''.join(f'{i:02X}' for i in (r, g, b))

    @staticmethod
    def hex2rgb(h: str) -> tuple:
        h = h.lstrip('#')
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
