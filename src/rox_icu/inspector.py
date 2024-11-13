#!/usr/bin/env python3
"""
 Inspect icu messages on can bus

 Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""
import struct

import can

import rox_icu.can_protocol as canp
from rox_icu.can_utils import get_can_bus
from rox_icu.utils import run_main


def process_message(msg: can.Message):

    node_id, opcode = canp.split_message_id(msg.arbitration_id)
    try:
        decoded = canp.decode_message(msg.arbitration_id, msg.data)
        if isinstance(decoded, canp.HeartbeatMessage):
            print(".", end="", flush=True)
        else:
            print(f"\n{node_id=}, {opcode=}, {decoded}")
    except (KeyError, struct.error):
        pass


def main():

    print("Starting inspector")
    with get_can_bus() as bus:
        try:
            while True:
                msg = bus.recv()
                if msg is not None:
                    process_message(msg)

        except KeyboardInterrupt:
            print("Inspector stopped")


if __name__ == "__main__":
    run_main(main)
