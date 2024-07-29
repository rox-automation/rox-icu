import can_protocol as protocol
import struct


def test_heartbeat() -> None:
    opcode = 0
    test_bytes = b"\x01\x02\x03\x04"

    msg = protocol.HeartbeatMessage(1, 2, 3, 4)
    assert msg.error_code == 2
    assert msg.device_type == 1
    assert msg.counter == 3
    assert msg.io_state == 4

    byte_def = protocol.MESSAGES[opcode][1]
    data_bytes = struct.pack(byte_def, *msg)

    assert protocol.pack(opcode, msg) == data_bytes

    assert data_bytes == test_bytes

    # # convert back
    msg2 = protocol.unpack(opcode, test_bytes)

    assert msg == msg2


def test_opcode() -> None:
    assert protocol.get_opcode(protocol.HeartbeatMessage) == 0
