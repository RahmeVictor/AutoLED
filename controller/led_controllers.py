import json
import os.path

from controller.color import Color

try:
    import RPi.GPIO as GPIO

except ImportError:
    import warnings
    import controller.GPIOSim as GPIO

    warnings.warn("USING GPIO EMULATOR, INSTALL Rpi.GPIO", RuntimeWarning)

CONTROLLER_FILE_PATH: str = os.path.join(os.path.join(os.getcwd(), 'controller'), 'controllers.json')


class ControllerChain:
    """
    Chain of P9813 based controller. Responsible for sending data to the controllers through the GPIO pins.
    You can access a controller using its ID as index: ControllerChain[ControllerID]
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
        """ Send 32x zeros """
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
        """
        Send a checksum byte with the format "1 1 ~B7 ~B6 ~G7 ~G6 ~R7 ~R6"
        The checksum colour bits should bitwise NOT the data colour bits
        """
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
            self._write_color(*controller.color.rgb)

        # End data frame 4 bytes
        self._frame()

    def get_id(self, controller: 'LEDController') -> int:
        return self.controllers.index(controller)

    def add_controller(self, name: str = 'Default name', existingController=None) -> 'LEDController':
        if existingController:
            controller = existingController
            controller.chain = self
        else:
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
        Color data is saved as HSV
        """

        savedControllers = {self.cid: []}
        for controller in self.controllers:
            # Create a dict with the controller data
            controllerDict: dict = {'name': controller.name, 'color': controller.color.hsv}

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

        with open(CONTROLLER_FILE_PATH, 'r') as readFile:
            try:
                data = json.load(readFile)

            except json.JSONDecodeError:
                self.add_controller()
                return  # Save data was corrupt or didn't exist, create a new controller and exit

            savedControllers = data[str(self.cid)]
            for savedController in savedControllers:
                controller = self.add_controller()
                controller.name = savedController['name']
                controller.color.hsv = savedController['color']


class LEDController:
    """
    Class that holds data about a controller. Color is passed as a tuple (red, green, blue).
    The id is the same as the index in the controller chain and is set by the chain automatically.
    """

    def __init__(self, chain: ControllerChain = None, name: str = "Controller 1"):
        self.chain: ControllerChain = chain  # Chain that owns this controller
        self.name: str = name
        self.cid: int = -1  # Controller ID
        self.color: Color = Color(owner=self)

    def on_color_changed(self) -> None:
        if self.chain:
            self.chain.write()
            self.chain.save_controllers()
