import os.path
import json

try:
    import RPi.GPIO as GPIO

except ImportError:
    import warnings
    import GPIOSim as GPIO

    warnings.warn("USING GPIO EMULATOR, INSTALL Rpi.GPIO", RuntimeWarning)

CONTROLLER_FILE_PATH = 'controllers.json'


class ControllerChain:
    # P9813 based controller
    def __init__(self, clockPin: int = 27, dataPin: int = 17):
        self.cid: int = -1  # Chain id
        self.controllers = []
        self.dataPin: int = dataPin
        self.clockPin: int = clockPin

        # Set GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.clockPin, GPIO.OUT)
        GPIO.setup(self.dataPin, GPIO.OUT)
        self.reset()
        self.load_controllers()
        print(self.controllers)
        if not self.controllers:
            self.add_controller()

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

    def write(self) -> None:
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
        self.save_controllers()
        return controller

    def delete_controller(self, cid: int) -> None:
        if len(self.controllers) <= 1:
            return  # Can't delete last controller

        controller = self.controllers[cid]
        self.controllers.remove(controller)

        # Update controller ids
        for controllerToUpdate in self.controllers:
            controllerToUpdate.cid = self.get_id(controllerToUpdate)

        self.save_controllers()

    def check_id_is_valid(self, cid: int) -> bool:
        if 0 <= cid < len(self.controllers) and len(self.controllers) > 0:
            return True

        return False

    def save_controllers(self) -> None:
        savedControllers = {self.cid: []}
        dataToSave = ['name', 'color']
        for controller in self.controllers:
            controllerDict = {}
            for data in dataToSave:
                controllerDict[data] = getattr(controller, data)

            savedControllers[self.cid].append(controllerDict)

        with open(CONTROLLER_FILE_PATH, 'w') as writeFile:
            json.dump(savedControllers, writeFile)

    def load_controllers(self) -> None:
        if not os.path.exists(CONTROLLER_FILE_PATH):
            return  # If file does not exist, don't load anything

        # Delete all controllers
        for controller in self.controllers:
            self.delete_controller(controller.cid)

        with open(CONTROLLER_FILE_PATH, "r") as readFile:
            data = json.load(readFile)
            savedControllers = data[str(self.cid)]
            for savedController in savedControllers:
                controller = self.add_controller()
                for key in savedController:
                    setattr(controller, key, savedController[key])

    def __setitem__(self, index, controller):
        self.controllers[index] = controller
        controller.id = self.get_id(controller)

    def __getitem__(self, item):
        return self.controllers[item]

    def _frame(self) -> None:
        # Send 32x zeros
        GPIO.output(self.dataPin, 0)
        for i in range(32):
            self._clk()

    def _clk(self) -> None:
        GPIO.output(self.clockPin, 0)
        GPIO.output(self.clockPin, 1)

    def _write_byte(self, b) -> None:
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
    # The id is the same as the index in the controller chain
    def __init__(self, chain: ControllerChain, name: str = "Controller 1"):
        self._warmth: int = 100
        self.name: str = name
        self.cid: int = -1  # Controller ID
        self.red: int = 0
        self.green: int = 0
        self.blue: int = 0
        self.chain: ControllerChain = chain  # Chain that owns this controller

    @property
    def color(self) -> tuple:
        return self.red, self.green, self.blue

    @color.setter
    def color(self, value: tuple) -> None:
        self.red, self.green, self.blue = value
        self.chain.write()
        self.chain.save_controllers()

    @staticmethod
    def rgb2hex(r: int, g: int, b: int) -> str:
        return '#' + ''.join(f'{i:02X}' for i in (r, g, b))

    @staticmethod
    def hex2rgb(h: str) -> tuple:
        h = h.lstrip('#')
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    def get_hex_color(self) -> str:
        return self.rgb2hex(*self.color)
