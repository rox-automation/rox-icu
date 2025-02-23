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
# ruff: noqa: E402

from rox_icu.firmware import mocks

mocks.mock_hardware()

import asyncio
import orjson
import logging
import aiomqtt

import rox_icu.firmware.remote_io.main as firmware
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

    MQTT_BASE_TOPIC = "/icu_mock"

    def __init__(
        self,
        node_id: int = NODE_ID,
        simulate_inputs: bool = False,
        mqtt_broker: str | None = None,  # use mqtt interface if provided
    ):
        self._log = logging.getLogger(f"icu.mock.{node_id}")

        firmware.NODE_ID = node_id
        self.D_PINS = firmware.D_PINS

        self.error_max1 = 0
        self.error_max2 = 0

        self._simulate_inputs = simulate_inputs

        self._mqtt_broker = mqtt_broker

        self._state_queue: asyncio.Queue[int] = (
            asyncio.Queue()
        )  # queue for state updates

    @property
    def node_id(self) -> int:
        """Get the node ID."""
        return firmware.NODE_ID

    @property
    def io_state(self):
        """Get the IO state."""
        return firmware.get_io_state()

    @io_state.setter
    def io_state(self, new_state: int) -> None:
        """Set the IO state."""
        self._log.info(f"Setting IO state: {new_state:02x}")

        # for bit, pin in enumerate(self.D_PINS):
        #     pin.value = bool((new_state >> bit) & 0x01)

        firmware.set_io_state(new_state)

        # Update the state queue
        if self._mqtt_broker is not None:
            self._state_queue.put_nowait(new_state)

    def set_pin(self, pin: int, state: bool) -> None:
        """Set the state of a pin."""
        self._log.info(f"Setting pin {pin} to {state}")
        self.D_PINS[pin].value = state

    def get_pin(self, pin: int) -> bool:
        """Get the state of a pin."""
        return self.D_PINS[pin].value

    def get_global_error(self) -> tuple[int, int]:
        """Return the error status of max1 and max2."""
        return self.error_max1, self.error_max2

    async def toggle_outputs(self):
        """Toggle the output pins."""
        if not self._simulate_inputs:
            return

        self._log.info("Starting output toggling loop")

        while True:

            # toggle bit 7
            self.io_state ^= 0x80

            await asyncio.sleep(1)

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

        self._log.info(
            f"Starting ICU mock id={self.node_id} on {firmware.can.bus.channel_info}"
        )

        async with asyncio.TaskGroup() as tg:
            tg.create_task(firmware.main())
            tg.create_task(self.toggle_outputs())
            tg.create_task(self.mqtt_loop())

    def start(self):
        """Start the main loop."""
        asyncio.run(self.main())

    def __del__(self) -> None:
        firmware.can.bus.shutdown()


def main(node_id: int = NODE_ID):
    try:
        mock = ICUMock(node_id, simulate_inputs=True)
        mock.start()
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt - shutting down ICU mock")


if __name__ == "__main__":
    run_main(main)
