import can_protocol as protocol
import struct


def test_heartbeat() -> None:
    opcode = 0
    test_bytes = b"\x01\x02\x00\x03\x00\x00\x00\x07"

    msg = protocol.HeartbeatMessage(1, 2, 3, 7)
    assert msg.error_code == 1
    assert msg.error_count == 2
    assert msg.uptime == 3
    assert msg.version == 7

    byte_def = protocol.MESSAGES[opcode][1]
    data_bytes = struct.pack(byte_def, *msg)

    assert protocol.pack(opcode, msg) == data_bytes

    assert data_bytes == test_bytes

    # # convert back
    msg2 = protocol.parse(opcode, test_bytes)

    assert msg == msg2


def test_opcode() -> None:
    assert protocol.get_opcode(protocol.HeartbeatMessage) == 0
