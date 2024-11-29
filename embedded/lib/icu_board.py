"""pin definitions


Feather M4 CAN pins  and ECU mapping (for reference)
Symbols:
 - "=" means same as on Feather
 - "x" means not connected
 - "!" means rempapped
-----------------------------------

= board.A0 board.D14 (PA02)  <- VCC10V measure 10V reference
! board.A1 board.D15 (PA05)  -> MAX_CRCEN
! board.A2 board.D16 (PB08)  <- MAX1_NFAULT
! board.A3 board.D17 (PB09)  <- MAX2_NFAULT
! board.A4 board.D18 (PA04)  -> MAX_ENABLE
! board.A5 board.D19 (PA06)  <- MAX1_NVDDOK
! board.BATTERY board.VOLTAGE_MONITOR (PB00) <- A0
= board.BOOST_ENABLE (PB13)
= board.CAN_RX (PB15)
= board.CAN_STANDBY (PB12)
= board.CAN_TX (PB14)
! board.D0 board.RX (PB17)  -> MAX_SYNCH
! board.D1 board.TX (PB16)  <- MAX_NREADY
! board.D10 (PA20)          <-> MAX2_D2
! board.D11 (PA21)          <-> MAX2_D3
! board.D12 (PA22)          <-> MAX2_D4
= board.D13 board.LED (PA23)
= board.D23 board.MISO (PB22)
= board.D24 board.MOSI (PB23)
= board.D25 board.SCK (PA17)
! board.D4 (PA14)           -> MAX_CS
! board.D5 (PA16)            <-> MAX1_D3
! board.D6 (PA18)           <-> MAX1_D4
! board.D9 (PA19)          <-> MAX2_D1
= board.NEOPIXEL (PB02)
x board.NEOPIXEL_POWER (PB03)
! board.SCL (PA13)          <-> MAX1_D2
! board.SDA (PA12)         <-> MAX1_D1

"""

from microcontroller import pin  # type: ignore
from digitalio import DigitalInOut, Direction

import neopixel
import canio
import busio
import max14906 as maxio


class Pins:
    """pin definitions"""

    NEOPIXEL = pin.PB02

    # status leds
    LED1 = pin.PA23
    LED2 = pin.PA27
    LED = pin.PA23  # consistent with Feather M4

    VCC10V = pin.PA02
    A0 = pin.PB00
    A1 = pin.PB01

    # enable 5V
    BOOST_ENABLE = pin.PB13

    # can
    CAN_STANDBY = pin.PB12
    CAN_TX = pin.PB14
    CAN_RX = pin.PB15

    # spi
    SCK = pin.PA17
    MOSI = pin.PB23
    MISO = pin.PB22

    # max 14906 pins
    MAX_CRCEN = pin.PA05
    MAX_SYNCH = pin.PB17
    MAX_NREADY = pin.PB16
    MAX_CS = pin.PA14
    MAX_ENABLE = pin.PA04
    MAX1_NFAULT = pin.PB08
    MAX2_NFAULT = pin.PB09
    MAX1_NVDDOK = pin.PA06
    MAX2_NVDDOK = pin.PA07

    # max d_pins
    MAX1_D1 = pin.PA12
    MAX1_D2 = pin.PA13
    MAX1_D3 = pin.PA16
    MAX1_D4 = pin.PA18
    MAX2_D1 = pin.PA19
    MAX2_D2 = pin.PA20
    MAX2_D3 = pin.PA21
    MAX2_D4 = pin.PA22


# ----- object instances -----

# leds
led1 = DigitalInOut(Pins.LED1)
led1.switch_to_output()

led2 = DigitalInOut(Pins.LED2)
led2.switch_to_output()

rgb_led = neopixel.NeoPixel(Pins.NEOPIXEL, 1)
# set dim green on module import
rgb_led.brightness = 0.01
rgb_led.fill((0, 255, 0))

# 5V supply, enable by default
boost_enable = DigitalInOut(Pins.BOOST_ENABLE)
boost_enable.switch_to_output()
boost_enable.value = True

# can interface
_can_standby = DigitalInOut(Pins.CAN_STANDBY)
_can_standby.switch_to_output(False)

can = canio.CAN(rx=Pins.CAN_RX, tx=Pins.CAN_TX, baudrate=500_000, auto_restart=True)


# spi interface
spi = busio.SPI(Pins.SCK, Pins.MOSI, Pins.MISO)

# lock the spi bus
_spi_lock = False
for retry in range(10):
    _spi_lock = spi.try_lock()
    if _spi_lock:
        print(f"spi locked on attempt {retry}")
        break

if not _spi_lock:
    raise RuntimeError("SPI lock failed")

del _spi_lock

spi.configure(baudrate=500_000, phase=0, polarity=0)


# max14906 pins
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


# max chips
_dpins = [
    DigitalInOut(pin)
    for pin in [Pins.MAX1_D1, Pins.MAX1_D2, Pins.MAX1_D3, Pins.MAX1_D4]
]
max1 = maxio.Max14906(spi, max_cs, _dpins, chip_address=0)
del _dpins

_dpins = [
    DigitalInOut(pin)
    for pin in [Pins.MAX2_D1, Pins.MAX2_D2, Pins.MAX2_D3, Pins.MAX2_D4]
]
max2 = maxio.Max14906(spi, max_cs, _dpins, chip_address=1)
del _dpins

# -------------convenience class for D pins----------------


class D_Pin:
    """wrapper around DigitalInOut and corresponding maxio pin"""

    def __init__(self, max_chip: maxio.Max14906, pin_nr: int):
        self.chip = max_chip
        self.pin_nr = pin_nr

    def switch_to_output(self, value: bool) -> None:
        self.chip.switch_to_output(self.pin_nr, value)

    def switch_to_input(self) -> None:
        self.chip.switch_to_input(self.pin_nr)

    def set_output_mode(self, mode: int) -> None:
        """
        Set the output mode

        Args:
            mode (int): Mode value (0–3).
                00: High-side
                01: High-side with 2x inrush current for tINRUSH time
                10: Active-clamp push-pull
                11: Simple push-pull
        """
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
        return f"D_Pin({self.chip.chip_address}, {self.pin_nr},{dir_sign})"


D_PINS = [D_Pin(max_chip, pin_nr) for max_chip in [max2, max1] for pin_nr in range(4)]
