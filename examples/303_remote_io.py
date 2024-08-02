"""
Running ICU as a remote IO device.



"""

import asyncio
import struct
import canio
from icu_board import led1, can, maxio, max1, max2, max_enable, D_PINS
from micropython import const
import can_protocol as canp

NODE_ID = const(0x01)

BUTTON = const(7)
SENSOR = const(0)

# -------------- initialisation ----------------
print(f"Can protocol version: {canp.VERSION}")

# intialize system
max_enable.value = True  # enable in- and outputs

# configure inputs
for pin_nr in [BUTTON, SENSOR]:
    D_PINS[pin_nr].switch_to_input()

# show state of all d pins
for pin in D_PINS:
    print(pin)


def get_io_state() -> int:
    io_state = 0
    for bit, pin in enumerate(D_PINS):
        io_state |= pin.value << bit
    return io_state


async def read_inputs() -> None:
    """read inputs and send can message on change"""

    # configuration

    # set scope pin to push-pull
    max2.write_register(maxio.REGISTERS.CONFIG_DO, 0x30)

    io_state = get_io_state()
    prev_io_state = io_state

    opcode, byte_def = canp.get_opcode_and_bytedef(canp.IOStateMessage)
    msg_id = canp.generate_message_id(NODE_ID, opcode)
    print(f"IOStateMessage ID: {msg_id:x}")

    while True:
        # get state of all pins
        io_state = get_io_state()

        if io_state != prev_io_state:
            msg = canio.Message(id=msg_id, data=struct.pack(byte_def, io_state))
            can.send(msg)

        prev_io_state = io_state

        await asyncio.sleep(0)


async def heartbeat_loop() -> None:
    counter = 0

    opcode, byte_def = canp.get_opcode_and_bytedef(canp.HeartbeatMessage)

    msg_id = canp.generate_message_id(NODE_ID, opcode)
    print(f"HeartbeatMessage ID: {msg_id:x}")

    while True:
        msg = canp.HeartbeatMessage(
            device_type=1,
            error_max1=max1.get_global_error(),
            error_max2=max2.get_global_error(),
            io_state=get_io_state(),
            device_state=0,
            counter=counter & 0xFF,
        )
        can_msg = canio.Message(id=msg_id, data=struct.pack(byte_def, *msg))
        can.send(can_msg)

        led1.value = not led1.value

        counter += 1

        await asyncio.sleep(0.1)


async def main() -> None:
    await asyncio.gather(read_inputs(), heartbeat_loop())


asyncio.run(main())
