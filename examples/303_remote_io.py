"""
Running ICU as a remote IO device.



"""

import asyncio
import struct
import canio
from icu_board import led1, can, maxio, max1, max2, max_enable
from micropython import const
import can_protocol as canp

NODE_ID = const(0x01)


BUTTION_PIN = const(3)
SENSOR_PIN = const(0)

# -------------- initialisation ----------------
print(f"Can protocol version: {canp.VERSION}")

# intialize system
max_enable.value = True  # enable in- and outputs
d_pins = max1.d_pins + max2.d_pins

max1.switch_to_input(BUTTION_PIN)  # button
max2.switch_to_input(SENSOR_PIN)  # sensor


def get_io_state() -> int:
    io_state = 0
    for bit, pin in ((0, max1.d_pins[3]), (1, max2.d_pins[0])):
        io_state |= pin.value << bit
    return io_state


async def read_inputs() -> None:
    """read inputs and send can message on change"""

    # configuration
    scope_pin = max2.d_pins[2]

    # set scope pin to push-pull
    max2.write_register(maxio.REGISTERS.CONFIG_DO, 0x30)

    io_state = get_io_state()
    prev_io_state = io_state

    msg_id = canp.generate_message_id(NODE_ID, 2)
    print(f"IOStateMessage ID: {msg_id:x}")

    byte_def = canp.BYTE_DEFS[canp.IOStateMessage]

    while True:
        # get state of all pins
        io_state = get_io_state()

        if io_state != prev_io_state:
            msg = canio.Message(id=msg_id, data=struct.pack(byte_def, io_state))
            can.send(msg)

        prev_io_state = io_state

        scope_pin.value = not scope_pin.value

        await asyncio.sleep(0)


async def heartbeat_loop() -> None:
    counter = 0
    byte_def = canp.BYTE_DEFS[canp.HeartbeatMessage]
    msg_id = canp.generate_message_id(NODE_ID, 1)
    print(f"HeartbeatMessage ID: {msg_id:x}")

    while True:
        msg = canp.HeartbeatMessage(
            device_type=1, error_code=0, counter=counter & 0xFF, io_state=get_io_state()
        )
        can_msg = canio.Message(id=msg_id, data=struct.pack(byte_def, *msg))
        can.send(can_msg)

        led1.value = not led1.value

        counter += 1

        await asyncio.sleep(0.1)


async def main() -> None:
    await asyncio.gather(read_inputs(), heartbeat_loop())


asyncio.run(main())
