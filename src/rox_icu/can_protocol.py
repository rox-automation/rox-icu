#!/usr/bin/env python3
"""
Simple CAN protocol for ROX devices.

This module provides a lightweight implementation of a CAN protocol designed for ROX devices.
It is compatible with both CPython and MicroPython, making it suitable for use in
low-resource environments such as embedded systems.

Protocol Definition
===================

Message ID: 11 bits, containing opcode and node ID.

* Upper 6 bits - Node ID - max 0x3F (63)
* Lower 5 bits - Command ID - max 0x1F (31)

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
    from typing import NamedTuple, Tuple
except ImportError:  # pragma: no cover
    pass

from collections import namedtuple

VERSION = 6


def generate_message_id(node_id: int, opcode: int) -> int:
    """Generates an 11-bit message ID from opcode and node ID."""
    return (node_id << 5) | opcode


def split_message_id(message_id: int) -> Tuple[int, int]:
    """Splits a 11-bit message ID into opcode and node ID."""

    # same as odrive 3.6
    opcode = message_id & 0x1F  # Extract lower 5 bits for cmd_id
    node_id = message_id >> 5  # Shift right by 5 bits to get node_id

    return node_id, opcode


# opcode 0
HaltMessage = namedtuple("HaltMessage", "io_state")  # halt with desired io state.


# opcode 1, normally sent every 100ms
HeartbeatMessage = namedtuple(
    "HeartbeatMessage",
    ("device_type", "error_max1", "error_max2", "io_state", "counter"),
)

# opcode 2, sent on change or request
IOStateMessage = namedtuple("IOStateMessage", "io_state")

# (message, byte_def) opcode is index
MESSAGES = ((HaltMessage, "<B"), (HeartbeatMessage, "<BBBBB"), (IOStateMessage, "<B"))


def get_opcode_and_bytedef(cls: NamedTuple) -> Tuple[int, str]:
    """Get the opcode for a message type."""
    for opcode, (msg_cls, byte_def) in enumerate(MESSAGES):
        if cls == msg_cls:
            return opcode + 1, byte_def
    raise ValueError("Unknown message type")
