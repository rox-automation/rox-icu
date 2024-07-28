# type: ignore

import pytest
from unittest.mock import MagicMock
import sys


class CAN:
    def __init__(self, *args, **kwargs):
        self.sent_message = None

    @property
    def state(self):
        return "ERROR_ACTIVE"

    def send(self, message):
        self.sent_message = message


class Message:
    is_mock = True

    def __init__(self, id: int, data: bytes):
        self.id = id
        self.data = data


# A fixture that runs once per test session
@pytest.fixture(scope="session", autouse=True)
def mock_hardware_modules():
    # Mock the hardware-specific modules
    board_mock = MagicMock()
    board_mock.CAN_RX = "CAN_RX"
    board_mock.CAN_TX = "CAN_TX"
    sys.modules["board"] = board_mock

    sys.modules["digitalio"] = MagicMock()

    canio = MagicMock()
    canio.Message = Message
    canio.CAN = CAN
    sys.modules["canio"] = canio

    # Optional: Cleanup after the test session is done
    yield  # This allows the test session to run with the mocks in place

    # cleanup
    del sys.modules["board"]
    del sys.modules["digitalio"]
    del sys.modules["canio"]
