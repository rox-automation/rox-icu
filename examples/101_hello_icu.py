#!/usr/bin/env python3
"""
Demonstrate basic functionality of the ICU board:

   - flash the onboard LEDs
   - cycle through the RGB LED colors on Neopixel

Note: we are using asyncio here to demonstrate loop-based programming

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import asyncio

from icu_board import rgb_led, led1, led2


async def flash_led(led, interval=0.5):
    """flash the LED at the given interval"""

    while True:
        led.value = not led.value
        await asyncio.sleep(interval)


async def cycle_neopixel():
    """cycle through the RGB colors on the Neopixel"""
    print("cycling through the RGB colors on the Neopixel")

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

    rgb_led.brightness = 0.3

    while True:
        for color in colors:
            rgb_led.fill(color)
            await asyncio.sleep(0.3)


async def main():
    """main coro"""
    await asyncio.gather(
        flash_led(led1),  # flash led1 with default frequency
        flash_led(led2, 0.4),  # flash led2 faster
        cycle_neopixel(),  # cycle through the RGB colors
    )


# ----------- run ---------------
asyncio.run(main())
