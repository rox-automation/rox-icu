"""

single loop test

Not the cleanest way to program, but most efficient.



"""

import time
import gc
from icu_board import maxio, max1, max2, max_enable


# configuration
scope_pin = max2.d_pins[2]

# set scope pin to push-pull
max2.write_register(maxio.REGISTERS.CONFIG_DO, 0x30)

max_enable.value = True  # enable in- and outputs
counter = 0


d_pins = max1.d_pins + max2.d_pins

t_start = time.monotonic_ns()

t_loop_max = 0.0

while True:
    # get state of all pins
    d_values = [int(pin.value) for pin in d_pins]

    scope_pin.value = not scope_pin.value
    counter += 1

    t_now = time.monotonic_ns()
    t_loop = (t_now - t_start) / 1e6  # ms

    t_loop_max = max(t_loop_max, t_loop)

    if counter % 1000 == 0:
        print(f"loop time: {t_loop:.3f} ms, max: {t_loop_max:.3f} ms")
        t_loop_max = 0.0

    t_start = t_now

    gc.collect()  # this takes quite some time
