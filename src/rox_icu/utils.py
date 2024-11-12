#!/usr/bin/env python3
"""
Support functions

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import asyncio
import logging
import os
from typing import Any, Coroutine, Callable, Union, TypeVar

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


def get_root_exception(exc: BaseException) -> BaseException:
    """Traverse the exception chain to find the root cause."""
    if isinstance(exc, ExceptionGroup):
        # If it's an ExceptionGroup, recursively check its exceptions
        for e in exc.exceptions:
            return get_root_exception(e)
    while exc.__cause__ is not None:
        exc = exc.__cause__
    return exc


def run_main(func: Callable) -> None:
    setup_logging()

    try:
        func()
    except KeyboardInterrupt:
        logging.info("Process interrupted by user")
    except ExceptionGroup as group:
        root_exc = get_root_exception(group)
        logging.error(
            f"Root cause: {type(root_exc).__name__}: {str(root_exc)}",
            exc_info=True,
        )

    except Exception as e:
        logging.error(e, exc_info=True)


def run_main_async(
    coro: Coroutine[Any, Any, None],
    silence_loggers: list[str] | None = None,
) -> None:
    """convenience function to avoid code duplication"""

    setup_logging()

    if silence_loggers:
        for logger in silence_loggers:
            logging.info(f"Silencing logger: {logger}")
            logging.getLogger(logger).setLevel(logging.WARNING)

    try:
        asyncio.run(coro)
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
    except ExceptionGroup as group:
        root_exc = get_root_exception(group)
        logging.error(
            f"Root cause: {type(root_exc).__name__}: {str(root_exc)}", exc_info=True
        )
    except asyncio.CancelledError:
        logging.error("Cancelled")
    except Exception as e:
        root_exc = get_root_exception(e)
        logging.error(
            f"Root cause: {type(root_exc).__name__}: {str(root_exc)}", exc_info=True
        )
