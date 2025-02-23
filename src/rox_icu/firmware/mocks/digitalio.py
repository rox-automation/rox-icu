# mocks/digitalio.py
class Direction:
    INPUT = "input"
    OUTPUT = "output"


class DigitalInOut:
    def __init__(self):
        self._value = False
        self.direction = Direction.OUTPUT

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        self._value = bool(val)
