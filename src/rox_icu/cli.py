#!/usr/bin/env python3
"""
rox_icu CLI
"""

import click
from rox_icu import __version__
from .utils import run_main


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
@click.option("--interface", default="vcan0", help="CAN interface")
def mock(node_id, interface):
    """Mock ICU device on CAN bus"""
    from .mock import main

    run_main(lambda: main(node_id=node_id, interface=interface))


@cli.command()
@click.option("--interface", default="vcan0", help="CAN interface")
def monitor(interface):
    """Monitor ICU devices on CAN bus"""
    import curses
    import rox_icu.monitor as monitor

    monitor.INTERFACE = interface

    curses.wrapper(monitor.main)


if __name__ == "__main__":
    cli()  # pragma: no cover
