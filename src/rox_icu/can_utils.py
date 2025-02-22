#!/usr/bin/env python3
"""
 supporting functions for working with can

 Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import os
import struct
from typing import List, NamedTuple, Type
from can.interfaces.socketcan import SocketcanBus
from can.interfaces.udp_multicast import UdpMulticastBus
from cantools.database import Database, Message, Signal, dump_file

import rox_icu.can_protocol as canp


def is_ci_environment() -> bool:
    """Check if the code is running in a CI environment"""
    return os.getenv("CI") == "true"


def get_can_bus(bus_type: str = "env") -> UdpMulticastBus | SocketcanBus:
    """Get a CAN bus instance"""

    match bus_type:
        case "udp_multicast":
            return UdpMulticastBus("224.0.0.1", interface="udp_multicast")

        case "env":

            channel = os.getenv("CAN_CHANNEL")
            if channel is None:
                raise ValueError(
                    "Missing CAN_CHANNEL environment variable, set to can0 or similar"
                )

            return SocketcanBus(
                channel=channel, interface="socketcan", receive_own_messages=False
            )

        case _:  # just use the bus_type as the channel

            return SocketcanBus(
                channel=bus_type, interface="socketcan", receive_own_messages=False
            )


# -----------------Database Functions-----------------
def byte_def_to_size(struct_byte_def: str) -> int:
    """Convert byte definition to number of bytes using struct.calcsize()."""
    return struct.calcsize(struct_byte_def)


def create_signals_from_namedtuple(
    namedtuple_type: Type[NamedTuple], format_string: str
) -> List[Signal]:

    signals = []
    offset = 0

    # Remove byte order character for processing individual formats
    if format_string[0] in "@=<>!":
        format_string = format_string[1:]

    for field_name, fmt in zip(namedtuple_type._fields, format_string):  # type: ignore
        # Calculate the bit length of the field
        bit_length = struct.calcsize(fmt) * 8

        # Determine if the field is signed
        is_signed = fmt.islower() and fmt not in "?"

        # Create the Signal object
        signal = Signal(
            name=field_name,
            start=offset,
            length=bit_length,
            byte_order="little_endian",  # Adjust based on your format string
            is_signed=is_signed,
        )
        signals.append(signal)

        # Update the offset for the next field
        offset += bit_length

    return signals


def create_dbc(node_id: int, filename: str | None = None) -> Database:
    """Create a DBC file for a given node ID"""

    # Create a new database
    db = Database(version=str(canp.VERSION))

    for msg in canp.MSG_DEFS.keys():
        opcode, byte_def = canp.get_opcode_and_bytedef(msg)
        msg_id = canp.generate_message_id(node_id, opcode)
        signals = create_signals_from_namedtuple(msg, byte_def)

        db_msg = Message(
            frame_id=msg_id,
            name="ICU_" + msg.__name__,
            length=byte_def_to_size(byte_def),
            signals=signals,
        )

        db.messages.append(db_msg)

    if filename is not None:
        dump_file(db, filename)

    return db
