#!/usr/bin/env python3
"""
control ICU device remotely.

ICU functions as remote I/O device with CAN interface.

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import asyncio
import logging

import can

import rox_icu.can_protocol as canp
from rox_icu.can_utils import get_can_bus
from rox_icu.utils import run_main_async

NODE_ID = 0x01


log = logging.getLogger("master")


# Callback function to process received messages
def print_message(msg):
    log.info(f"callback: {msg}")


# Coroutine to send messages
async def send_messages(bus) -> None:
    io_state = 0

    try:
        for _ in range(256):
            io_msg = canp.IoStateMessage(io_state)

            arb_id, data = canp.encode_message(io_msg, NODE_ID)

            bus_msg = can.Message(arbitration_id=arb_id, data=data)
            bus.send(bus_msg)

            # shift the io_state by 1 bit
            io_state = io_state << 1

            # reset the io_state to 1 if in overflow
            if io_state & 0xFF == 0:
                io_state = 1

            await asyncio.sleep(0.01)
        log.info("Finished sending messages")
    except asyncio.CancelledError:
        log.info("Send messages cancelled")
        raise


# Coroutine to receive messages
async def receive_messages(reader):
    try:
        while True:
            raw_msg = await reader.get_message()
            node_id = canp.get_node_id(raw_msg.arbitration_id)

            try:
                msg = canp.decode_message(raw_msg.arbitration_id, raw_msg.data)
            except KeyError:
                log.error(f"Unknown message: {raw_msg}")
                continue

            log.info(f"< node [{node_id}] message: {msg.__class__.__name__}")

    except asyncio.CancelledError:
        log.info("Receive messages cancelled")
        raise


async def main():
    # Start the sending and receiving coroutines
    bus = get_can_bus()

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


run_main_async(main())
