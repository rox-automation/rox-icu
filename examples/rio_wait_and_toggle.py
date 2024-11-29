#!/usr/bin/env python3
"""
 example of waiting for an edge on input and toggling an output with a delay

 Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""
import asyncio
import logging

from rox_icu.core import ICU
from rox_icu.utils import run_main_async

NODE_ID = 10

SENSOR_PIN = 0
RELAY_PIN = 6

log = logging.getLogger("main")

icu = ICU(NODE_ID)

sensor = icu.pins[SENSOR_PIN]
relay = icu.pins[RELAY_PIN]


async def actuate_relay(delay: float = 3.0) -> None:
    log.info("Actuating relay")
    await asyncio.sleep(delay)
    relay.state = True
    await asyncio.sleep(0.1)
    relay.state = False


async def handle_input() -> None:
    log.info("Starting input handler")

    while True:
        log.info("Waiting for sensor")
        await sensor.high_event.wait()
        log.info(f"Sensor state: {sensor.state}")

        asyncio.create_task(actuate_relay())


async def main() -> None:
    await icu.start()

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(handle_input())

    finally:
        await icu.stop()
        print("Done")


if __name__ == "__main__":
    run_main_async(main())
