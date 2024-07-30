"""

single loop test

Not the cleanest way to program, but most efficient.
Garbage collection however is dominant factor here, so async programming
should not be much slower than this.



"""

import time
import struct
import gc
import canio
from icu_board import can, maxio, max1, max2, max_enable
from micropython import const
import can_protocol as canp

NODE_ID = const(1)
MSG_ID = canp.generate_message_id(NODE_ID, canp.get_opcode(canp.HeartbeatMessage))

print(f"msg_id: {MSG_ID:x}")

# configuration
scope_pin = max2.d_pins[2]

# set scope pin to push-pull
max2.write_register(maxio.REGISTERS.CONFIG_DO, 0x30)

max_enable.value = True  # enable in- and outputs
counter = 0


d_pins = max1.d_pins + max2.d_pins

# set all D pins to input
for idx in range(4):
    max1.switch_to_input(idx)
    max2.switch_to_input(idx)

# set scope to output
max2.switch_to_output(2, False)

t_start = time.monotonic_ns()

t_loop_max = 0.0


hb_msg, hb_byte_def = canp.MESSAGES[0]

while True:
    # get state of all pins
    io_state = 0
    for bit, pin in enumerate(d_pins):
        io_state |= pin.value << bit

    # clear scope bit
    # io_state &= ~(1 << 6)

    # send heartbeat message
    msg = hb_msg(device_type=1, error_code=0, counter=counter & 0xFF, io_state=io_state)
    can_msg = canio.Message(id=MSG_ID, data=struct.pack(hb_byte_def, *msg))
    can.send(can_msg)

    # toggle scope pin
    scope_pin.value = not scope_pin.value

    # timing
    counter += 1

    t_now = time.monotonic_ns()
    t_loop = (t_now - t_start) / 1e6  # ms

    t_loop_max = max(t_loop_max, t_loop)

    if counter > 1000:
        print(f"loop time: {t_loop:.3f} ms, max: {t_loop_max:.3f} ms")
        t_loop_max = 0.0
        counter = 0

    t_start = t_now

    gc.collect()  # this takes quite some time
