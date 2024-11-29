# ECU board demo
import asyncio
import gc
import struct

import analogio  # pylint: disable=import-error
import canio  # pylint: disable=import-error
from icu_board import (
    D_PINS,
    Pins,
    can,
    led1,
    led2,
    max1,
    max2,
    max_enable,
    maxio,
    rgb_led,
)

VERSION = "0.2"

maxio.DEBUG = False  # print debug info

# --------define pins and peripherals--------
sensor = D_PINS[0]
sensor.switch_to_input()

button = D_PINS[7]
button.switch_to_input()

relay = D_PINS[6]

rgb_led.brightness = 0.1
rgb_led.fill((0, 0, 255))

# --------initialize system--------

button_pressed = asyncio.Event()

nr_button_presses = 0
nr_sensor_triggers = 0


# read all max registers
for drv in [max1, max2]:
    print("chip address:", drv.chip_address)
    drv.print_registers()

print(48 * "-")

print(f"Board demo v {VERSION} ")

# turn max on
max_enable.value = True  # enable in- and outputs


async def flash_leds() -> None:
    while True:
        led1.value = not led1.value
        await asyncio.sleep(0.2)


async def read_button() -> None:
    prev_val = False

    global nr_button_presses

    while True:
        val = button.value
        if val != prev_val and val:
            nr_button_presses += 1
            print(f"Button pressed {nr_button_presses} times")
            button_pressed.set()
        prev_val = val
        await asyncio.sleep(0.01)


async def read_inductive_sensor() -> None:
    global nr_sensor_triggers

    prev_val = False

    output = D_PINS[4]

    while True:
        val = sensor.value
        output.value = val
        if val != prev_val and val:
            nr_sensor_triggers += 1
            print(f"Inductive sensor triggered {nr_sensor_triggers} times")
        prev_val = val
        await asyncio.sleep(0)


async def handle_analog() -> None:
    """read analog inputs and set nepixel colors"""

    AIN1 = analogio.AnalogIn(Pins.A0)
    AIN2 = analogio.AnalogIn(Pins.A1)

    c_offset = 700
    c_range = 47915 - c_offset

    rgb = [0, 0, 0]

    counter = 0

    while True:
        for idx, a in enumerate([AIN1, AIN2]):
            adc_val = a.value
            pct = max(0, min(100, ((adc_val - c_offset) / c_range) * 100))

            rgb[idx] = int(pct * 2.55)

        rgb_led.fill((rgb[0], 0, rgb[1]))
        counter += 1
        if counter % 10 == 0:
            led2.value = not led2.value
        await asyncio.sleep(0)


async def handle_outputs() -> None:
    """perform output actions"""

    output = D_PINS[5]
    output.value = False

    while True:
        await button_pressed.wait()
        print("Button pressed, toggling outputs")
        button_pressed.clear()

        # flash output
        for _ in range(10):
            output.value = not output.value
            await asyncio.sleep(0.1)

        output.value = False

        relay.value = True
        await asyncio.sleep(1.0)
        relay.value = False


async def send_can_messages() -> None:
    """send counter and number of button presses and sensor triggers over CAN"""
    counter = 0
    scope_pin = max2.d_pins[2]

    while True:
        message = canio.Message(
            id=0x01,
            data=struct.pack(
                "<BBB",
                counter & 0xFF,
                nr_button_presses & 0xFF,
                nr_sensor_triggers & 0xFF,
            ),
        )
        can.send(message)
        counter += 1
        scope_pin.value = not scope_pin.value
        gc.collect()
        await asyncio.sleep(0)


async def main() -> None:
    await asyncio.gather(
        flash_leds(),
        read_button(),
        handle_analog(),
        handle_outputs(),
        read_inductive_sensor(),
        send_can_messages(),
    )


# ---------main code----------

asyncio.run(main())
