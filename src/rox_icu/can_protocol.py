#!/usr/bin/env python3
# Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""
ROX-ICU CAN Protocol Implementation

Works both in MicroPython and CPython.

Key Features:
-------------
- Compatible with fixed-length and variable-length message formats.
- Dynamic support for parameter-based messages, with `ParameterMessage`.
- Uses an 11-bit structured message ID for efficient communication:
  - Upper 6 bits: Node ID (0-63, with 0 reserved for broadcast)
  - Lower 5 bits: Command ID (0-31)

Message Types:
--------------
- **HaltMessage**: Halts operations with a specific IO state.
- **HeartbeatMessage**: Provides periodic status updates, including device type, IO state, errors, and a counter.
- **IoStateMessage**: Reports or sets IO state changes.
- **ParameterMessage**: Handles parameter updates or retrievals using signed 32 bit integer.

Byte format:
-------------
This interface uses LITTLE ENDIAN ('<') byte order for all messages.

Adding Custom Messages:
-----------------------
1. Define the message using a `namedtuple` or a custom class.
2. Register the message type in the `_MSG_DEFS` dictionary with an associated opcode and format.
3. Define the data structure using `struct` format characters (e.g., `B=uint8`, `H=uint16`).


"""


import struct
from collections import namedtuple

try:  # circuitpython does not have typing module
    from typing import Type, NamedTuple, Tuple  # pragma: no cover
except ImportError:  # pragma: no cover
    pass


VERSION = 23


# -----------------Data Types-----------------
# See https://docs.python.org/3/library/struct.html#format-characters

BOOL = "?"
UINT8 = "B"
INT8 = "b"
UINT16 = "H"
INT16 = "h"
UINT32 = "I"
INT32 = "i"
FLOAT = "f"


# ----------------------------Message Definitions----------------------------
# opcode 0
HaltMessage = namedtuple("HaltMessage", "io_state")  # halt with desired io state.


# normally sent every 100ms
HeartbeatMessage = namedtuple(
    "HeartbeatMessage",
    ("device_type", "io_dir", "io_state", "errors", "counter"),
)


IoStateMessage = namedtuple("IoStateMessage", "io_state")
SetIoStateMessage = namedtuple("SetIoStateMessage", "io_state")

SetParameterMessage = namedtuple("SetParameterMessage", ("param_id", "value"))
GetParameterMessage = namedtuple("GetParameterMessage", ("param_id"))


# ----------------------------Internal lookup tables---------------------------

# message: (opcode, byte_def)
MSG_DEFS = {
    message_type: (opcode, byte_def)
    for opcode, (message_type, byte_def) in enumerate(
        [
            (HaltMessage, "<B"),
            (HeartbeatMessage, "<BBBBB"),
            (IoStateMessage, "<B"),
            (SetIoStateMessage, "<B"),
            (SetParameterMessage, "<Bi"),
            (GetParameterMessage, "<B"),
        ]
    )
}
OPCODE2MSG = {v[0]: k for k, v in MSG_DEFS.items()}


# ----------------------------Utility Functions----------------------------
def generate_message_id(node_id: int, opcode: int) -> int:
    """Generates an 11-bit message ID from opcode and node ID."""
    return (node_id << 5) | opcode


def split_message_id(message_id: int) -> "tuple[int, int]":
    """Splits a 11-bit message ID into opcode and node ID."""
    opcode = message_id & 0x1F  # Extract lower 5 bits for cmd_id
    node_id = message_id >> 5  # Shift right by 5 bits to get node_id
    return node_id, opcode


def get_node_id(message_id: int) -> int:
    """Get the node ID from a message ID."""
    return message_id >> 5


def get_opcode_and_bytedef(message_class: "Type[NamedTuple]") -> "Tuple[int, str]":
    """Get the opcode for a message type."""

    return MSG_DEFS[message_class]  # type: ignore


def encode_message(message: "NamedTuple", node_id: int) -> "Tuple[int, bytes]":
    """Pack a message into arbitration ID and data bytes.
    returns: (arbitration_id, data_bytes)"""

    opcode, byte_def = get_opcode_and_bytedef(type(message))
    arbitration_id = generate_message_id(node_id, opcode)

    return arbitration_id, struct.pack(byte_def, *message)


# Note: not using can.Message because it's not available in MicroPython
def decode_message(arb_id: int, data: "bytes | bytearray") -> "NamedTuple":
    """Parse a message from raw data."""
    opcode = arb_id & 0x1F
    message_class = OPCODE2MSG[opcode]

    return message_class(*struct.unpack(MSG_DEFS[message_class][1], data))  # type: ignore
