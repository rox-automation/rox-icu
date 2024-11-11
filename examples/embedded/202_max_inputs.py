"""
Read inputs

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import time
from icu_board import maxio, max1, max2, max_enable, D_PINS

maxio.DEBUG = False  # print debug info
max_enable.value = True  # enable in- and outputs

for pin in D_PINS:
    pin.switch_to_input()
    print(pin)


for drv in [max1, max2]:
    print("chip address:", drv.chip_address)

    drv.print_registers()

    # check pin configuration
    set_out = drv.read_register(maxio.REGISTERS.SET_OUT)
    print(f"SET_OUT: {set_out[1]:08b}")

# read inputs

while True:
    d_values = [int(pin.value) for pin in D_PINS]
    print(f"d values: {d_values}")
    time.sleep(0.5)
