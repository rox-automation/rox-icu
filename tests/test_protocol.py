import can_protocol as protocol
import struct


def test_version() -> None:
    assert protocol.VERSION == 6


def test_heartbeat() -> None:
    test_bytes = b"\x01\x02\x03\xbe\xef"

    msg = protocol.HeartbeatMessage(1, 2, 3, 0xBE, 0xEF)
    assert msg.device_type == 1
    assert msg.error_max1 == 2
    assert msg.error_max2 == 3
    assert msg.io_state == 0xBE
    assert msg.counter == 0xEF

    opcode, byte_def = protocol.get_opcode_and_bytedef(protocol.HeartbeatMessage)
    assert opcode == 1
    assert byte_def == "<BBBBB"

    data_bytes = struct.pack(byte_def, *msg)

    assert data_bytes == test_bytes

    # # convert back
    msg2 = protocol.HeartbeatMessage(*struct.unpack(byte_def, test_bytes))

    assert msg == msg2
