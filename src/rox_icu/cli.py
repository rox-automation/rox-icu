#!/usr/bin/env python3
"""
rox_icu CLI
"""

import click
from rox_icu import __version__


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    pass  # pragma: no cover


@cli.command()
def info() -> None:
    """Print package info"""
    print(__version__)


cli.add_command(info)

if __name__ == "__main__":
    cli()  # pragma: no cover
