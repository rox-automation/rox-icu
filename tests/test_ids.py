from can_protocol import generate_message_id, split_message_id


def test_split() -> None:
    message_id = 0x2C

    assert split_message_id(message_id) == (0x0C, 0x01)


def test_roundtip() -> None:
    for endpoint in range(32):
        for node_id in range(64):
            message_id = generate_message_id(endpoint, node_id)
            assert split_message_id(message_id) == (endpoint, node_id)
