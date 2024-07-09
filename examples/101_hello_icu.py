#!/usr/bin/env python3
"""
Demonstrate basic functionality of the ICU board:

   - flash the onboard LEDs
   - cycle through the RGB LED colors on Neopixel

Note: we are using asyncio here to demonstrate loop-based programming

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import asyncio
import ecu_board as board
from digitalio import DigitalInOut
import neopixel


async def flash_led(pin, interval=0.5):
    """flash the LED at the given interval"""
    print(f"flashing LED at {pin} with interval {interval}")
    led = DigitalInOut(pin)
    led.switch_to_output()

    while True:
        led.value = not led.value
        await asyncio.sleep(interval)


async def cycle_neopixel():
    """cycle through the RGB colors on the Neopixel"""
    print("cycling through the RGB colors on the Neopixel")

    board.switch_5V(True)

    colors = [
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (255, 255, 0),
        (255, 0, 255),
        (0, 255, 255),
        (255, 255, 255),
        (0, 0, 0),
    ]

    px = neopixel.NeoPixel(board.NEOPIXEL, 1)
    px.brightness = 0.3

    while True:
        for color in colors:
            px.fill(color)
            await asyncio.sleep(0.5)


async def main():
    """main coro"""
    await asyncio.gather(
        flash_led(board.LED1),  # flash led1 with default frequency
        flash_led(board.LED2, 0.1),  # flash led2 faster
        cycle_neopixel(),  # cycle through the RGB colors
    )


# ----------- run ---------------
asyncio.run(main())
