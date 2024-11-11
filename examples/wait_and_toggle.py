#!/usr/bin/env python3
"""
 example of waiting for an edge on input and toggling an output with a delay

 Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""
import os
import logging

from rox_icu.core import ICU
from rox_icu.utils import run_main_async

NODE_ID = 1
INTERFACE = os.getenv("ICU_INTERFACE", "vcan0")
print(f"Using interface: {INTERFACE}")

log = logging.getLogger("main")


async def handle_input(icu: ICU) -> None:
    log.info("Starting input handler")

    sensor = icu.pins[7]

    while True:
        log.info("Waiting for input change")
        await sensor.on_change.wait()
        log.info(f"Sensor state: {sensor.state}")


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
