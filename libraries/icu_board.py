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

from microcontroller import pin
from digitalio import DigitalInOut
import neopixel


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

# 5V supply, enable by default
boost_enable = DigitalInOut(Pins.BOOST_ENABLE)
boost_enable.switch_to_output()
boost_enable.value = True

# interface pins
# D_PINS = [
#     MAX1_D1,  # D5
#     MAX1_D2,  # D6
#     MAX1_D3,  # D7
#     MAX1_D4,  # D8
#     MAX2_D1,  # D1
#     MAX2_D2,  # D2
#     MAX2_D3,  # D3
#     MAX2_D4,  # D4
# ]

# input_to_d_pins = {
#     "D5": D_PINS[0],
#     "D6": D_PINS[1],
#     "D7": D_PINS[2],
#     "D8": D_PINS[3],
#     "D1": D_PINS[4],
#     "D2": D_PINS[5],
#     "D3": D_PINS[6],
#     "D4": D_PINS[7],
# }
