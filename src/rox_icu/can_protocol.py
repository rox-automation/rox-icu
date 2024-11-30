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
- **ParameterMessage**: Handles parameter updates or retrievals using a flexible format.

Adding Custom Messages:
-----------------------
1. Define the message using a `namedtuple` or a custom class.
2. Register the message type in the `_MSG_DEFS` dictionary with an associated opcode and format.
3. Define the data structure using `struct` format characters (e.g., `B=uint8`, `H=uint16`).


"""


import struct
from collections import namedtuple

try:  # circuitpython does not have typing module
    from typing import TYPE_CHECKING
except ImportError:  # pragma: no cover
    TYPE_CHECKING = False

if TYPE_CHECKING:
    from typing import Type, NamedTuple, Tuple  # pragma: no cover


VERSION = 12


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


class Operation:
    """Operation types for parameter messages."""

    GET = 0
    SET = 1


# Define parameters as a dictionary {name: (param_id, byte_def)}
device_parameters = {
    "io_state": (0, ord(UINT8)),
    "device_state": (1, ord(UINT8)),
    "error_max1": (2, ord(UINT8)),
    "error_max2": (3, ord(UINT8)),
    "test_param": (255, ord(UINT32)),
}

# Create reverse lookup by ID {param_id: byte_def}
params_byte_defs = {param[0]: param[1] for _, param in device_parameters.items()}


# ----------------------------Message Definitions----------------------------
# opcode 0
HaltMessage = namedtuple("HaltMessage", "io_state")  # halt with desired io state.


# normally sent every 100ms
HeartbeatMessage = namedtuple(
    "HeartbeatMessage",
    ("device_type", "io_dir", "io_state", "errors", "counter"),
)

# io (op, io_state), use RTR for get
IoStateMessage = namedtuple("IoStateMessage", ("op", "io_state"))


# device parameter message, (id, op, datatype, value), use RTR for get
# datatype is int derived from struct format character (e.g. ord('I') for UINT32)
ParameterMessage = namedtuple("ParameterMessage", ("param_id", "op", "dtype", "value"))


# ----------------------------Internal lookup tables---------------------------

# message: (opcode, byte_def)
_MSG_DEFS = {
    message_type: (opcode, byte_def)
    for opcode, (message_type, byte_def) in enumerate(
        [
            (HaltMessage, "<B"),
            (HeartbeatMessage, "<BBBBB"),
            (IoStateMessage, "<BB"),
            (ParameterMessage, None),  # variable length
        ]
    )
}
_OPCODE2MSG = {v[0]: k for k, v in _MSG_DEFS.items()}


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

    return _MSG_DEFS[message_class]  # type: ignore


def encode_message(message: "NamedTuple", node_id: int) -> "Tuple[int, bytes]":
    """Pack a message into arbitration ID and data bytes.
    returns: (arbitration_id, data_bytes)"""

    opcode, byte_def = get_opcode_and_bytedef(type(message))
    arbitration_id = generate_message_id(node_id, opcode)

    if isinstance(message, ParameterMessage):  # custom byte_def for variable length
        byte_def = "<BBB" + chr(message.dtype)

    return arbitration_id, struct.pack(byte_def, *message)


# Note: not using can.Message because it's not available in MicroPython
def decode_message(arb_id: int, data: "bytes | bytearray") -> "NamedTuple":
    """Parse a message from raw data."""
    opcode = arb_id & 0x1F
    message_class = _OPCODE2MSG[opcode]

    if message_class == ParameterMessage:
        param_id, op, dtype = data[:3]
        value = struct.unpack(chr(dtype), data[3:])[0]

        return ParameterMessage(param_id, op, dtype, value)

    return message_class(*struct.unpack(_MSG_DEFS[message_class][1], data))  # type: ignore
