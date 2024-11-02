#!/usr/bin/env python3
"""
Monitor multiple ICU devices using the ICU CAN driver.

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import asyncio
import os

from rox_icu.core import ICU
from rox_icu.utils import run_main


INTERFACE = os.getenv("ICU_INTERFACE", "vcan0")
print(f"Using interface: {INTERFACE}")


def state_change_callback(device: ICU) -> None:
    print(f"Node {device.node_id} IO state: {device.io_state:#04x}")


async def main():
    # create icus
    devices = [
        ICU(node_id, INTERFACE, on_dio_change=state_change_callback)
        for node_id in range(1, 3)
    ]

    # start the icus
    for device in devices:
        await device.start()

    # monitor the icus
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    run_main(main())