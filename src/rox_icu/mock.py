#!/usr/bin/env python3
"""
ICU Mock CAN Interface Module

This module provides a mock implementation of the ICU (Integrated Control Unit) CAN interface.
It simulates CAN-based remote I/O control for testing and development purposes, supporting message
encoding/decoding, MQTT integration, and simulated I/O toggling.

Key Features:
- CAN communication simulation using `python-can`.
- I/O state management with message broadcasting.
- Heartbeat generation for system health monitoring.
- MQTT command interface for remote I/O control.
- Support for toggling outputs in a simulated environment.

Classes:
- ICUMock: Core class that simulates the ICU interface, providing methods for managing I/O states,
  sending heartbeats, and handling CAN or MQTT messages.

Functions:
- main(node_id: int): Entry point for running the mock interface as a standalone application.

MQTT Command Structure:
The MQTT interface allows remote interaction with the ICU mock through structured JSON messages.
Commands are published to the topic `/icu_mock/<node_id>/cmd` and must follow the format:
```json
{
    "cmd": "<command_name>",
    "args": {
        "arg1": <value>,
        "arg2": <value>,
        ...
    }
}
````


Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import asyncio
import orjson
import logging

import aiomqtt
import can
from can.interfaces.socketcan import SocketcanBus
from can.interfaces.udp_multicast import UdpMulticastBus

import rox_icu.can_protocol as canp
from rox_icu.can_utils import get_can_bus
from rox_icu.utils import run_main
from rox_icu.bit_ops import set_bit, clear_bit

# Constants for CAN messages
NODE_ID = 0x01
DEVICE_TYPE = 201

# CAN logger to INFO level
logger_can = logging.getLogger("can")
if logger_can is not None:
    logger_can.setLevel(logging.INFO)


class ICUMock:
    """Class to mock the ICU CAN interface."""

    MQTT_BASE_TOPIC = "/icu_mock"

    def __init__(
        self,
        node_id: int = NODE_ID,
        can_bus: SocketcanBus | UdpMulticastBus | None = None,
        simulate_inputs: bool = False,
        mqtt_broker: str | None = None,  # use mqtt interface if provided
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

        self._mqtt_broker = mqtt_broker

        self._state_queue: asyncio.Queue[int] = (
            asyncio.Queue()
        )  # queue for state updates

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

        # Update the state queue
        if self._mqtt_broker is not None:
            self._state_queue.put_nowait(new_state)

    def set_pin(self, pin: int, state: bool) -> None:
        """Set the state of a pin."""
        self._log.info(f"Setting pin {pin} to {state}")
        if state:
            self.io_state = set_bit(self._io_state, pin)
        else:
            self.io_state = clear_bit(self._io_state, pin)

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
                io_dir=0,  # All outputs
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

    async def send_mqtt_state(self, client: aiomqtt.Client):
        """Send the current I/O state to the MQTT broker."""
        state_topic = f"{self.MQTT_BASE_TOPIC}/{self.node_id}/state"

        self._log.info(f"Publishing state to MQTT topic: {state_topic}")

        while True:
            state = await self._state_queue.get()
            await client.publish(state_topic, state)
            self._state_queue.task_done()

    async def receive_mqtt_commands(self, client: aiomqtt.Client):
        """Receive and process MQTT commands."""
        self._log.info("Receiving MQTT commands")

        commands = {"set_pin": self.set_pin}

        cmd_topic = f"{self.MQTT_BASE_TOPIC}/{self.node_id}/cmd"

        self._log.info(f"Subscribing to MQTT topic: {cmd_topic}")

        await client.subscribe(cmd_topic)
        async for message in client.messages:
            try:
                self._log.info(f"{message.topic=}, {message.payload=}")
                if not isinstance(message.payload, (str, bytes, bytearray)):
                    raise TypeError(f"Unexpected payload type {type(message.payload)}")

                payload = orjson.loads(message.payload)

                # command format {"cmd": "set_pin", "args: {"pin": 0, "state": 1}}
                cmd = payload["cmd"]
                args = payload["args"]

                if cmd not in commands:
                    raise ValueError(f"Invalid command: {cmd}")

                commands[cmd](**args)

            except (TypeError, orjson.JSONDecodeError) as e:
                self._log.error(f"Error decoding message {message.payload!r}: {e}")

            except Exception as e:
                self._log.exception(e, exc_info=True)

    async def mqtt_loop(self):
        """handle mqtt interface if broker address is provided"""
        if self._mqtt_broker is None:
            self._log.info("No MQTT broker address provided, skipping MQTT loop")
            return

        self._log.info(f"Connecting to MQTT broker: {self._mqtt_broker}")
        async with aiomqtt.Client(self._mqtt_broker) as client:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.send_mqtt_state(client))
                tg.create_task(self.receive_mqtt_commands(client))

    async def main(self):
        """Main async loop for the ICU mock."""
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.heartbeat_loop())
            tg.create_task(self.message_handler())
            tg.create_task(self.toggle_outputs())
            tg.create_task(self.mqtt_loop())

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
