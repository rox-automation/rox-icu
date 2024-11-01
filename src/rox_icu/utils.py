#!/usr/bin/env python3
"""
Support functions

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import asyncio
import logging
import os
from typing import Any, Coroutine, Callable, Union, TypeVar, cast

import coloredlogs

LOG_FORMAT = "%(asctime)s [%(name)s] %(filename)s:%(lineno)d - %(message)s"
TIME_FORMAT = "%H:%M:%S.%f"

# Type variable for the return type of the callable/coroutine
T = TypeVar("T")

# Define a type alias for our supported function types
MainFunction = Union[
    Callable[[], T],  # Regular synchronous function
    Coroutine[Any, Any, T],  # Coroutine
]


def setup_logging() -> None:
    """Setup logging"""
    loglevel = os.environ.get("LOGLEVEL", "INFO").upper()
    coloredlogs.install(level=loglevel, fmt=LOG_FORMAT, datefmt=TIME_FORMAT)
    logging.info(f"Log level set to {loglevel}")


def run_main(func: MainFunction[T]) -> T:
    """
    Convenience function to run either an async coroutine or a regular callable.

    Args:
        func: Either a coroutine or a regular callable to execute

    Returns:
        The return value of the executed function

    Raises:
        Exception: Any exception that occurs during execution (except KeyboardInterrupt)
    """
    setup_logging()

    try:
        if asyncio.iscoroutine(func):
            # If it's a coroutine, run it with asyncio
            return cast(T, asyncio.run(func))
        else:
            # If it's a regular callable, just call it
            return cast(Callable[[], T], func)()
    except KeyboardInterrupt:
        logging.info("Process interrupted by user")
        return cast(T, None)
    except Exception as e:
        logging.error(e)
        raise
