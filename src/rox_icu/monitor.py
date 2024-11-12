#!/usr/bin/env python3
"""
monitor devices on can bus.
Listens to heartbeat, displays status in curses.

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

from __future__ import annotations

import curses
import signal
import struct
from dataclasses import dataclass

import can

from rox_icu import can_protocol as canp
from rox_icu.can_utils import get_can_bus


HB_OPCODE, HB_BYTEDEF = canp.get_opcode_and_bytedef(canp.HeartbeatMessage)

devices: dict[int, Device] = {}
should_exit = False


@dataclass
class Device:
    node_id: int
    is_icu: bool = False
    last_heartbeat: canp.HeartbeatMessage | None = None

    def get_display_data(self) -> tuple:
        """Get tuple of display values, handling unknown devices and message changes"""
        if not self.is_icu or self.last_heartbeat is None:
            return (self.node_id, "--", "--", "--", "--", "--", "--")

        hb = self.last_heartbeat
        # Convert io_state to binary string, pad to 8 bits
        io_state_bin = format(hb.io_state, "08b")

        # Use getattr with default to handle possible changes in heartbeat message
        return (
            self.node_id,
            getattr(hb, "device_type", "--"),
            getattr(hb, "error_max1", "--"),
            getattr(hb, "error_max2", "--"),
            io_state_bin,
            getattr(hb, "errors", "--"),
            getattr(hb, "counter", "--"),
        )


def handle_msg(msg: can.Message) -> None:
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


def signal_handler(signum, frame) -> None:
    """Handle keyboard interrupt"""
    global should_exit  # pylint: disable=global-statement
    should_exit = True


def draw_table(pad: curses.window, screen: curses.window) -> None:
    """Draw the table using a pad"""
    height, width = screen.getmaxyx()
    pad.erase()

    # Draw header
    header = f"| {'NodeID':<6} | {'DeviceType':<10} | {'ErrorMax1':<9} | {'ErrorMax2':<9} | {'IO State':<10} | {'Errors':<11} | {'Counter':<7} |"
    pad.addstr(0, 0, header)
    pad.addstr(1, 0, "-" * len(header))

    # Draw data
    for idx, (_, device) in enumerate(sorted(devices.items()), start=2):
        # Get display values
        (
            node_id,
            dev_type,
            err1,
            err2,
            io_state,
            dev_state,
            counter,
        ) = device.get_display_data()

        row = f"| {node_id:<6} | {dev_type:<10} | {err1:<9} | {err2:<9} | {io_state:<10} | {dev_state:<11} | {counter:<7} |"
        pad.addstr(idx, 0, row)

    # Calculate visible area
    visible_rows = height - 1
    visible_cols = width - 1

    # Copy the pad contents to the screen
    pad.refresh(0, 0, 0, 0, visible_rows, visible_cols)


def main(stdscr: curses.window) -> None:
    # Set up curses
    curses.curs_set(0)  # Hide the cursor
    curses.use_default_colors()  # Use terminal's default colors

    # Create a pad larger than the screen
    _, width = stdscr.getmaxyx()
    pad = curses.newpad(1000, width)  # Support up to 1000 rows

    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    try:
        with get_can_bus() as bus:
            while not should_exit:
                # Check for messages
                msg = bus.recv(timeout=0.1)  # 100ms timeout
                if msg is not None:
                    handle_msg(msg)

                # Update display
                draw_table(pad, stdscr)

    except Exception as e:
        curses.endwin()
        print(f"Error: {e}")


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        print("\nExiting gracefully...")
