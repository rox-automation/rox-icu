#!/usr/bin/env python3
"""
rox_icu CLI
"""


from pathlib import Path
import os
import can
import click

import rox_icu.can_protocol as canp
from rox_icu import __version__
from rox_icu.can_utils import get_can_bus
from rox_icu.utils import run_main


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
@click.option("--channel", "-c", help="CAN bus name", default="vcan0")
def mock(
    node_id: int,
    channel: str,
):
    # set env variable for can bus
    os.environ["CAN_CHANNEL"] = channel

    import rox_icu.mock as mock

    run_main(lambda: mock.main(node_id))


@cli.command()
def monitor():
    """Monitor ICU devices on CAN bus"""
    import curses

    import rox_icu.monitor as icu_monitor

    curses.wrapper(icu_monitor.main)


@cli.command()
@click.argument("node_id", type=int)
@click.option("--channel", "-c", default="can0")
def inspect(node_id: int, channel: str) -> None:
    """Inspect ICU messages on CAN bus for a specific node"""
    from candbg import inspector

    from rox_icu.can_utils import create_dbc

    # note: tried to pass dbc object directly but for some reason that
    # does not work. Spent 1.5 hours trying to figure out why, but no luck.
    # So, for now, just create a temporary DBC file and use that.
    tmp_file = "/tmp/icu.dbc"

    create_dbc(node_id, filename=tmp_file)
    dbc_pth = Path(tmp_file)
    assert dbc_pth.exists(), f"Failed to create DBC file: {dbc_pth}"

    try:
        inspector.main(dbc_pth, channel=channel)
    except KeyboardInterrupt:
        pass


@cli.command()
@click.argument("node_id", type=int)
@click.argument("hex_input")
def output(node_id: int, hex_input: str) -> None:
    """Set output state, provide hex value"""
    try:
        state = int(hex_input, 16)

    except ValueError:
        print("Invalid hex input. Please provide a valid hexadecimal value.")
        return

    # for now, simply put packet on the bus, without checking if device is alive

    print(f"Setting ICU_{node_id} output state to {state:08b}")

    with get_can_bus() as bus:
        arb_id, data = canp.encode_message(canp.SetIoStateMessage(state), node_id)
        msg = can.Message(arbitration_id=arb_id, data=data, is_extended_id=False)
        bus.send(msg)


if __name__ == "__main__":
    cli()  # pragma: no cover
