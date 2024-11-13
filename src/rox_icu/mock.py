#!/usr/bin/env python3
"""
ICU Mock CAN Interface

This mock simulates the ICU (Integrated Control Unit) CAN interface,
providing a virtual environment to test the Python driver for remote I/O
functionalities.


Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import asyncio
import logging

import can
from can.interfaces.socketcan import SocketcanBus
from can.interfaces.udp_multicast import UdpMulticastBus

import rox_icu.can_protocol as canp
from rox_icu.can_utils import get_can_bus
from rox_icu.utils import run_main

# Constants for CAN messages
NODE_ID = 0x01
DEVICE_TYPE = 201

# CAN logger to INFO level
logger_can = logging.getLogger("can")
if logger_can is not None:
    logger_can.setLevel(logging.INFO)


class ICUMock:
    """Class to mock the ICU CAN interface."""

    def __init__(
        self,
        node_id: int = NODE_ID,
        can_bus: SocketcanBus | UdpMulticastBus | None = None,
        simulate_inputs: bool = False,
    ):
        self._log = logging.getLogger(f"icu.mock.{node_id}")
        self.node_id = node_id

        self._io_state = 0  # Represents the state of all I/Os (8 bits for 8 I/Os)
        self.error_max1 = 0
        self.error_max2 = 0

        self._simulate_inputs = simulate_inputs

        self._bus = can_bus or get_can_bus()
        self._can_reader = can.AsyncBufferedReader()
        self._notifier = can.Notifier(self._bus, [self._can_reader])

    @property
    def io_state(self):
        """Get the IO state."""
        return self._io_state

    @io_state.setter
    def io_state(self, new_state: int) -> None:
        """Set the IO state."""
        self._log.info(f"Setting IO state: {new_state:02x}")
        self._io_state = new_state

        arb_id, data_bytes = canp.encode_message(
            canp.IOStateMessage(self._io_state), self.node_id
        )

        message = can.Message(
            arbitration_id=arb_id,
            data=data_bytes,
            is_extended_id=False,
        )
        self._bus.send(message)

    def get_global_error(self) -> tuple[int, int]:
        """Return the error status of max1 and max2."""
        return self.error_max1, self.error_max2

    async def message_handler(self) -> None:
        """Handle received CAN messages."""
        self._log.info("Starting message handler")

        while True:
            try:
                raw_msg = await self._can_reader.get_message()

                node_id = canp.get_node_id(raw_msg.arbitration_id)

                # Ignore messages that are not for this node ID
                if node_id != self.node_id:
                    continue

                self._log.debug(
                    f"Received message ID: {raw_msg.arbitration_id:x}, Data: {raw_msg.data.hex(' ')}"
                )

                msg = canp.decode_message(raw_msg.arbitration_id, raw_msg.data)

                if isinstance(msg, canp.IOSetMessage):
                    self._log.info(f"Received IOSetMessage: {msg.io_state:02x}")
                    self.io_state = msg.io_state

            except Exception as e:
                self._log.error(f"Error in message handler: {e}")

    async def heartbeat_loop(self, delay: float = 0.1) -> None:
        """Send heartbeat message."""
        self._log.info("Starting heartbeat loop")

        counter = 0

        while True:
            # Construct the heartbeat message
            heartbeat = canp.HeartbeatMessage(
                device_type=DEVICE_TYPE,
                error_max1=self.error_max1,
                error_max2=self.error_max2,
                io_state=self._io_state,
                errors=0,
                counter=counter,  # Increment counter for each loop
            )

            arb_id, data_bytes = canp.encode_message(heartbeat, self.node_id)

            message = can.Message(
                arbitration_id=arb_id,
                data=data_bytes,
                is_extended_id=False,
            )
            self._bus.send(message)
            counter += 1
            counter &= 0xFF  # Wrap around at 255
            await asyncio.sleep(delay)

    async def toggle_outputs(self):
        """Toggle the output pins."""
        if not self._simulate_inputs:
            return

        self._log.info("Starting output toggling loop")

        while True:

            # toggle bit 7
            self.io_state ^= 0x80

            await asyncio.sleep(0.5)

    async def main(self):
        """Main async loop for the ICU mock."""
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.heartbeat_loop())
            tg.create_task(self.message_handler())
            tg.create_task(self.toggle_outputs())

    def start(self):
        """Start the main loop."""
        asyncio.run(self.main())

    def __del__(self):
        """Destructor to clean up resources."""
        self._notifier.stop()
        self._bus.shutdown()


def main(node_id: int = NODE_ID):
    try:
        mock = ICUMock(node_id, simulate_inputs=True)
        mock.start()
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt - shutting down ICU mock")


if __name__ == "__main__":
    run_main(main)
