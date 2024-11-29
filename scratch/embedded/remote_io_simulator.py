#!/usr/bin/env python3
"""
Simulate ICU remote IO device.

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import asyncio
import struct
import time
import gc
import can_protocol as canp
import canio
from icu_board import D_PINS, can, led1, max1, max2, max_enable
from micropython import const
from digitalio import Direction

NODE_ID = const(0x01)
device_errors = 0

# -------------- initialisation ----------------
print("----------Remote IO sumulator-------------")
print(f"Node ID: {NODE_ID}")
print(f"Can protocol version: {canp.VERSION}")

# intialize system
max_enable.value = True  # enable in- and outputs

# TODO: get pin configurations for outputs from settings.toml
# see https://docs.circuitpython.org/en/latest/docs/environment.html
# for pin_nr in [BUTTON, SENSOR]:
#     D_PINS[pin_nr].switch_to_input()

# show state of all d pins
for pin in D_PINS:
    print(pin)


def get_io_state() -> int:
    io_state = 0

    for bit, pin in enumerate(D_PINS):
        io_state |= pin.value << bit
    return io_state


def set_io_state(state: int) -> None:
    """set output pins based on state (byte)"""
    for bit, pin in enumerate(D_PINS):
        if pin.direction == Direction.OUTPUT:
            pin.value = (state >> bit) & 0x01


async def read_inputs() -> None:
    """read inputs and send can message on change"""

    global device_errors

    io_state = get_io_state()
    prev_io_state = io_state

    opcode, byte_def = canp.get_opcode_and_bytedef(canp.IOStateMessage)
    msg_id = canp.generate_message_id(NODE_ID, opcode)
    print(f"IOStateMessage ID: {msg_id:x}")

    # Timing variables
    loop_count = 0
    max_loop_time = 0.0
    total_loop_time = 0.0
    loop_start = time.monotonic_ns()

    while True:
        # get state of all pins
        io_state = get_io_state()

        if io_state != prev_io_state:
            msg = canio.Message(id=msg_id, data=struct.pack(byte_def, io_state))
            can.send(msg)

        prev_io_state = io_state

        # Calculate loop time in milliseconds
        loop_time = (time.monotonic_ns() - loop_start) / 1_000_000  # Convert ns to ms

        # Update statistics
        max_loop_time = max(max_loop_time, loop_time)
        total_loop_time += loop_time
        loop_count += 1

        # Print statistics every 100 loops
        if loop_count % 100 == 0:
            avg_loop_time = total_loop_time / 100
            print(
                f"Loop timing - Avg: {avg_loop_time:.3f}ms, Max: {max_loop_time:.3f}ms"
            )

            # set error if required
            if max_loop_time > 10:
                print("*****************Long looptime********************")
                device_errors = device_errors | 0x01

            # Reset statistics
            max_loop_time = 0.0
            total_loop_time = 0.0

        gc.collect()

        loop_start = time.monotonic_ns()
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
            errors=device_errors,
            counter=counter & 0xFF,
        )
        # print(msg)
        can_msg = canio.Message(id=msg_id, data=struct.pack(byte_def, *msg))
        can.send(can_msg)

        led1.value = not led1.value

        counter += 1

        await asyncio.sleep(0.1)


async def receive_can_message() -> None:
    listener = can.listen(timeout=0)
    while True:
        if listener.in_waiting():
            msg = listener.receive()
            if msg:
                if canp.get_node_id(msg.id) == NODE_ID:
                    if isinstance(msg, canio.RemoteTransmissionRequest):
                        print(f"RTR message {msg.id:x}")
                    else:
                        decoded_msg = canp.decode_message(msg.id, msg.data)
                        print(f"Received message: {decoded_msg}")

                        if isinstance(decoded_msg, canp.IOStateMessage):
                            set_io_state(decoded_msg.io_state)
                            print(f"IO state set to: {decoded_msg.io_state}")

        await asyncio.sleep(0)  # Yield control to other tasks


# -------------------test function --------------------------------


async def toggle_outputs() -> None:
    """testing function to toggle outputs"""
    pin = D_PINS[0]

    while True:
        pin.value = not pin.value
        await asyncio.sleep(0.5)


# ---------------------main---------------------------------------------


async def main() -> None:
    await asyncio.gather(
        read_inputs(),
        heartbeat_loop(),
        toggle_outputs(),
        receive_can_message(),
    )


asyncio.run(main())
