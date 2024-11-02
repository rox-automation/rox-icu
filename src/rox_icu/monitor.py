#!/usr/bin/env python3
"""
monitor devices on can bus.
Listens to heartbeat, displays status in curses.

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

from __future__ import annotations
import os
import can
import struct
from dataclasses import dataclass
from rox_icu import can_protocol as canp
from rox_icu.utils import run_main

INTERFACE = os.getenv("ICU_INTERFACE", "vcan0")

HB_OPCODE, HB_BYTEDEF = canp.get_opcode_and_bytedef(canp.HeartbeatMessage)

devices: dict[int, Device] = {}


@dataclass
class Device:
    node_id: int
    is_icu: bool = False
    last_heartbeat: canp.HeartbeatMessage | None = None

    def __repr__(self):
        if self.is_icu:
            return f"ICU [{self.node_id}]: {self.last_heartbeat}"
        else:
            return f"[{self.node_id}] Unknown device"


def handle_msg(msg: can.Message):
    # check if the message is a heartbeat
    node_id, opcode = canp.split_message_id(msg.arbitration_id)

    if opcode == HB_OPCODE:
        try:
            hb_msg = canp.decode_message(msg.arbitration_id, msg.data)
            if not isinstance(hb_msg, canp.HeartbeatMessage):
                raise ValueError("Invalid heartbeat message")
            if node_id not in devices:
                devices[node_id] = Device(node_id, is_icu=True, last_heartbeat=hb_msg)
            else:
                devices[node_id].last_heartbeat = hb_msg
        except struct.error:  # wrong number of bytes
            if node_id not in devices:
                devices[node_id] = Device(node_id, is_icu=False)


def print_devices():
    print("Devices:")
    for node_id, device in devices.items():
        print(f"Node {node_id}: {device}")


def main():
    with can.Bus(channel=INTERFACE, bustype="socketcan") as bus:
        for msg in bus:
            handle_msg(msg)
            print_devices()


if __name__ == "__main__":
    run_main(main, trace_on_exc=True)
