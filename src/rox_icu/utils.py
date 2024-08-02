#!/usr/bin/env python3
"""
Support functions

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import asyncio
import logging
import os
from typing import Any, Coroutine

import coloredlogs

LOG_FORMAT = "%(asctime)s [%(name)s] %(filename)s:%(lineno)d - %(message)s"
TIME_FORMAT = "%H:%M:%S.%f"


def run_main_async(coro: Coroutine[Any, Any, None]) -> None:
    """convenience function to avoid code duplication"""
    loglevel = os.environ.get("LOGLEVEL", "INFO").upper()
    coloredlogs.install(level=loglevel, fmt=LOG_FORMAT, datefmt=TIME_FORMAT)
    logging.info(f"Log level set to {loglevel}")

    try:
        asyncio.run(coro)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.error(e)
