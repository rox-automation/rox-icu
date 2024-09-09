#!/usr/bin/env python3
"""
Read analog and display bar on the outputs.

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import asyncio
import analogio
import math

from icu_board import rgb_led, led1, led2, D_PINS, max_enable, Pins

max_enable.value = True  # enable the MAX14906 chips


def pct_to_bar(pct: float) -> list:
    """convert percentage to a list of 8 elements for the bar display"""

    value = max(0, min(100, pct))

    # Calculate how many elements should be True
    true_count = round((value / 100) * 8)

    # Create the array
    return [1] * true_count + [0] * (8 - true_count)


async def flash_led(led, interval=0.5):
    """flash the LED at the given interval"""

    while True:
        led.value = not led.value
        await asyncio.sleep(interval)


async def glow_neopixel(period=5.0):
    """
    Make the Neopixel glow with a single color, varying brightness linearly

    :param period: Time in seconds for one complete brightness cycle (up and down)
    """
    print(f"Glowing the Neopixel with green color, {period}-second period")

    # Define the color (green)
    color = (0, 255, 0)  # Green

    # Set the pixel color
    rgb_led.fill(color)

    # Calculate the step time for smooth transition
    steps = 200  # Number of steps for a full cycle
    step_time = period / steps

    while True:
        for i in range(steps):
            # Use sine wave to smoothly transition between 0 and 1
            brightness = 0.5 * (1 + math.sin(2 * math.pi * i / steps - math.pi / 2))
            rgb_led.brightness = brightness
            await asyncio.sleep(step_time)


async def handle_analog() -> None:
    """read analog inputs and set nepixel colors"""
    print("Staring analog input handler")

    AIN1 = analogio.AnalogIn(Pins.A0)
    VREF = analogio.AnalogIn(Pins.VCC10V)

    c_offset = 500

    counter = 0

    while True:
        adc_val = AIN1.value
        adc_max_val = VREF.value
        pct = max(0, min(100, ((adc_val - c_offset) / (adc_max_val - c_offset)) * 100))

        bar_vals = pct_to_bar(pct)

        # set the D pins
        for idx, val in enumerate(bar_vals):
            D_PINS[idx].value = val

        counter += 1
        if counter % 100 == 0:
            led2.value = not led2.value
            print(f"{adc_val=} {pct=:.1f} {bar_vals=}")
        await asyncio.sleep(0)


async def main():
    """main coro"""
    await asyncio.gather(
        flash_led(led1),  # flash led1 with default frequency
        handle_analog(),  # read analog inputs and set neopixel colors
        glow_neopixel(),  # cycle through the RGB colors
    )


# ----------- run ---------------
asyncio.run(main())
