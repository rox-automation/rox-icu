"""demonstrate can usage basics on Feather M4 CAN"""


# SPDX-FileCopyrightText: 2020 Jeff Epler for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import struct
import time

import canio
import can_utils


can = can_utils.can_init()
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

    time.sleep(1.0)
