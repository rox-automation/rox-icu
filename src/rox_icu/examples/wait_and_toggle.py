#!/usr/bin/env python3
"""
 example of waiting for an edge on input and toggling an output with a delay

 Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""
import asyncio
import os
import logging

from rox_icu.core import ICU
from rox_icu.utils import run_main_async

NODE_ID = 1

SENSOR_PIN = 7
RELAY_PIN = 0

INTERFACE = os.getenv("ICU_INTERFACE", "vcan0")
print(f"Using interface: {INTERFACE}")

log = logging.getLogger("main")


async def handle_input(icu: ICU) -> None:
    log.info("Starting input handler")

    sensor = icu.pins[SENSOR_PIN]
    relay = icu.pins[RELAY_PIN]
    relay.state = False

    while True:
        log.info("Waiting for high state")
        await sensor.high_event.wait()
        log.info(f"Sensor state: {sensor.state}")

        # toggle relay
        relay.state = True
        await asyncio.sleep(0.1)
        relay.state = False


async def main() -> None:

    icu = ICU(NODE_ID, INTERFACE)
    await icu.start()

    try:
        await handle_input(icu)
    finally:
        await icu.stop()
        print("Done")


if __name__ == "__main__":
    run_main_async(main())
