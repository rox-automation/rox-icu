#!/usr/bin/env python3
"""
 test output pins

 Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""
import asyncio
import os

from rox_icu.core import ICU
from rox_icu.utils import run_main_async

NODE_ID = 1
INTERFACE = os.getenv("ICU_INTERFACE", "vcan0")
print(f"Using interface: {INTERFACE}")


async def main() -> None:

    icu = ICU(NODE_ID, INTERFACE)
    await icu.start()

    for i in range(32):

        icu.io_state = i
        await asyncio.sleep(0.1)

    icu.io_state = 0

    await icu.stop()
    print("Done")


if __name__ == "__main__":
    run_main_async(main())
