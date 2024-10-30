#!/usr/bin/env python3
"""
control ICU device remotely.

ICU functions as remote I/O device with CAN interface.

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import struct
import asyncio
import can
import logging
from rox_icu.utils import run_main
from rox_icu.can_protocol import (
    IOStateMessage,
    generate_message_id,
    get_opcode_and_bytedef,
)


NODE_ID = 0x01

log = logging.getLogger("master")


# Callback function to process received messages
def print_message(msg):
    log.info(f"callback: {msg}")


# Coroutine to send messages
async def send_messages(bus) -> None:
    opcode, byte_def = get_opcode_and_bytedef(IOStateMessage)
    msg_id = generate_message_id(NODE_ID, opcode)

    io_state = 0

    try:
        for i in range(16):
            io_msg = IOStateMessage(io_state)

            bus_msg = can.Message(
                arbitration_id=msg_id, data=struct.pack(byte_def, *io_msg)
            )
            bus.send(bus_msg)

            # shift the io_state by 1 bit
            io_state = io_state << 1

            # reset the io_state to 1 if in overflow
            if io_state & 0xFF == 0:
                io_state = 1

            await asyncio.sleep(0.5)
        log.info("Finished sending messages")
    except asyncio.CancelledError:
        log.info("Send messages cancelled")
        raise


# Coroutine to receive messages
async def receive_messages(reader):
    try:
        while True:
            msg = await reader.get_message()
            log.info(
                f"Received message ID: {msg.arbitration_id:x}, Data: {msg.data.hex(" ")}"
            )

    except asyncio.CancelledError:
        log.info("Receive messages cancelled")
        raise


async def main():
    # Start the sending and receiving coroutines
    bus = can.interface.Bus(
        channel="vcan0", interface="socketcan", receive_own_messages=True
    )

    reader = can.AsyncBufferedReader()
    notifier = can.Notifier(bus, [reader])

    try:
        # Create tasks for both coroutines
        send_task = asyncio.create_task(send_messages(bus))
        receive_task = asyncio.create_task(receive_messages(reader))

        # Wait for send_task to complete first
        await send_task

        # Once send_task is done, cancel the receive_task
        receive_task.cancel()
        try:
            await receive_task
        except asyncio.CancelledError:
            pass

        print("Done")

    except Exception as e:
        log.error(f"Exception: {e}")
        raise
    finally:
        log.info("Cleaning up")
        notifier.stop()  # Stop the notifier when done
        bus.shutdown()


run_main(main())
