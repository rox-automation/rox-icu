import sys


def mock_hardware() -> None:
    print("Running on CPython - using mocks")

    # Inject into sys.modules so regular imports work
    from rox_icu.firmware.mocks import canio, icu_board, digitalio, gc, micropython
    from rox_icu import can_protocol, bit_ops

    sys.modules["gc"] = gc
    sys.modules["icu_board"] = icu_board
    sys.modules["digitalio"] = digitalio
    sys.modules["canio"] = canio
    sys.modules["micropython"] = micropython
    sys.modules["can_protocol"] = can_protocol
    sys.modules["bit_ops"] = bit_ops
