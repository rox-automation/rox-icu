"""
Toggle outputs

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import time
from icu_board import maxio, max1, max2, max_enable, D_PINS


maxio.DEBUG = True  # print debug info
max_enable.value = True  # enable in- and outputs

for drv in [max1, max2]:
    print("chip address:", drv.chip_address)
    error = drv.get_global_error()
    print("global error:", error)

    drv.print_registers()

    # toggle outputs with D pins

try:
    while True:
        for pin in D_PINS:
            print("toggling", pin)
            pin.value = True
            time.sleep(0.5)
            pin.value = False
finally:
    # disable all outputs
    max_enable.value = False
