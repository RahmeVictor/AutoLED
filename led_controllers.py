import json
import math
import os.path

try:
    import RPi.GPIO as GPIO

except ImportError:
    import warnings
    import GPIOSim as GPIO

    warnings.warn("USING GPIO EMULATOR, INSTALL Rpi.GPIO", RuntimeWarning)

CONTROLLER_FILE_PATH: str = 'controllers.json'


class ControllerChain:
    """
    Chain of P9813 based controller. Responsible for sending data to the controllers through the GPIO pins.
    """

    def __init__(self, clockPin: int = 27, dataPin: int = 17):
        self.cid: int = -1  # Chain id
        self.controllers: list[LEDController] = []
        self.dataPin: int = dataPin
        self.clockPin: int = clockPin

        # Set GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.clockPin, GPIO.OUT)
        GPIO.setup(self.dataPin, GPIO.OUT)
        self.reset()
        self.load_controllers()
        if not self.controllers:
            self.add_controller()

    def __setitem__(self, index: int, controller: 'LEDController') -> None:
        self.controllers[index] = controller
        controller.id = self.get_id(controller)

    def __getitem__(self, item) -> 'LEDController':
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

    def add_controller(self, name: str = 'Default name') -> 'LEDController':
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
        """
        Objects are saved in JSON format as follows:
        {ChainID(1): [controller1, controller2, ...], ChainID(2):[...], ...}
        Where controller1, controller2 etc. is the data associated with the controller as a dict.
        """

        savedControllers = {self.cid: []}
        dataToSave = ['name', 'color']  # Name of controller proprieties to save
        for controller in self.controllers:
            # Create a dict with the controller data
            controllerDict: dict = {}
            for data in dataToSave:
                controllerDict[data] = getattr(controller, data)

            # Add the controller data to the list. The id is saved as the index in the list
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


class LEDController:
    """
    Class that holds data about a controller. Color is passed as a tuple (red, green, blue).
    The id is the same as the index in the controller chain and is set by the chain automatically.
    """

    def __init__(self, chain: ControllerChain, name: str = "Controller 1"):
        self.name: str = name
        self.chain: ControllerChain = chain  # Chain that owns this controller
        self.cid: int = -1  # Controller ID
        self.red: int = 0
        self.green: int = 0
        self.blue: int = 0

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

    @staticmethod
    def kelvin2rgb(colorTemperature: float) -> tuple[int, int, int]:
        """
        Converts from K to RGB, algorithm courtesy of
        https://gist.github.com/petrklus/b1f427accdf7438606a6
        """
        # range check
        if colorTemperature < 1000:
            colorTemperature = 1000
        elif colorTemperature > 40000:
            colorTemperature = 40000

        tmpInternal = colorTemperature / 100.0

        # Red
        if tmpInternal <= 66:
            red = 255
        else:
            tmp_red = 329.698727446 * (tmpInternal - 60 ** 0.1332047592)
            if tmp_red < 0:
                red = 0
            elif tmp_red > 255:
                red = 255
            else:
                red = tmp_red

        # Green
        if tmpInternal <= 66:
            tmp_green = 99.4708025861 * math.log(tmpInternal) - 161.1195681661
            if tmp_green < 0:
                green = 0
            elif tmp_green > 255:
                green = 255
            else:
                green = tmp_green
        else:
            tmp_green = 288.1221695283 * (tmpInternal - 60 ** -0.0755148492)
            if tmp_green < 0:
                green = 0
            elif tmp_green > 255:
                green = 255
            else:
                green = tmp_green

        # Blue
        if tmpInternal >= 66:
            blue = 255
        elif tmpInternal <= 19:
            blue = 0
        else:
            tmp_blue = 138.5177312231 * math.log(tmpInternal - 10) - 305.0447927307
            if tmp_blue < 0:
                blue = 0
            elif tmp_blue > 255:
                blue = 255
            else:
                blue = tmp_blue

        return int(red), int(green), int(blue)

    def get_hex_color(self) -> str:
        return self.rgb2hex(*self.color)
