#!/usr/bin/env python3
"""
 supporting functions for working with can

 Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import os
import logging
from can.interfaces.udp_multicast import UdpMulticastBus
from can.interfaces.socketcan import SocketcanBus


def is_ci_environment() -> bool:
    """Check if the code is running in a CI environment"""
    return os.getenv("CI") == "true"


def get_can_bus() -> UdpMulticastBus | SocketcanBus:
    """Get a CAN bus instance, using environment variables
    ICU_CAN_CHANNEL and ICU_CAN_INTERFACE for configuration or a multicast bus in CI"""

    if is_ci_environment():
        return UdpMulticastBus("224.0.0.1", interface="udp_multicast")

    channel = os.getenv("ICU_CAN_CHANNEL")
    if channel is None:
        raise ValueError(
            "Missing ICU_CAN_CHANNEL environment variable, set to can0 or similar"
        )

    interface = os.getenv("ICU_CAN_INTERFACE", "socketcan")
    logging.info(f"Using CAN interface: {interface}, channel: {channel}")
    if interface == "udp_multicast":
        # note: will always receive own messages
        return UdpMulticastBus(channel, interface=interface)

    return SocketcanBus(
        channel=channel, interface=interface, receive_own_messages=False
    )
