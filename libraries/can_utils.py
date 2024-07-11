"""common CAN utilities"""

import board
import canio
import digitalio


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
    can = canio.CAN(
        rx=board.CAN_RX, tx=board.CAN_TX, baudrate=500_000, auto_restart=True
    )
    return can
