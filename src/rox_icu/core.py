#!/usr/bin/env python3
"""
ICU CAN driver

Copyright (c) 2024 ROX Automation
"""

import asyncio
import logging
import threading
import time
from typing import Callable, Optional

import can

from rox_icu import can_protocol as canp
from rox_icu.utils import run_main


# message timeout in seconds
MESSAGE_TIMEOUT = 1.0  # message expiration time & can timeout
HEARTBEAT_TIMEOUT = 0.5  # heartbeat specific timeout


class DeviceError(Exception):
    """ICU device error"""


class HeartbeatError(Exception):
    """No heartbeat error"""


class ICU:
    """ICU CAN driver"""

    def __init__(
        self,
        node_id: int,
        interface: str = "can0",
        interface_type: str = "socketcan",
        on_dio_change: Optional[Callable[["ICU"], None]] = None,
    ) -> None:
        self._log = logging.getLogger(f"icu.{node_id}")
        self._node_id = node_id

        self._bus = can.interface.Bus(channel=interface, interface=interface_type)

        self._receive_thread: Optional[threading.Thread] = None
        self._msg_task: Optional[asyncio.Task] = None
        self._msg_queue: asyncio.Queue = asyncio.Queue()

        self._last_heartbeat: Optional[canp.HeartbeatMessage] = None
        self._last_heartbeat_time: float = 0
        self._heartbeat_event = asyncio.Event()

        self._ignored_messages: set = set()
        self._running = True

        # Public state
        self.io_state: int = 0

        # Optional callback for IO state changes
        self.on_dio_change: Optional[Callable[["ICU"], None]] = on_dio_change

    @property
    def node_id(self) -> int:
        """Node ID"""
        return self._node_id

    def check_alive(self) -> None:
        """Check if device is alive, raise an exception if not"""
        if self._last_heartbeat is None:
            raise HeartbeatError("Error: No heartbeat message received.")

        if time.time() - self._last_heartbeat_time > HEARTBEAT_TIMEOUT:
            raise HeartbeatError("Error: Heartbeat message timeout.")

    async def wait_for_heartbeat(self, timeout: float = 1.0) -> None:
        """Wait for heartbeat message"""
        self._heartbeat_event.clear()
        self._log.debug("waiting for heartbeat")
        try:
            await asyncio.wait_for(self._heartbeat_event.wait(), timeout)
        except asyncio.TimeoutError as e:
            raise HeartbeatError("Timeout waiting for heartbeat") from e

    async def start(self) -> None:
        """Start driver"""
        self._log.info(
            f"Starting. node_id={self._node_id}, bus={self._bus.channel_info}"
        )

        loop = asyncio.get_running_loop()
        self._receive_thread = threading.Thread(
            target=self._can_reader_thread, args=(loop,), daemon=True
        )
        self._receive_thread.start()

        self._msg_task = asyncio.create_task(self._message_handler())

        # Wait for first heartbeat
        self._log.info("waiting for first heartbeat")
        await self.wait_for_heartbeat()

        self._log.info("started")

    async def stop(self) -> None:
        """Stop driver"""
        self._log.info("stopping driver")
        self._running = False

        if self._msg_task is not None:
            self._msg_task.cancel()
            try:
                await self._msg_task
            except asyncio.CancelledError:
                pass

        if self._receive_thread is not None:
            self._receive_thread.join(timeout=1.0)

        if hasattr(self, "_bus"):
            self._bus.shutdown()

        self._log.info("stopped")

    def _can_reader_thread(self, loop: asyncio.AbstractEventLoop) -> None:
        """Receive CAN messages, filter and put them into the queue"""
        timeout_warned = False

        while self._running:
            try:
                msg = self._bus.recv(MESSAGE_TIMEOUT)
                if not msg:
                    if not timeout_warned:
                        self._log.warning("can timeout")
                        timeout_warned = True
                    continue
                else:
                    if timeout_warned:
                        self._log.info("message flow restored")
                    timeout_warned = False

                node_id, opcode = canp.split_message_id(msg.arbitration_id)

                # Ignore messages that aren't for this node
                if node_id != self._node_id:
                    continue

                # Ignore messages that were requested to be ignored
                if opcode in self._ignored_messages:
                    continue

                # RTR messages are requests for data
                if msg.is_remote_frame:
                    self._log.warning("RTR message received")
                    continue

                self._log.debug(f"< {node_id=} {opcode=}")

                if self._running:  # Check again before queueing
                    asyncio.run_coroutine_threadsafe(
                        self._msg_queue.put((msg.arbitration_id, bytes(msg.data))), loop
                    )

            except Exception as e:
                if self._running:  # Only log if we're still meant to be running
                    self._log.error(f"Error in CAN reader thread: {e}")
                break

        self._log.debug("CAN reader thread stopped")

    async def _message_handler(self) -> None:
        """Handle received messages"""
        while self._running:
            try:
                arb_id, data = await self._msg_queue.get()
                self._msg_queue.task_done()

                msg = canp.decode_message(arb_id, data)

                if isinstance(msg, canp.HeartbeatMessage):
                    self._last_heartbeat = msg
                    self._last_heartbeat_time = time.time()
                    self.io_state = self._last_heartbeat.io_state
                    self._heartbeat_event.set()
                    self._log.debug(f"heartbeat: {self._last_heartbeat}")

                elif isinstance(msg, canp.IOStateMessage):
                    msg = canp.IOStateMessage(*data)
                    self.io_state = msg.io_state

                    if self.on_dio_change is not None:
                        self.on_dio_change(self)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._log.error(f"Error processing message: {e}")

        self._log.debug("Message handler stopped")


async def _demo(icu: ICU) -> None:
    """Run ICU with proper startup and shutdown handling"""
    try:
        await icu.start()
        while True:
            await asyncio.sleep(1)
            logging.info(f"IO State: {icu.io_state:08b}")
    except (KeyboardInterrupt, asyncio.CancelledError):
        logging.info("Shutdown requested")
    finally:
        await icu.stop()


if __name__ == "__main__":

    async def main() -> None:
        icu = ICU(node_id=1, interface="slcan0")
        await _demo(icu)

    run_main(main())
