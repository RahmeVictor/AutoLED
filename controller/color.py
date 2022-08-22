import math


class Color:
    """
    Base Class that contains color data as HSV with helper functions. Preferred color method is HSV.

    When color values (rgb, hex, hsv) are changed it calls the 'on_color_changed' function in its owner. This function
    is not called if the h,s,v values are modified individually.

    RGB (int, int, int) is from 0 to 255 int

    HSV (int, int, int) is from 0 to 360 for H and 0 to 100 for S and V

    HEX (str) is #ffaa00
    """

    def __init__(self, constructFrom=None, owner=None):
        self.h: int = 0  # Hue
        self.s: int = 0  # Saturation
        self.v: int = 0  # Vue
        self.owner = owner
        if constructFrom is tuple or constructFrom is list:
            self.rgb = constructFrom

    @property
    def rgb(self) -> tuple[int, ...]:
        return self.hsv2rgb(*self.hsv)

    @rgb.setter
    def rgb(self, value) -> None:
        self.hsv = self.rgb2hsv(*value)

    @property
    def hex(self) -> str:
        return self.rgb2hex(*self.rgb)

    @hex.setter
    def hex(self, value: str) -> None:
        self.rgb = self.hex2rgb(value)

    @property
    def hsv(self) -> tuple[int, int, int]:
        return self.h, self.s, self.v

    @hsv.setter
    def hsv(self, value) -> None:
        self.h, self.s, self.v = (round(i) for i in value)
        self.color_changed()

    @property
    def temperature(self) -> int:
        return self.rgb2kelvin()

    @temperature.setter
    def temperature(self, value: int) -> None:
        # Don't update the v (vue)
        tempHSV = self.rgb2hsv(*self.kelvin2rgb(value))
        self.hsv = (tempHSV[0], tempHSV[1], self.v)

    @staticmethod
    def rgb2hex(r: int, g: int, b: int) -> str:
        return '#' + ''.join(f'{i:02X}' for i in (r, g, b))

    @staticmethod
    def hex2rgb(h: str) -> tuple:
        h = h.lstrip('#')
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def rgb2kelvin() -> int:
        # TODO
        return 0

    @staticmethod
    def kelvin2rgb(colorTemperature: float) -> tuple[int, int, int]:
        # Taken from https://gist.github.com/petrklus/b1f427accdf7438606a6

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
    def rgb2hsv(r, g, b) -> tuple[int, int, int]:
        r, g, b = tuple(i / 255.0 for i in (r, g, b))
        cmax = max(r, g, b)  # maximum of r, g, b
        cmin = min(r, g, b)  # minimum of r, g, b
        diff = cmax - cmin
        if cmax == cmin:
            h = 0

        elif cmax == r:
            h = (60 * ((g - b) / diff) + 360) % 360

        elif cmax == g:
            h = (60 * ((b - r) / diff) + 120) % 360

        else:
            h = (60 * ((r - g) / diff) + 240) % 360

        if cmax == 0:
            s = 0

        else:
            s = (diff / cmax) * 100

        v = cmax * 100
        return int(h), int(s), int(v)

    @staticmethod
    def hsv2rgb(h: int, s: int, v: int) -> tuple[int, ...]:
        s /= 100.0
        v /= 100.0
        c = s * v
        x = c * (1 - abs(math.fmod(h / 60.0, 2) - 1))
        m = v - c
        if 0 <= h < 60:
            r, g, b = c, x, 0

        elif 60 <= h < 120:
            r, g, b = x, c, 0

        elif 120 <= h < 180:
            r, g, b = 0, c, x

        elif 180 <= h < 240:
            r, g, b = 0, x, c

        elif 240 <= h < 300:
            r, g, b = x, 0, c

        else:
            r, g, b = c, 0, x

        return tuple(round((i + m) * 255.0) for i in (r, g, b))

    @staticmethod
    def clamp(n, smallest, largest):
        return max(smallest, min(n, largest))

    def get_hsv_for_js(self) -> str:
        # Returns a string to be used in a flask template as a dict: <{h:..., s:..., v:...}>
        return '{h:' + str(self.h) + ', s:' + str(self.s) + ', v:' + str(self.v) + '}'

    def color_changed(self) -> None:
        if self.owner:
            self.owner.on_color_changed()
