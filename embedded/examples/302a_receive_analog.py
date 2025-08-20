"""demonstrate can usage basics on ROX ICU board"""

import struct

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
        adc_val = struct.unpack("<H", data)[0]
        print(f"Received ADC value: {adc_val}")


    led1.value = not led1.value
