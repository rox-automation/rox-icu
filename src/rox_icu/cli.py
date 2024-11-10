#!/usr/bin/env python3
"""
rox_icu CLI
"""

import can
import click
from rox_icu import __version__
from rox_icu.utils import run_main
import rox_icu.can_protocol as canp


DEFAULT_INTERFACE = "slcan0"


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    pass  # pragma: no cover


@cli.command()
def info() -> None:
    """Print package info"""
    print(__version__)


@cli.command()
@click.option("--node-id", default=1, help="device ID")
@click.option("--interface", default=DEFAULT_INTERFACE, help="CAN interface")
def mock(node_id, interface):
    """Mock ICU device on CAN bus"""
    from .mock import main

    run_main(lambda: main(node_id=node_id, interface=interface))


@cli.command()
@click.option("--interface", default=DEFAULT_INTERFACE, help="CAN interface")
def monitor(interface):
    """Monitor ICU devices on CAN bus"""
    import curses
    import rox_icu.monitor as monitor

    monitor.INTERFACE = interface

    curses.wrapper(monitor.main)


@cli.command()
@click.argument("hex_input")
@click.option("--node-id", default=1, help="device ID")
@click.option("--interface", default=DEFAULT_INTERFACE, help="CAN interface")
def output(hex_input: str, node_id: int, interface: str):
    """Set output state, provide hex value"""
    try:
        state = int(hex_input, 16)

    except ValueError:
        print("Invalid hex input. Please provide a valid hexadecimal value.")
        return

    # for now, simply put packet on the bus, without checking if device is alive

    print(f"Setting ICU_{node_id} on {interface} output state to {state:08b}")

    with can.interface.Bus(channel=interface, bustype="socketcan") as bus:
        arb_id, data = canp.encode_message(canp.IOStateMessage(state), node_id)
        msg = can.Message(arbitration_id=arb_id, data=data)
        bus.send(msg)


if __name__ == "__main__":
    cli()  # pragma: no cover
