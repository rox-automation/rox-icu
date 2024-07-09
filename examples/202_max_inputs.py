"""
Read inputs

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import time
import max14906 as mx

mx.DEBUG = True  # print debug info
mx.ENABLE.value = True  # enable in- and outputs

drv = mx.Max14906(chip_address=0)
error = drv.get_global_error()
print("global error:", error)

# set all D pins to input
for idx in range(4):
    drv.switch_to_input(idx)

drv.print_registers()

# read inputs
while True:
    d_values = [int(pin.value) for pin in drv.d_pins]
    print(f"d values: {d_values}")
    time.sleep(0.5)
