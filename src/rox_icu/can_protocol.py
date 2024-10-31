#!/usr/bin/env python3
"""
ROX CAN Protocol Implementation

A lightweight CAN (Controller Area Network) protocol implementation for ROX devices,
compatible with both CPython and MicroPython for embedded systems use.

Message Format
-------------
- Message ID: 11 bits split into:
  - Node ID: Upper 6 bits (0-63, node 0 reserved for broadcast)
  - Command ID: Lower 5 bits (0-31)

Message Types
------------
- HaltMessage: Emergency halt command with IO state
- HeartbeatMessage: Periodic status update (100ms interval)
- IOStateMessage: IO state change notification

Adding New Messages
-----------------
1. Define a new namedtuple for the message
2. Add entry to MSG_DEFS with (opcode, byte_definition)
3. Byte definition uses struct format chars (B=uint8, H=uint16, etc.)

Example
-------
>>> msg_id = generate_message_id(node_id=1, opcode=2)
>>> node_id, opcode = split_message_id(msg_id)

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

try:
    from typing import Type, NamedTuple, Tuple
except ImportError:  # pragma: no cover
    pass

import struct
from collections import namedtuple

VERSION = 8


class DeviceState:
    """Device state flags"""

    RUNNING = 0
    STOPPED = 1


# ----------------------------Message Definitions----------------------------
# opcode 0
HaltMessage = namedtuple("HaltMessage", "io_state")  # halt with desired io state.


# opcode 1, normally sent every 100ms
HeartbeatMessage = namedtuple(
    "HeartbeatMessage",
    ("device_type", "error_max1", "error_max2", "io_state", "device_state", "counter"),
)

# opcode 2, sent on change or request
IOStateMessage = namedtuple("IOStateMessage", "io_state")

# message: (opcode, byte_def)
_MSG_DEFS = {
    HaltMessage: (0, "<B"),
    HeartbeatMessage: (1, "<BBBBBB"),
    IOStateMessage: (2, "<B"),
}

_OPCODE2MSG = {v[0]: k for k, v in _MSG_DEFS.items()}


# ----------------------------Utility Functions----------------------------
def generate_message_id(node_id: int, opcode: int) -> int:
    """Generates an 11-bit message ID from opcode and node ID."""
    return (node_id << 5) | opcode


def split_message_id(message_id: int) -> Tuple[int, int]:
    """Splits a 11-bit message ID into opcode and node ID."""

    # same as odrive 3.6
    opcode = message_id & 0x1F  # Extract lower 5 bits for cmd_id
    node_id = message_id >> 5  # Shift right by 5 bits to get node_id

    return node_id, opcode


def get_opcode_and_bytedef(message_class: Type[NamedTuple]) -> Tuple[int, str]:  # type:ignore
    """Get the opcode for a message type."""
    return _MSG_DEFS[message_class]  # type:ignore


def pack_message(message: NamedTuple, node_id: int) -> Tuple[int, bytes]:  # type:ignore
    """Pack a message into arbitration ID and data bytes.
    returns: (arbitration_id, data_bytes)"""
    opcode, byte_def = get_opcode_and_bytedef(type(message))
    arbitration_id = generate_message_id(node_id, opcode)
    return arbitration_id, struct.pack(byte_def, *message)


def parse_message(msg_id: int, data: bytes) -> NamedTuple:
    """Parse a message from raw data."""
    opcode = msg_id & 0x1F
    message_class = _OPCODE2MSG[opcode]
    return message_class(*struct.unpack(_MSG_DEFS[message_class][1], data))


if __name__ == "__main__":  # pragma: no cover
    # simple tests
    print("ROX CAN Protocol v", VERSION)
    node_id = 1

    msg = HeartbeatMessage(1, 2, 3, 4, 5, 6)
    print("Heartbeat message:", msg)

    msg_id, data = pack_message(msg, node_id)
    msg2 = parse_message(msg_id, data)

    assert msg2 == msg
