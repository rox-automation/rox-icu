"""Mock implementation of icu_board.py for CPython testing

This module provides mock classes and functionality to simulate the CircuitPython
hardware interfaces used in the original icu_board.py.
"""

from enum import Enum
from typing import List

from . import canio


# Mock base classes to simulate CircuitPython hardware interfaces
class Pin:
    """Mock microcontroller pin"""

    def __init__(self, pin_id: str):
        self.pin_id = pin_id
        self.value = False

    def __repr__(self):
        return f"Pin({self.pin_id})"


class Direction(Enum):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"


class DigitalInOut:
    """Mock digital I/O pin"""

    def __init__(self, pin: Pin):
        self.pin = pin
        self.direction = Direction.INPUT
        self._value = False

    def switch_to_output(self, value: bool = False) -> None:
        self.direction = Direction.OUTPUT
        self._value = value

    def switch_to_input(self) -> None:
        self.direction = Direction.INPUT

    @property
    def value(self) -> bool:
        return self._value

    @value.setter
    def value(self, val: bool):
        self._value = val


# Mock peripheral interfaces
class NeoPixel:
    """Mock NeoPixel LED"""

    def __init__(self, pin: Pin, num_pixels: int):
        self.pin = pin
        self.num_pixels = num_pixels
        self.pixels = [(0, 0, 0)] * num_pixels
        self.brightness = 1.0

    def fill(self, color):
        for i in range(self.num_pixels):
            self.pixels[i] = color


class SPI:
    """Mock SPI interface"""

    def __init__(self, clock: Pin, mosi: Pin, miso: Pin):
        self.clock = clock
        self.mosi = mosi
        self.miso = miso
        self.locked = False

    def try_lock(self) -> bool:
        if not self.locked:
            self.locked = True
            return True
        return False

    def configure(self, baudrate: int, phase: int, polarity: int):
        pass


class Max14906:
    """Mock MAX14906 IC"""

    def __init__(
        self,
        spi: SPI,
        cs_pin: DigitalInOut,
        d_pins: List[DigitalInOut],
        chip_address: int,
    ):
        self.spi = spi
        self.cs_pin = cs_pin
        self.d_pins = d_pins
        self.chip_address = chip_address
        self._output_modes = [0] * len(d_pins)

    def switch_to_output(self, pin_nr: int, value: bool) -> None:
        self.d_pins[pin_nr].switch_to_output(value)

    def switch_to_input(self, pin_nr: int) -> None:
        self.d_pins[pin_nr].switch_to_input()

    def set_output_mode(self, pin_nr: int, mode: int) -> None:
        if 0 <= mode <= 3:
            self._output_modes[pin_nr] = mode


# Create mock pin instances to match the original board definitions
class Pins:
    """Mock pin definitions matching the original board"""

    NEOPIXEL = Pin("PB02")
    LED1 = Pin("PA23")
    LED2 = Pin("PA27")
    LED = Pin("PA23")
    VCC10V = Pin("PA02")
    A0 = Pin("PB00")
    A1 = Pin("PB01")
    BOOST_ENABLE = Pin("PB13")
    CAN_STANDBY = Pin("PB12")
    CAN_TX = Pin("PB14")
    CAN_RX = Pin("PB15")
    SCK = Pin("PA17")
    MOSI = Pin("PB23")
    MISO = Pin("PB22")
    MAX_CRCEN = Pin("PA05")
    MAX_SYNCH = Pin("PB17")
    MAX_NREADY = Pin("PB16")
    MAX_CS = Pin("PA14")
    MAX_ENABLE = Pin("PA04")
    MAX1_NFAULT = Pin("PB08")
    MAX2_NFAULT = Pin("PB09")
    MAX1_NVDDOK = Pin("PA06")
    MAX2_NVDDOK = Pin("PA07")
    MAX1_D1 = Pin("PA12")
    MAX1_D2 = Pin("PA13")
    MAX1_D3 = Pin("PA16")
    MAX1_D4 = Pin("PA18")
    MAX2_D1 = Pin("PA19")
    MAX2_D2 = Pin("PA20")
    MAX2_D3 = Pin("PA21")
    MAX2_D4 = Pin("PA22")


# Initialize mock hardware interfaces
led1 = DigitalInOut(Pins.LED1)
led1.switch_to_output()

led2 = DigitalInOut(Pins.LED2)
led2.switch_to_output()

rgb_led = NeoPixel(Pins.NEOPIXEL, 1)
rgb_led.brightness = 0.01
rgb_led.fill((0, 255, 0))

boost_enable = DigitalInOut(Pins.BOOST_ENABLE)
boost_enable.switch_to_output()
boost_enable.value = True

_can_standby = DigitalInOut(Pins.CAN_STANDBY)
_can_standby.switch_to_output(False)

can = canio.CAN()

spi = SPI(Pins.SCK, Pins.MOSI, Pins.MISO)
spi.try_lock()
spi.configure(baudrate=500_000, phase=0, polarity=0)

# MAX14906 control pins
max_cs = DigitalInOut(Pins.MAX_CS)
max_cs.switch_to_output(True)

max_synch = DigitalInOut(Pins.MAX_SYNCH)
max_synch.switch_to_output(True)

max_nready = DigitalInOut(Pins.MAX_NREADY)

max_crcen = DigitalInOut(Pins.MAX_CRCEN)
max_crcen.switch_to_output(False)

max_enable = DigitalInOut(Pins.MAX_ENABLE)
max_enable.switch_to_output(False)

max1_nfault = DigitalInOut(Pins.MAX1_NFAULT)
max2_nfault = DigitalInOut(Pins.MAX2_NFAULT)

# Initialize MAX14906 chips
_dpins = [
    DigitalInOut(pin)
    for pin in [Pins.MAX1_D1, Pins.MAX1_D2, Pins.MAX1_D3, Pins.MAX1_D4]
]
max1 = Max14906(spi, max_cs, _dpins, chip_address=0)
del _dpins

_dpins = [
    DigitalInOut(pin)
    for pin in [Pins.MAX2_D1, Pins.MAX2_D2, Pins.MAX2_D3, Pins.MAX2_D4]
]
max2 = Max14906(spi, max_cs, _dpins, chip_address=1)
del _dpins


class D_Pin:
    """Mock wrapper around DigitalInOut and corresponding maxio pin"""

    def __init__(self, max_chip: Max14906, pin_nr: int):
        self.chip = max_chip
        self.pin_nr = pin_nr

    def switch_to_output(self, value: bool) -> None:
        self.chip.switch_to_output(self.pin_nr, value)

    def switch_to_input(self) -> None:
        self.chip.switch_to_input(self.pin_nr)

    def set_output_mode(self, mode: int) -> None:
        self.chip.set_output_mode(self.pin_nr, mode)

    @property
    def value(self) -> bool:
        return self.chip.d_pins[self.pin_nr].value

    @value.setter
    def value(self, value: bool):
        self.chip.d_pins[self.pin_nr].value = value

    @property
    def direction(self) -> Direction:
        return self.chip.d_pins[self.pin_nr].direction

    @direction.setter
    def direction(self, direction: Direction):
        self.chip.d_pins[self.pin_nr].direction = direction

    def __repr__(self):
        dir_sign = "input" if self.direction == Direction.INPUT else "output"
        return f"D_Pin({self.chip.chip_address}, {self.pin_nr}, {dir_sign})"


D_PINS = [D_Pin(max_chip, pin_nr) for max_chip in [max2, max1] for pin_nr in range(4)]
