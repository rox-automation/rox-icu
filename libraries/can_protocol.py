#!/usr/bin/env python3
#!/usr/bin/env python3
"""
Simple CAN protocol for ROX devices.

This module provides a lightweight implementation of a CAN protocol designed for ROX devices.
It is compatible with both CPython and MicroPython, making it suitable for use in
low-resource environments such as embedded systems.

Protocol Definition
===================

Message ID: 11 bits, containing opcode and node ID.
* bits 10-7: opcode (0-15) - operation code
* bits 6-0: node ID (0-127) - node identifier

Node 0 is reserved for broadcast messages and CANopen NMT messages.

Message Structure
=================

Messages are defined using namedtuples, providing a simple and memory-efficient
structure for handling data. Each message type has an associated opcode and
byte definition for serialization.

Key Components:
1. Message definitions (HeartbeatMessage, IOStateMessage)
2. MESSAGES tuple containing message classes and their byte definitions
3. Utility functions for message ID generation and parsing
4. Functions for packing and unparsing messages

Adding New Messages
===================

To add a new message type:
1. Define a new namedtuple with the required fields
2. Add the new message type to the MESSAGES tuple with its byte definition
3. The opcode for the new message will be its index in the MESSAGES tuple

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

Type Hinting
============

This module uses type hinting for improved code clarity and error detection.
However, to maintain compatibility with MicroPython, which may not support the
`typing` module, type hints are implemented using a try-except block to import
the necessary types.

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

try:
    from typing import NamedTuple
except ImportError:
    pass

from collections import namedtuple
import struct

VERSION = 3


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


def get_opcode(cls: NamedTuple) -> int:
    """Get the opcode for a message type."""
    for opcode, (msg_cls, _) in enumerate(MESSAGES):
        if cls == msg_cls:
            return opcode
    raise ValueError("Unknown message type")


def pack(opcode: int, msg: NamedTuple) -> bytes:
    """
    pack message data into bytes
    for more efficient code packing just use
    struct.pack(byte_def, *msg)"""
    byte_def = MESSAGES[opcode][1]
    return struct.pack(byte_def, *msg)


def parse(opcode: int, data: bytes) -> NamedTuple:
    """Parse a message from message ID and data bytes."""

    message_cls, byte_def = MESSAGES[opcode]
    return message_cls(*struct.unpack(byte_def, data))
