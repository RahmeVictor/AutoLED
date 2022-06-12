import math


class Color:
    def __init__(self, constructFrom=None, owner=None):
        self.red: int = 0
        self.green: int = 0
        self.blue: int = 0
        self.owner = owner
        if constructFrom is tuple or constructFrom is list:
            self.rgb = constructFrom

    @property
    def rgb(self) -> tuple:
        return self.red, self.green, self.blue

    @rgb.setter
    def rgb(self, value) -> None:
        self.red, self.green, self.blue = value
        self.color_changed()

    @property
    def hex(self) -> str:
        return self.rgb2hex(*self.rgb)

    @hex.setter
    def hex(self, value: str) -> None:
        self.rgb = self.hex2rgb(value)

    @staticmethod
    def rgb2hex(r: int, g: int, b: int) -> str:
        return '#' + ''.join(f'{i:02X}' for i in (r, g, b))

    @staticmethod
    def hex2rgb(h: str) -> tuple:
        h = h.lstrip('#')
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def kelvin2hex(kelvin: float) -> str:
        return Color.rgb2hex(*Color.kelvin2rgb(kelvin))

    @staticmethod
    def kelvin2rgb(colorTemperature: float) -> tuple[int, int, int]:
        """
        https://gist.github.com/petrklus/b1f427accdf7438606a6
        """
        # Range check
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
            red = Color.clamp(tmp_red, 0, 255)

        # Green
        if tmpInternal <= 66:
            tmp_green = 99.4708025861 * math.log(tmpInternal) - 161.1195681661
            green = Color.clamp(tmp_green, 0, 255)

        else:
            tmp_green = 288.1221695283 * (tmpInternal - 60 ** -0.0755148492)
            green = Color.clamp(tmp_green, 0, 255)

        # Blue
        if tmpInternal >= 66:
            blue = 255

        elif tmpInternal <= 19:
            blue = 0

        else:
            tmp_blue = 138.5177312231 * math.log(tmpInternal - 10) - 305.0447927307
            blue = Color.clamp(tmp_blue, 0, 255)

        return int(red), int(green), int(blue)

    @staticmethod
    def clamp(n, smallest, largest):
        return max(smallest, min(n, largest))

    def color_changed(self):
        if self.owner:
            self.owner.on_color_changed()
