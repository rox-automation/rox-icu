#!/usr/bin/env python3
"""
 supporting functions for working with can

 Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import os
from can.interfaces.udp_multicast import UdpMulticastBus
from can.interfaces.socketcan import SocketcanBus


def get_can_bus() -> UdpMulticastBus | SocketcanBus:
    """Get a CAN bus instance, using environment variables
    CAN_CHANNEL and CAN_INTERFACE for configuration"""

    channel = os.getenv("CAN_CHANNEL")
    if channel is None:
        raise ValueError(
            "Missing CAN_CHANNEL environment variable, set to can0 or similar"
        )

    interface = os.getenv("CAN_INTERFACE", "socketcan")

    if interface == "udp_multicast":
        return UdpMulticastBus(channel, interface=interface, receive_own_messages=False)
    else:
        return SocketcanBus(
            channel=channel, interface=interface, receive_own_messages=False
        )
