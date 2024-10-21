#!/usr/bin/env python3
"""
ICU Mock CAN Interface

This mock simulates the ICU (Integrated Control Unit) CAN interface, providing a
virtual environment to test the Python driver for remote I/O functionalities.
This implementation is inspired by an ODrive mock previously written.

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import asyncio
import logging
import struct
from typing import Optional

import can
import coloredlogs  # type: ignore
from rox_icu.can_protocol import (
    HeartbeatMessage,
    generate_message_id,
    get_opcode_and_bytedef,
)

# Configuration for logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
TIME_FORMAT = "%H:%M:%S"

# Constants for CAN messages
NODE_ID = 0x01

# CAN logger to INFO level
logger_can = logging.getLogger("can")
if logger_can is not None:
    logger_can.setLevel(logging.INFO)


class ICUMock:
    """Mock of the physical ICU device excluding CAN interface."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.log = logger or logging.getLogger("icu_mock")
        self.io_state = 0  # Represents the state of all I/Os (8 bits for 8 I/Os)
        self.error_max1 = 0
        self.error_max2 = 0

    def get_io_state(self) -> int:
        """Return the current IO state."""
        return self.io_state

    def update_io_state(self, new_state: int):
        """Update the IO state."""
        self.io_state = new_state
        self.log.info(f"Updated IO state: {bin(self.io_state)}")

    def get_global_error(self):
        """Return the error status of max1 and max2."""
        return self.error_max1, self.error_max2


class ICUMockCAN:
    """Class to mock the ICU CAN interface."""

    def __init__(
        self,
        node_id: int = NODE_ID,
        channel: str = "vcan0",
        interface: str = "socketcan",
    ):
        self.log = logging.getLogger(f"icu.mock.{node_id}")
        self.node_id = node_id
        self.channel = channel
        self.interface = interface
        self.icumock = ICUMock(logger=self.log)

        self.log.info(f"Starting mock {node_id=} , {channel=} , {interface=}")
        self.bus = can.interface.Bus(channel=channel, interface=interface)
        self.can_reader = can.AsyncBufferedReader()
        self.notifier = can.Notifier(self.bus, [self.can_reader])

    async def message_handler(self):
        """Handle received CAN messages."""
        self.log.info("Starting message handler")

        while True:
            try:
                msg = await self.can_reader.get_message()
                if msg.arbitration_id >> 5 != self.node_id:
                    # Ignore messages that are not for this node ID
                    continue

                # Decode message
                self.log.info(
                    f"Received message ID: {msg.arbitration_id:x}, Data: {msg.data}"
                )
                # Update IO based on received data (example)
                self.icumock.update_io_state(
                    int.from_bytes(msg.data, byteorder="little")
                )

            except Exception as e:
                self.log.error(f"Error in message handler: {e}")

    async def heartbeat_loop(self, delay: float = 0.1):
        """Send heartbeat message."""
        self.log.info("Starting heartbeat loop")

        opcode, byte_def = get_opcode_and_bytedef(HeartbeatMessage)
        msg_id = generate_message_id(self.node_id, opcode)
        counter = 0

        while True:
            # Construct the heartbeat message
            heartbeat = HeartbeatMessage(
                device_type=1,
                error_max1=self.icumock.error_max1,
                error_max2=self.icumock.error_max2,
                io_state=self.icumock.get_io_state(),
                device_state=0,
                counter=counter,  # Increment counter for each loop
            )
            data_bytes = struct.pack(byte_def, *heartbeat)
            message = can.Message(
                arbitration_id=msg_id,
                data=data_bytes,
                is_extended_id=False,
            )
            self.bus.send(message)
            counter += 1
            counter &= 0xFF  # Wrap around at 255
            await asyncio.sleep(delay)

    async def main(self):
        """Main async loop for the ICU mock."""
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.heartbeat_loop())
            tg.create_task(self.message_handler())

    def start(self):
        """Start the main loop."""
        asyncio.run(self.main())

    def __del__(self):
        """Destructor to clean up resources."""
        self.notifier.stop()
        self.bus.shutdown()


def main(node_id: int = NODE_ID, interface: str = "vcan0"):
    try:
        mock = ICUMockCAN(node_id, interface)
        mock.start()
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt - shutting down ICU mock")


if __name__ == "__main__":
    coloredlogs.install(level="DEBUG", fmt=LOG_FORMAT, datefmt=TIME_FORMAT)
    main()
