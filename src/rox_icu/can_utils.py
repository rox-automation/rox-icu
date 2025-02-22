#!/usr/bin/env python3
"""
 supporting functions for working with can

 Copyright (c) 2024 ROX Automation - Jev Kuznetsov
"""

import os
from can.interfaces.udp_multicast import UdpMulticastBus
from can.interfaces.socketcan import SocketcanBus


def is_ci_environment() -> bool:
    """Check if the code is running in a CI environment"""
    return os.getenv("CI") == "true"


def get_can_bus(bus_type: str = "env") -> UdpMulticastBus | SocketcanBus:
    """Get a CAN bus instance"""

    match bus_type:
        case "udp_multicast":
            return UdpMulticastBus("224.0.0.1", interface="udp_multicast")

        case "env":

            channel = os.getenv("CAN_CHANNEL")
            if channel is None:
                raise ValueError(
                    "Missing CAN_CHANNEL environment variable, set to can0 or similar"
                )

            return SocketcanBus(
                channel=channel, interface="socketcan", receive_own_messages=False
            )

        case _:  # just use the bus_type as the channel

            return SocketcanBus(
                channel=bus_type, interface="socketcan", receive_own_messages=False
            )
