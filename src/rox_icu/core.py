from __future__ import annotations

import asyncio
import time
import logging
import threading
from typing import Optional, Tuple

import can
import can_protocol as protocol

MESSAGE_TIMEOUT: float = 1.0  # message expiration time & can timeout
ICU_DEVICE_TYPE: int = 0x01


class DeviceDead(Exception):
    """No heartbeat error"""


class Timer:
    """Timer class, including timeout"""

    def __init__(self, timeout: float) -> None:
        self.timeout: float = timeout
        self.start_time: float = time.time()

    def is_timeout(self) -> bool:
        """Check if timeout has expired"""
        return time.time() - self.start_time > self.timeout

    def reset(self) -> None:
        """Reset timer"""
        self.start_time = time.time()

    def elapsed(self) -> float:
        """Return elapsed time since timer was started"""
        return time.time() - self.start_time


class ICU:
    """ICU device"""

    def __init__(self, node_id: int) -> None:
        self.node_id: int = node_id
        self.io_state: int = 0
        self._heartbeat_msg: Optional[protocol.HeartbeatMessage] = None
        self._hb_timer: Timer = Timer(timeout=0.5)

    def process_message(self, opcode: int, data: bytes) -> None:
        """Process incoming message"""
        match opcode:
            case 1:
                self._heartbeat_msg = protocol.HeartbeatMessage(*data)
                self.io_state = self._heartbeat_msg.io_state
                self._hb_timer.reset()
            case 2:
                msg = protocol.IOStateMessage(*data)
                self.io_state = msg.io_state
            case _:
                pass


class Supervisor:
    """listens to can messages and manages devices"""

    def __init__(
        self, interface: str = "can0", interface_type: str = "socketcan"
    ) -> None:
        self._log: logging.Logger = logging.getLogger(self.__class__.__name__)
        self._bus: can.BusABC = can.interface.Bus(
            channel=interface, interface=interface_type
        )
        self._recieve_thread: Optional[threading.Thread] = None
        self._msg_queue: asyncio.Queue[Tuple[int, int, bytes]] = asyncio.Queue()
        self._running: threading.Event = threading.Event()
        self._msg_task: Optional[asyncio.Task[None]] = None

    async def start(self) -> None:
        """start driver"""
        self._log.info("Starting...")
        self._running.set()

        loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        self._recieve_thread = threading.Thread(
            target=self._can_reader_thread, args=(loop,), daemon=True
        )
        self._recieve_thread.start()

        self._msg_task = asyncio.create_task(self._message_handler())

        self._log.info("started")

    def stop(self) -> None:
        """stop driver"""
        self._log.info("stopping driver")
        self._running.clear()

        if self._msg_task is not None:
            self._msg_task.cancel()

        if self._recieve_thread is not None:
            self._recieve_thread.join()

        self._log.info("driver stopped")

    def _can_reader_thread(self, loop: asyncio.AbstractEventLoop) -> None:
        """receive can messages, filter and put them into the queue"""
        while self._running.is_set():
            msg: Optional[can.Message] = self._bus.recv(MESSAGE_TIMEOUT)
            if not msg:
                self._log.warning("can timeout")
                continue

            if msg.is_remote_frame:
                self._log.warning("RTR message received")
                continue

            node_id, opcode = protocol.split_message_id(msg.arbitration_id)

            self._log.debug(f"< {node_id=} {opcode=} {msg.data=}")

            try:
                asyncio.run_coroutine_threadsafe(
                    self._msg_queue.put((node_id, opcode, msg.data)), loop
                )
            except RuntimeError:
                # The event loop is closed, time to exit
                break

        self._log.debug("CAN reader thread stopped")

    async def _message_handler(self) -> None:
        """handle received message"""
        await asyncio.sleep(0.1)  # wait for the queue to be ready

        while self._running.is_set():
            try:
                node_id, opcode, data = await asyncio.wait_for(
                    self._msg_queue.get(), timeout=0.1
                )
                self._msg_queue.task_done()

                match opcode:
                    case 0:
                        pass
                    case 1:
                        if len(data) != 6:
                            self._log.debug("Invalid heartbeat message length")
                            continue
                        msg: protocol.HeartbeatMessage = protocol.HeartbeatMessage(
                            *data
                        )
                        self._log.debug(f"Heartbeat message: {msg}")
                    case 2:
                        pass
            except asyncio.TimeoutError:
                # This allows the loop to check the running flag periodically
                continue

        self._log.debug("message handler stopped")

    def close(self) -> None:
        """Close the CAN bus"""
        if hasattr(self, "_bus"):
            self._bus.shutdown()

    def __enter__(self) -> Supervisor:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        self.stop()
        self.close()


if __name__ == "__main__":
    import coloredlogs
    from rox_icu.utils import LOG_FORMAT, TIME_FORMAT

    coloredlogs.install(level="DEBUG", fmt=LOG_FORMAT, datefmt=TIME_FORMAT)

    async def main() -> None:
        with Supervisor(interface="slcan0") as supervisor:
            await supervisor.start()
            await asyncio.sleep(1)
        print("done")

    asyncio.run(main())
