import can_protocol as protocol
import struct
import pytest


def test_version() -> None:
    assert protocol.VERSION == 7


def test_invalid_message() -> None:
    class InvalidMessage:
        pass

    with pytest.raises(ValueError):
        protocol.get_opcode_and_bytedef(InvalidMessage)


def test_halt() -> None:
    test_bytes = b"\x01"

    msg = protocol.HaltMessage(1)
    assert msg.io_state == 1

    opcode, byte_def = protocol.get_opcode_and_bytedef(protocol.HaltMessage)
    assert opcode == 0
    assert byte_def == "<B"

    data_bytes = struct.pack(byte_def, *msg)

    assert data_bytes == test_bytes

    # convert back
    msg2 = protocol.HaltMessage(*struct.unpack(byte_def, test_bytes))

    assert msg == msg2


def test_heartbeat() -> None:
    test_bytes = b"\x01\x02\x03\xbe\xef\xff"

    msg = protocol.HeartbeatMessage(1, 2, 3, 0xBE, 0xEF, 0xFF)
    assert msg.device_type == 1
    assert msg.error_max1 == 2
    assert msg.error_max2 == 3
    assert msg.io_state == 0xBE
    assert msg.device_state == 0xEF
    assert msg.counter == 0xFF

    opcode, byte_def = protocol.get_opcode_and_bytedef(protocol.HeartbeatMessage)
    assert opcode == 1
    assert byte_def == "<BBBBBB"

    data_bytes = struct.pack(byte_def, *msg)

    assert data_bytes == test_bytes

    # # convert back
    msg2 = protocol.HeartbeatMessage(*struct.unpack(byte_def, test_bytes))

    assert msg == msg2
