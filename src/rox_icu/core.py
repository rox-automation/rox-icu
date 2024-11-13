#!/usr/bin/env python3
"""
ICU CAN driver

Copyright (c) 2024 ROX Automation
"""
from __future__ import annotations

import asyncio
import logging
import threading
import time
from typing import Literal, Optional

import can
from can.interfaces.socketcan import SocketcanBus
from can.interfaces.udp_multicast import UdpMulticastBus

from rox_icu import can_protocol as canp
from rox_icu.can_utils import get_can_bus

# message timeout in seconds
MESSAGE_TIMEOUT = 1.0  # message expiration time & can timeout
HEARTBEAT_TIMEOUT = 0.5  # heartbeat specific timeout


class DeviceError(Exception):
    """ICU device error"""


class HeartbeatError(Exception):
    """No heartbeat error"""


class AutoClearEvent(asyncio.Event):
    """Event that automatically clears itself after all waiters are done"""

    def __init__(self) -> None:
        super().__init__()
        self._active_waiters: int = 0

    async def wait(self) -> Literal[True]:
        self._active_waiters += 1
        try:
            return await super().wait()
        finally:
            self._active_waiters -= 1
            if self._active_waiters == 0:
                self.clear()


class Pin:
    """Represents a single I/O pin with its state and events"""

    def __init__(
        self, number: int, is_input: bool = False, parent: ICU | None = None
    ) -> None:
        self._parent = parent
        self._number: int = number
        self._is_input: bool = is_input
        self._state: bool = False
        self._previous_state: bool = False
        self.high_event: AutoClearEvent = AutoClearEvent()
        self.low_event: AutoClearEvent = AutoClearEvent()
        self.change_event: AutoClearEvent = AutoClearEvent()

    @property
    def number(self) -> int:
        return self._number

    @property
    def is_input(self) -> bool:
        return self._is_input

    @property
    def state(self) -> bool:
        return self._state

    @state.setter
    def state(self, new_state: bool) -> None:
        if self._is_input:
            raise ValueError("pin is read-only")

        if self._parent is None:
            raise RuntimeError("parent is not set")

        self._parent.io_state = self._parent.io_state & ~(1 << self._number) | (
            new_state << self._number
        )

    def _update(self, new_state: bool) -> None:
        """update pin state, set events, used by ICU class"""

        if new_state == self._state:
            return

        self._previous_state = self._state
        self._state = new_state

        # Set appropriate events
        self.change_event.set()
        if new_state:
            self.high_event.set()
        else:
            self.low_event.set()


class ICU:
    """ICU CAN driver"""

    def __init__(
        self,
        node_id: int,
        can_bus: UdpMulticastBus | SocketcanBus | None = None,
    ) -> None:
        self._log = logging.getLogger(f"icu.{node_id}")
        self._node_id = node_id

        self._bus = can_bus or get_can_bus()

        self._receive_thread: Optional[threading.Thread] = None
        self._msg_task: Optional[asyncio.Task] = None
        self._msg_queue: asyncio.Queue = asyncio.Queue()

        self._last_heartbeat: Optional[canp.HeartbeatMessage] = None
        self._last_heartbeat_time: float = 0
        self._heartbeat_event = asyncio.Event()

        self._ignored_messages: set = set()
        self._running = True

        self._io_state: int = 0

        self.pins = [Pin(i, parent=self) for i in range(8)]

    @property
    def node_id(self) -> int:
        """Node ID"""
        return self._node_id

    @property
    def io_state(self) -> int:
        """Get IO state"""
        return self._io_state

    @io_state.setter
    def io_state(self, state: int) -> None:
        """Set output state, provide a byte for all 8 outputs"""

        self._log.debug(f"> {self._node_id=} {state=}")

        self.check_alive()

        arb_id, msg_data = canp.encode_message(
            canp.IOSetMessage(state), node_id=self._node_id
        )

        self._bus.send(
            can.Message(arbitration_id=arb_id, data=msg_data, is_extended_id=False)
        )

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

    @property
    def last_heartbeat(self) -> canp.HeartbeatMessage | None:
        """Get last heartbeat message"""
        return self._last_heartbeat

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

    def _uptate_io_state(self, io_state: int) -> None:
        """Update IO state"""
        self._io_state = io_state

        for i in range(8):
            # pylint: disable=protected-access
            self.pins[i]._update(bool(io_state & (1 << i)))

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
                    self._uptate_io_state(self._last_heartbeat.io_state)
                    self._heartbeat_event.set()
                    self._log.debug(f"heartbeat: {self._last_heartbeat}")

                elif isinstance(msg, canp.IOStateMessage):
                    self._uptate_io_state(msg.io_state)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._log.error(f"Error processing message: {e}")

        self._log.debug("Message handler stopped")
