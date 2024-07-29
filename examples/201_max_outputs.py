"""
Toggle outputs

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import time
from icu_board import mx, max1, max2, max_enable


mx.DEBUG = True  # print debug info
max_enable.value = True  # enable in- and outputs

for drv in [max1, max2]:
    print("chip address:", drv.chip_address)
    error = drv.get_global_error()
    print("global error:", error)

    drv.print_registers()

    # toggle outputs with D pins

    for idx in range(16):
        for pin in drv.d_pins:
            pin.value = False

        drv.d_pins[idx % 4].value = True

        time.sleep(0.1)

# disable all outputs
max_enable.value = False
