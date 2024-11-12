"""demonstrate can usage basics on ROX ICU board"""

import struct
import time

import canio
from icu_board import can, led1


listener = can.listen(matches=[canio.Match(0x123)], timeout=0.1)


old_bus_state = None
counter = 0

while True:
    bus_state = can.state
    if bus_state != old_bus_state:
        print(f"Bus state changed to {bus_state}")
        old_bus_state = bus_state

    message = listener.receive()
    if message is not None:
        data = message.data  # type: ignore
        print(f"received message: {data!r}")

    # Send a message with the counter value
    counter += 1
    message = canio.Message(id=0x124, data=struct.pack("<I", counter))
    print(f"> {message.data.hex(" ")}")
    can.send(message)

    led1.value = not led1.value

    time.sleep(1.0)
