from can_protocol import generate_message_id, split_message_id


def test_generate_message_id() -> None:
    # Test valid inputs
    assert generate_message_id(0, 0) == 0
    assert generate_message_id(15, 127) == 0x7FF
    assert generate_message_id(1, 5) == 0x085


def test_split_message_id() -> None:
    # Test valid inputs
    assert split_message_id(0) == (0, 0)
    assert split_message_id(0x7FF) == (15, 127)
    assert split_message_id(0x085) == (1, 5)

    # Test split and generate are inverse operations
    endpoint, node_id = 1, 5
    message_id = generate_message_id(endpoint, node_id)
    assert split_message_id(message_id) == (endpoint, node_id)


def test_roundtip() -> None:
    for endpoint in range(16):
        for node_id in range(128):
            message_id = generate_message_id(endpoint, node_id)
            assert split_message_id(message_id) == (endpoint, node_id)
