""" Mock for the CANIO firmware module. """

# canio.py mock for CPython
try:
    import can as pycan  # python-can package
except ImportError:
    pycan = None  # type: ignore
    print("python-can is not installed; CAN operations will be simulated.")


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

        if pycan:
            try:
                # Adjust bustype and channel based on your system.
                self._bus = pycan.interface.Bus(
                    bustype="socketcan", channel="can0", bitrate=baudrate
                )
                self.state = (
                    BusState.ERROR_ACTIVE
                )  # or set to a 'normal' state if you prefer
            except Exception as e:
                print("Error initializing python-can bus:", e)
                self._bus = None
        else:
            self._bus = None

    def send(self, msg):
        if self._bus:
            can_msg = pycan.Message(
                arbitration_id=msg.id, data=msg.data, is_extended_id=False
            )
            try:
                self._bus.send(can_msg)
                print(f"Sent CAN message: id={msg.id}, data={msg.data}")
            except Exception as e:
                print("Error sending message:", e)
        else:
            # When no bus is available, simulate the send.
            print(f"Mock send: id={msg.id}, data={msg.data}")

    def listen(self, timeout=0):
        # Return a dummy listener wrapping python-can's receive functionality.
        return DummyListener(self._bus, timeout)


# A simple listener that provides in_waiting() and receive() methods.
class DummyListener:
    def __init__(self, bus, timeout):
        self._bus = bus
        self._timeout = timeout

    def in_waiting(self):
        # For simplicity, always return False; you could integrate a queue for real messages.
        return False

    def receive(self):
        if self._bus:
            can_msg = self._bus.recv(timeout=self._timeout)
            if can_msg:
                return Message(id=can_msg.arbitration_id, data=can_msg.data)
        return None
