""" send can messages and measure loop timing on Feather M4 CAN """

import gc
import struct
import time

import board
import canio
import digitalio
import neopixel


def can_init() -> canio.CAN:
    """initialize the CAN bus"""
    # If the CAN transceiver has a standby pin, bring it out of standby mode
    if hasattr(board, "CAN_STANDBY"):
        standby = digitalio.DigitalInOut(board.CAN_STANDBY)
        standby.switch_to_output(False)

    # If the CAN transceiver is powered by a boost converter, turn on its supply
    if hasattr(board, "BOOST_ENABLE"):
        boost_enable = digitalio.DigitalInOut(board.BOOST_ENABLE)
        boost_enable.switch_to_output(True)

    # Use this line if your board has dedicated CAN pins. (Feather M4 CAN and Feather STM32F405)
    return canio.CAN(
        rx=board.CAN_RX, tx=board.CAN_TX, baudrate=500_000, auto_restart=True
    )


led = digitalio.DigitalInOut(board.LED)
led.switch_to_output()

px = neopixel.NeoPixel(board.NEOPIXEL, 1)
px.brightness = 0.1
px.fill((0, 255, 0))


can = can_init()
old_bus_state = None
counter = 0

loop_count = 0
max_loop_time = 0.0
total_loop_time = 0.0


while True:
    loop_start = time.monotonic()  # Use monotonic for ms precision

    bus_state = can.state
    if bus_state != old_bus_state:
        print(f"Bus state changed to {bus_state}")
        old_bus_state = bus_state

    # Send a message with the counter value
    counter += 1
    counter &= 0xFFFFFFFF
    message = canio.Message(id=0x01, data=struct.pack("<I", counter))
    can.send(message)

    gc.collect()  # force garbage collection

    # -------- calculate loop time

    loop_time = (time.monotonic() - loop_start) * 1000  # Convert to ms
    max_loop_time = max(max_loop_time, loop_time)
    total_loop_time += loop_time
    loop_count += 1

    if loop_count % 1000 == 0:
        avg_loop_time = total_loop_time / 1000
        uptime_h = time.monotonic() / 3600
        print(
            f"timing: {avg_loop_time:.2f}ms, Max: {max_loop_time:.2f}ms (mem {gc.mem_alloc()} {gc.mem_free()} ) Uptime: {uptime_h:.2f}h"
        )
        led.value = not led.value

        if max_loop_time > 10:
            print("***************** Long looptime ********************")
            px.fill((0, 0, 255))
        elif bus_state != canio.BusState.ERROR_ACTIVE:
            print("***************** Bus error ********************")
            px.fill((255, 0, 0))
        else:
            px.fill((0, 255, 0))

        max_loop_time = 0.0
        total_loop_time = 0.0
