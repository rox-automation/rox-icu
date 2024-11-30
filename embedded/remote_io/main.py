#!/usr/bin/env python3
"""
Remote IO firmware for ICU board

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""
import os
import asyncio
import struct
import time
import gc
import can_protocol as canp
import canio  # pylint: disable=import-error
from icu_board import D_PINS, can, led1, led2, max_enable
from digitalio import Direction  # pylint: disable=import-error
from bit_ops import set_bit, clear_bit


VERSION = "1.6.0"
CAN_PROTOCOL_VERSION = 12

gc.enable()
# gc.disable()  # Disable automatic garbage collection


class ErrorBits:
    LONG_LOOP_TIME = 0
    CAN_ERROR = 1


device_errors = 0

print(f"------------------Remote IO firmware-v{VERSION}-----------------")


NODE_ID = int(os.getenv("NODE_ID", 60))  # pylint: disable=W1508
print(f"NODE_ID: {NODE_ID}")


# -------------- initialization ----------------
print(f"Node ID: {NODE_ID}")
print(f"Can protocol version: {canp.VERSION}")

assert (
    canp.VERSION == CAN_PROTOCOL_VERSION
), f"Can protocol version must be  {CAN_PROTOCOL_VERSION}"

# Initialize system
max_enable.value = True  # enable in- and outputs

IO_DIRS = 0  # 0=output, 1=input
inputs_str = os.getenv("INPUTS")
if inputs_str is not None:
    inputs = [int(val) for val in inputs_str.split(",")]
    print(f"Inputs: {inputs}")
    for nr in inputs:
        D_PINS[nr].switch_to_input()
        IO_DIRS = set_bit(IO_DIRS, nr)
else:
    print("No inputs defined")

# Show state of all D pins
for p in D_PINS:
    print(p)

# D_PINS[0].set_output_mode(3)  # Set output mode to simple push-pull


def get_io_state() -> int:
    """Get the state of all input pins."""
    return sum(pin.value << bit for bit, pin in enumerate(D_PINS))


def set_io_state(state: int) -> None:
    """Set output pins based on the provided state."""
    for bit, pin in enumerate(D_PINS):
        if pin.direction == Direction.OUTPUT:
            pin.value = bool((state >> bit) & 0x01)


async def read_inputs() -> None:
    """Read inputs and send CAN message on change."""
    global device_errors  # pylint: disable=global-statement

    io_state = get_io_state()
    prev_io_state = io_state
    prev_cycle_start = time.monotonic_ns()

    opcode, byte_def = canp.get_opcode_and_bytedef(canp.IoStateMessage)
    msg_id = canp.generate_message_id(NODE_ID, opcode)
    print(f"IOStateMessage ID: {msg_id:x}")

    loop_count = 0
    max_cycle_time = 0.0
    total_cycle_time = 0.0

    while True:

        # D_PINS[0].value = True
        cycle_start = time.monotonic_ns()
        cycle_time = (cycle_start - prev_cycle_start) / 1e6  # Convert to ms
        prev_cycle_start = cycle_start

        io_state = get_io_state()

        if io_state != prev_io_state:
            msg = canio.Message(id=msg_id, data=struct.pack(byte_def, 0, io_state))
            can.send(msg)

        prev_io_state = io_state

        # Free memory
        # gc.collect()

        # D_PINS[0].value = False

        await asyncio.sleep(0)

        max_cycle_time = max(max_cycle_time, cycle_time)
        total_cycle_time += cycle_time
        loop_count += 1

        if loop_count % 1000 == 0:
            avg_cycle_time = total_cycle_time / 1000
            uptime_h = time.monotonic() / 3600
            print(
                f"timing: {avg_cycle_time:.2f}ms, Max: {max_cycle_time:.2f}ms (mem {gc.mem_alloc()} {gc.mem_free()}) Uptime: {uptime_h:.2f}h"
            )

            if max_cycle_time > 10:
                print("***************** Long cycle time ********************")
                device_errors = set_bit(device_errors, ErrorBits.LONG_LOOP_TIME)

            max_cycle_time = 0.0
            total_cycle_time = 0.0


async def heartbeat_loop() -> None:
    """Send heartbeat messages at regular intervals."""

    counter = 0
    opcode, byte_def = canp.get_opcode_and_bytedef(canp.HeartbeatMessage)
    msg_id = canp.generate_message_id(NODE_ID, opcode)  # type: ignore
    print(f"HeartbeatMessage ID: {msg_id:x}")

    while True:
        msg = canp.HeartbeatMessage(
            device_type=12,
            io_dir=IO_DIRS,
            io_state=get_io_state(),
            errors=device_errors,
            counter=counter & 0xFF,
        )
        can_msg = canio.Message(id=msg_id, data=struct.pack(byte_def, *msg))
        can.send(can_msg)

        led1.value = not led1.value
        counter += 1
        await asyncio.sleep(0.1)


async def receive_can_message() -> None:
    """Listen for and process incoming CAN messages."""
    listener = can.listen(timeout=0)
    while True:
        if listener.in_waiting():
            msg = listener.receive()
            if msg and canp.get_node_id(msg.id) == NODE_ID:
                if isinstance(msg, canio.RemoteTransmissionRequest):
                    print(f"RTR message {msg.id:x}")
                else:
                    decoded_msg = canp.decode_message(msg.id, msg.data)
                    print(f"Received message: {decoded_msg}")

                    if isinstance(decoded_msg, canp.IoStateMessage):
                        if decoded_msg.op == 1:
                            set_io_state(decoded_msg.io_state)
                            print(f"IO state set to: {decoded_msg.io_state}")

        await asyncio.sleep(0.001)  # Yield to other tasks


async def check_errors() -> None:
    """Check for device errors and update error LED."""

    global device_errors  # pylint: disable=global-statement

    error_led = led2
    error_led.value = False

    while True:
        if can.state != canio.BusState.ERROR_ACTIVE:
            device_errors = set_bit(device_errors, ErrorBits.CAN_ERROR)
        else:
            device_errors = clear_bit(device_errors, ErrorBits.CAN_ERROR)

        error_led.value = bool(device_errors)
        await asyncio.sleep(1)


# ---------------------main---------------------------------------------


async def main() -> None:

    await asyncio.gather(
        read_inputs(),
        heartbeat_loop(),
        check_errors(),
        receive_can_message(),
    )


asyncio.run(main())
