import can_protocol as protocol


def test_heartbeat() -> None:
    node_id = 10
    test_bytes = b"\x01\x02\x00\x03\x00\x00\x00\x07"

    msg = protocol.HeartbeatMessage(node_id, 1, 2, 3, 7)
    assert msg.node_id == node_id
    assert msg.error_code == 1
    assert msg.error_count == 2
    assert msg.uptime == 3
    assert msg.version == 7

    message_id, data_bytes = msg.pack()

    assert data_bytes == test_bytes

    assert message_id == protocol.generate_message_id(msg.opcode, node_id)

    # # convert back
    msg2 = protocol.parse(message_id, test_bytes)

    for key in msg.__slots__:
        assert getattr(msg, key) == getattr(msg2, key)
