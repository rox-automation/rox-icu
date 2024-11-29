#!/usr/bin/env python3
"""ECU board demo with button, sensor, LED, relay and CAN control"""
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

VERSION = "0.3"
BUTTON_POLL_INTERVAL = 0.01
LED_FLASH_INTERVAL = 0.2
RELAY_HOLD_TIME = 1.0


def init_system():
    maxio.DEBUG = False
    max_enable.value = True
    rgb_led.brightness = 0.1
    rgb_led.fill((0, 0, 255))

    for drv in [max1, max2]:
        print(f"chip address: {drv.chip_address}")
        drv.print_registers()

    print(f"Board demo v {VERSION}")


def init_pins():
    sensor = D_PINS[0]
    sensor.switch_to_input()
    button = D_PINS[7]
    button.switch_to_input()
    return sensor, button


async def flash_leds() -> None:
    while True:
        led1.value = not led1.value
        await asyncio.sleep(LED_FLASH_INTERVAL)


async def read_button(button, button_pressed: asyncio.Event, stats: dict) -> None:
    prev_val = False
    while True:
        val = button.value
        if val and val != prev_val:
            stats["button_presses"] += 1
            print(f"Button pressed {stats['button_presses']} times")
            button_pressed.set()
        prev_val = val
        await asyncio.sleep(BUTTON_POLL_INTERVAL)


async def read_sensor(sensor, output_pin, stats: dict) -> None:
    prev_val = False
    while True:
        val = sensor.value
        output_pin.value = val
        if val and val != prev_val:
            stats["sensor_triggers"] += 1
            print(f"Inductive sensor triggered {stats['sensor_triggers']} times")
        prev_val = val
        await asyncio.sleep(0)


async def handle_analog() -> None:
    ain1 = analogio.AnalogIn(Pins.A0)
    ain2 = analogio.AnalogIn(Pins.A1)
    offset = 700
    range_val = 47915 - offset
    counter = 0

    while True:
        rgb = [
            int(max(0, min(100, ((ain.value - offset) / range_val) * 100)) * 2.55)
            for ain in [ain1, ain2]
        ]
        rgb_led.fill((rgb[0], 0, rgb[1]))

        counter += 1
        if counter % 10 == 0:
            led2.value = not led2.value
        await asyncio.sleep(0)


async def handle_outputs(output_pin, relay_pin, button_pressed: asyncio.Event) -> None:
    output_pin.value = False
    while True:
        await button_pressed.wait()
        print("Button pressed, toggling outputs")
        button_pressed.clear()

        for _ in range(10):
            output_pin.value = not output_pin.value
            await asyncio.sleep(0.1)
        output_pin.value = False

        relay_pin.value = True
        await asyncio.sleep(RELAY_HOLD_TIME)
        relay_pin.value = False


async def send_can_messages(scope_pin, stats: dict) -> None:
    counter = 0
    while True:
        message = canio.Message(
            id=0x01,
            data=struct.pack(
                "<BBB",
                counter & 0xFF,
                stats["button_presses"] & 0xFF,
                stats["sensor_triggers"] & 0xFF,
            ),
        )
        can.send(message)
        counter += 1
        scope_pin.value = not scope_pin.value
        gc.collect()
        await asyncio.sleep(0)


async def main() -> None:
    init_system()
    sensor, button = init_pins()

    button_pressed = asyncio.Event()
    stats = {"button_presses": 0, "sensor_triggers": 0}

    await asyncio.gather(
        flash_leds(),
        read_button(button, button_pressed, stats),
        handle_analog(),
        handle_outputs(D_PINS[5], D_PINS[6], button_pressed),
        read_sensor(sensor, D_PINS[4], stats),
        send_can_messages(max2.d_pins[2], stats),
    )


if __name__ == "__main__":
    asyncio.run(main())
