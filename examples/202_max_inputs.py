"""
Read inputs

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import time
from icu_board import maxio, max1, max2, max_enable

maxio.DEBUG = False  # print debug info
max_enable.value = True  # enable in- and outputs


for drv in [max1, max2]:
    print("chip address:", drv.chip_address)

    drv.print_registers()

    # set all D pins to input
    for idx in range(4):
        drv.switch_to_input(idx)

    # check pin configuration
    set_out = drv.read_register(maxio.REGISTERS.SET_OUT)
    print(f"SET_OUT: {set_out[1]:08b}")

# read inputs
input_pins = max1.d_pins + max2.d_pins

while True:
    d_values = [int(pin.value) for pin in input_pins]
    print(f"d values: {d_values}")
    time.sleep(0.5)
