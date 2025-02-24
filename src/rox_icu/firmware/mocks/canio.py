""" Mock for the CANIO firmware module. """

import warnings
import time
import logging
import can as pycan  # python-can package
from rox_icu.can_utils import get_can_bus

log = logging.getLogger("canio")


# A minimal Message class that mimics CircuitPython's canio.Message.
class Message:
    def __init__(self, id, data):
        self.id = id
        self.data = data


# A minimal placeholder for RemoteTransmissionRequest.
class RemoteTransmissionRequest:
    pass


# BusState with one constant; expand if needed.
class BusState:
    ERROR_ACTIVE = 0


# The CAN class wraps python-can's Bus functionality.
class CAN:
    def __init__(self, rx=None, tx=None, baudrate=500000, auto_restart=True, **kwargs):
        # rx, tx, and auto_restart are ignored in this mock.
        self.baudrate = baudrate
        self.auto_restart = auto_restart
        self.state = BusState.ERROR_ACTIVE  # you can adjust this based on bus status

        # Adjust bustype and channel based on your system.
        try:
            self.bus = get_can_bus()
        except ValueError:
            self.bus = None
            warnings.warn("Failed to initialize python-can bus", RuntimeWarning)

        log.info(f"Initialized python-can bus: {self.bus}")
        self.state = BusState.ERROR_ACTIVE  # or set to a 'normal' state if you prefer

    def send(self, msg):

        can_msg = pycan.Message(
            arbitration_id=msg.id, data=msg.data, is_extended_id=False
        )
        if self.bus:
            self.bus.send(can_msg)

    def listen(self, timeout=0):
        # Return a dummy listener wrapping python-can's receive functionality.
        return DummyListener(self.bus, timeout)


# A simple listener that provides in_waiting() and receive() methods.
class DummyListener:
    def __init__(self, bus, timeout) -> None:
        self._bus = bus
        self._timeout = timeout

    def in_waiting(self) -> bool:
        # For simplicity, always return True; you could integrate a queue for real messages.
        return True

    def receive(self) -> Message | RemoteTransmissionRequest | None:

        can_msg = self._bus.recv(timeout=self._timeout)
        if can_msg:
            return Message(id=can_msg.arbitration_id, data=can_msg.data)

        return None


# --------testing code----------------


def monitor_can() -> None:
    can = CAN()
    print(f"Monitoring {can.bus}")
    listener = can.listen(timeout=0)
    while True:
        if listener.in_waiting():
            msg = listener.receive()
            if msg:
                if isinstance(msg, RemoteTransmissionRequest):
                    print(f"RTR message {msg.id:x}")
                else:
                    print(f"Received message: {msg.id:x} {msg.data.hex()}")
        else:
            print("No message received")
            break
        time.sleep(0.001)


if __name__ == "__main__":
    monitor_can()
