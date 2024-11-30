#!/usr/bin/env python3
# Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""
ROX CAN Protocol Implementation

This module implements a lightweight CAN (Controller Area Network) protocol for ROX devices,
designed for both CPython and MicroPython environments. It provides message encoding and decoding,
allowing uniform communication across embedded systems using the ROX protocol.

Features:
---------
- Supports fixed-length and variable-length message types.
- Flexible parameter handling with dynamic value decoding for `ParameterMessage`.
- Compact and extensible protocol design using a structured message ID format.

Protocol Structure:
-------------------
Message ID (11 bits):
    - Node ID: Upper 6 bits (0-63, node 0 reserved for broadcast)
    - Command ID: Lower 5 bits (0-31)

Message Types:
--------------
- `HaltMessage`: Stop operation with a specified IO state.
- `HeartbeatMessage`: Periodic status updates with device type, IO state, and error counters.
- `IOStateMessage`: Reports changes to the IO state.
- `IOSetMessage`: Requests to modify the IO state.
- `ParameterMessage`: Variable-length messages for parameter settings.
- `GetParameterMessage`: Requests to retrieve a specific parameter.

Adding New Messages:
--------------------
1. Define the message structure using `namedtuple`.
2. Add an entry to `_MSG_DEFS` with `(opcode, byte_definition)`.
3. Use `struct` format characters for defining data layouts (e.g., `B=uint8`, `H=uint16`).

Usage Example:
--------------
>>> # Create and encode a message
>>> msg = HeartbeatMessage(device_type=1, io_dir=1, io_state=0, errors=0, counter=0)
>>> arb_id, data = encode_message(msg, node_id=1)

>>> # Decode a received message
>>> decoded_msg = decode_message(arb_id, data)

>>> # Encode a parameter message
>>> param_msg = ParameterMessage(param_id=255, value=12345)
>>> arb_id, data = encode_message(param_msg, node_id=1)

>>> # Decode a parameter message
>>> decoded_msg = decode_message(arb_id, data)

Future Enhancements:
--------------------
- Add support for additional generic message types.
- Extend parameter definitions for device-specific configurations.

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
    "io_state": (0, UINT8),
    "device_state": (1, UINT8),
    "error_max1": (2, UINT8),
    "error_max2": (3, UINT8),
    "test_param": (255, UINT32),
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

# sent on change
IoStateMessage = namedtuple("IoStateMessage", "io_state")

# requist to change io state
SetIoMessage = namedtuple("SetIoMessage", "io_state")

# device parameter message, (id, value)
ParameterMessage = namedtuple("ParameterMessage", "param_id, value")

GetParameterMessage = namedtuple("GetParameterMessage", "param_id")
SetParameterMessage = namedtuple("SetParameterMessage", "param_id, value")

# ----------------------------Internal lookup tables---------------------------

# message: (opcode, byte_def)
_MSG_DEFS = {
    message_type: (opcode, byte_def)
    for opcode, (message_type, byte_def) in enumerate(
        [
            (HaltMessage, "<B"),
            (HeartbeatMessage, "<BBBBB"),
            (IoStateMessage, "<B"),
            (SetIoMessage, "<B"),
            (ParameterMessage, None),  # variable length
            (GetParameterMessage, "<B"),
            (SetParameterMessage, None),  # variable length
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

    if byte_def is None:  # custom byte_def for variable length
        byte_def = "<B" + params_byte_defs[message.param_id]

    return arbitration_id, struct.pack(byte_def, *message)


def encode_get_parameter(param_id: int, node_id: int) -> "Tuple[int, bytes]":
    """Encode a GetParameter message."""
    opcode, byte_def = get_opcode_and_bytedef(GetParameterMessage)
    arbitration_id = generate_message_id(node_id, opcode)
    return arbitration_id, struct.pack(byte_def, param_id)


# Note: not using can.Message because it's not available in MicroPython
def decode_message(arb_id: int, data: "bytes | bytearray") -> "NamedTuple":
    """Parse a message from raw data."""
    opcode = arb_id & 0x1F
    message_class = _OPCODE2MSG[opcode]
    if message_class == ParameterMessage:
        param_id = data[0]  # first byte is param_id
        dtype = params_byte_defs[param_id]
        value = struct.unpack(dtype, data[1:])[0]
        return ParameterMessage(param_id, value)

    return message_class(*struct.unpack(_MSG_DEFS[message_class][1], data))  # type: ignore
