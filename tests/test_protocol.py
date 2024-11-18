import struct

import pytest

from rox_icu import can_protocol as canp

EXPECTED_PROTOCOL_VERSION = 11


def test_version() -> None:
    assert canp.VERSION >= EXPECTED_PROTOCOL_VERSION


def test_split() -> None:
    message_id = 0x2C

    assert canp.split_message_id(message_id) == (0x01, 0x0C)


def test_node_id() -> None:
    for node_id in range(64):
        assert canp.get_node_id(canp.generate_message_id(node_id, 0)) == node_id


def test_roundtip() -> None:
    for endpoint in range(32):
        for node_id in range(64):
            message_id = canp.generate_message_id(node_id, endpoint)
            assert canp.split_message_id(message_id) == (node_id, endpoint)


def test_invalid_message() -> None:
    class InvalidMessage:
        pass

    with pytest.raises(KeyError):
        canp.get_opcode_and_bytedef(InvalidMessage)  # type: ignore


def test_halt() -> None:
    test_bytes = b"\x01"

    msg = canp.HaltMessage(1)
    assert msg.io_state == 1

    opcode, byte_def = canp.get_opcode_and_bytedef(canp.HaltMessage)
    assert opcode == 0
    assert byte_def == "<B"

    data_bytes = struct.pack(byte_def, *msg)

    assert data_bytes == test_bytes

    # use function
    arb_id, data_bytes = canp.encode_message(msg, 1)
    assert data_bytes == test_bytes

    # convert back
    msg2 = canp.HaltMessage(*struct.unpack(byte_def, test_bytes))

    assert msg == msg2


def test_heartbeat() -> None:
    test_bytes = b"\x01\x02\xbe\xef\xff"

    msg = canp.HeartbeatMessage(1, 2, 0xBE, 0xEF, 0xFF)
    assert msg.device_type == 1
    assert msg.io_dir == 2
    assert msg.io_state == 0xBE
    assert msg.errors == 0xEF
    assert msg.counter == 0xFF

    opcode, byte_def = canp.get_opcode_and_bytedef(canp.HeartbeatMessage)
    assert opcode == 1
    assert byte_def == "<BBBBB"

    data_bytes = struct.pack(byte_def, *msg)
    assert data_bytes == test_bytes

    # # convert back
    msg2 = canp.HeartbeatMessage(*struct.unpack(byte_def, test_bytes))

    assert msg == msg2

    # use function
    _, data_bytes = canp.encode_message(msg, 1)
    assert data_bytes == test_bytes


def test_pack_unpack() -> None:
    test_bytes = b"\x01\x02\xbe\xef\xff"

    msg = canp.HeartbeatMessage(1, 2, 0xBE, 0xEF, 0xFF)

    msg_id, data_bytes = canp.encode_message(msg, 1)

    assert data_bytes == test_bytes

    # convert back
    msg2 = canp.decode_message(msg_id, data_bytes)
    assert msg == msg2
