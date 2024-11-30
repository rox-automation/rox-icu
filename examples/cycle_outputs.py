#!/usr/bin/env python3
"""
 cycle all outputs on the ICU board

 Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import asyncio

from rox_icu.core import ICU
from rox_icu.utils import run_main_async


async def main() -> None:
    icu = ICU(10)
    await icu.start()

    while True:
        for idx in range(8):
            icu.io_state = 1 << idx
            await asyncio.sleep(0.1)


if __name__ == "__main__":
    run_main_async(main())
