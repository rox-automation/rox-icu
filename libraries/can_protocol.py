#!/usr/bin/env python3
"""
Simple CAN protocol for ROX devices.

This module is designed to be usable in both CPython and MicroPython, catering to low-resource environments such as embedded systems.

Protocol definition
=====================

Message ID : 11 bits, contains opcode and node ID.
* bits 10-7: opcode (0-15) - operation code
* bits 6-0: node ID (0-127) - node identifier

Node 0 is reserved for broadcast messages and CANopen NMT messages.

How Messages Work
=================

1. Messages are defined as standalone classes with their data attributes and methods for packing and unpacking binary data.
2. The `byte_def` attribute in each message class defines the binary structure using struct format characters.
3. The `opcode` class attribute uniquely identifies each message type.
4. Messages are packed into bytes using the `pack` method, which returns both the message ID and the serialized data.
5. Messages are unpacked from bytes using the `from_data` class method.

Adding New Messages
===================

To add a new message type:
1. Define a new class directly handling its data and serialization.
2. Set the `byte_def` attribute with struct format characters in the class.
3. Assign a unique `opcode` as a class attribute.
4. Register the new message class in the `MESSAGES` dictionary to facilitate parsing.

Struct Types Summary
====================

The `struct` module is used for packing and unpacking binary data. Common format characters include:
- 'B': unsigned char (1 byte)
- 'H': unsigned short (2 bytes)
- 'I': unsigned int (4 bytes)
- 'b': signed char (1 byte)
- 'h': signed short (2 bytes)
- 'i': signed int (4 bytes)
- 'f': float (4 bytes)
- 'd': double (8 bytes)

Use '<' for little-endian or '>' for big-endian byte order as required.

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

# TODO: update docstring

from typing import NamedTuple
from collections import namedtuple
import struct


def generate_message_id(opcode: int, node_id: int) -> int:
    """Generates an 11-bit message ID from opcode and node ID."""
    return (opcode << 7) | node_id


def split_message_id(message_id: int) -> tuple[int, int]:
    """Splits a 11-bit message ID into opcode and node ID."""
    node_id = message_id & 0x7F  # Extract the lower 7 bits for the node ID
    opcode = message_id >> 7  # Shift right 7 bits to get the opcode
    return opcode, node_id


# opcode 0
HeartbeatMessage = namedtuple(
    "HeartbeatMessage", "error_code error_count uptime version"
)

# opcode 1
IOStateMessage = namedtuple("IOStateMessage", "io_state")

# (message, byte_def) opcode is index in tuple for easy lookup
MESSAGES = ((HeartbeatMessage, "<BHIB"), (IOStateMessage, "<B"))

# for packing just use
# struct.pack(byte_def, *msg)


def parse(opcode: int, data: bytes) -> NamedTuple:
    """Parse a message from message ID and data bytes."""

    message_cls, byte_def = MESSAGES[opcode]
    return message_cls(*struct.unpack(byte_def, data))
