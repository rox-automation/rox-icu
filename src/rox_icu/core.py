#!/usr/bin/env python3
"""
Core pc driver for ROX ICU.

Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import time
import can_protocol as protocol


ICU_DEVICE_TYPE = 0x01


class DeviceDead(Exception):
    """No heartbeat error"""


class Timer:
    """Timer class, including timeout"""

    def __init__(self, timeout):
        self.timeout = timeout
        self.start_time = time.time()

    def is_timeout(self):
        """Check if timeout has expired"""
        return time.time() - self.start_time > self.timeout

    def reset(self):
        """Reset timer"""
        self.start_time = time.time()

    def elapsed(self):
        """Return elapsed time since timer was started"""
        return time.time() - self.start_time


class ICU:
    def __init__(self, address: int) -> None:
        self.address = address
        self.heartbeat: protocol.HeartbeatMessage | None = None
        self._timer = Timer(timeout=0.5)
