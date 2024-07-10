# ECU board demo
import asyncio
import analogio
from digitalio import DigitalInOut, Direction
import ecu_board as board
import max14906 as mx
import neopixel

button_pressed = asyncio.Event()

npx = neopixel.NeoPixel(board.NEOPIXEL, 1)


def init_system() -> None:
    mx.ENABLE.value = False
    mx.DEBUG = True

    npx.brightness = 0.1
    npx.fill((0, 0, 255))

    # set in- and outputs
    mx.write_register(mx.REGISTERS.SET_OUT, 0x80, 0)
    mx.write_register(mx.REGISTERS.SET_OUT, 0x00, 1)

    # read all max registers
    for chip_address in [0, 1]:
        print(f"-------reading register chip {chip_address}")
        for reg in mx.REGISTERS.get_registers():
            mx.read_register(reg[1], chip_address)

    print(48 * "-")

    # turn max on
    mx.ENABLE.value = True

    # set button to input
    mx.input_to_d_pins["D8"].direction = Direction.INPUT


async def flash_leds() -> None:
    led = DigitalInOut(board.LED1)
    led.direction = Direction.OUTPUT

    while True:
        led.value = not led.value
        await asyncio.sleep(0.2)


async def read_button() -> None:
    prev_val = False
    counter = 0

    while True:
        val = mx.input_to_d_pins["D8"].value
        if val != prev_val and val:
            counter += 1
            print(f"Button pressed {counter} times")
            button_pressed.set()
        prev_val = val
        await asyncio.sleep(0.01)


async def handle_analog() -> None:
    """read analog inputs and set nepixel colors"""

    AIN1 = analogio.AnalogIn(board.A0)
    AIN2 = analogio.AnalogIn(board.A1)

    led = DigitalInOut(board.LED2)
    led.direction = Direction.OUTPUT

    c_offset = 700
    c_range = 47915 - c_offset

    rgb = [0, 0, 0]

    counter = 0

    while True:
        for idx, a in enumerate([AIN1, AIN2]):
            adc_val = a.value
            pct = max(0, min(100, ((adc_val - c_offset) / c_range) * 100))

            rgb[idx] = int(pct * 2.55)

        npx.fill((rgb[0], 0, rgb[1]))
        counter += 1
        if counter % 10 == 0:
            led.value = not led.value
        await asyncio.sleep(0)


async def handle_outputs() -> None:
    """perform output actions"""

    outputs = [mx.input_to_d_pins[name] for name in ["D5", "D6"]]
    for p in outputs:
        p.value = False

    for chip_address in range(2):
        mx.read_register(mx.REGISTERS.GLOBAL_ERR, chip_address)

    relay = mx.input_to_d_pins["D7"]

    while True:
        await button_pressed.wait()
        print("Button pressed, toggling outputs")
        button_pressed.clear()

        # flash outputs
        for _ in range(10):
            for p in outputs:
                p.value = True
                await asyncio.sleep(0.02)
                p.value = False
                await asyncio.sleep(0.02)

        relay.value = True
        await asyncio.sleep(1.0)
        relay.value = False


async def main() -> None:
    await asyncio.gather(flash_leds(), read_button(), handle_analog(), handle_outputs())


# ---------main code----------


init_system()
asyncio.run(main())
