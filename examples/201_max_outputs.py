"""
Toggle outputs

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import time
import max14906 as mx

mx.DEBUG = True  # print debug info
mx.ENABLE.value = True  # enable in- and outputs

drv = mx.Max14906(chip_address=0)
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
mx.ENABLE.value = False
