#!/usr/bin/env python3
"""
Monitor multiple ICU devices using the ICU CAN driver.

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import asyncio


from rox_icu.core import ICU
from rox_icu.utils import run_main


INTERFACE = "slcan0"


def state_change_callback(device: ICU) -> None:
    print(f"Node {device.node_id} IO state: {device.io_state:08b}")


async def main():
    # create icus
    devices = [
        ICU(node_id, INTERFACE, state_change_callback=state_change_callback)
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
