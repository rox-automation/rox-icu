import sys

if sys.implementation.name == "cpython":
    print("Running on CPython - using mocks")

    # Inject into sys.modules so regular imports work
    # sys.modules["microcontroller"] = microcontroller
    # sys.modules["digitalio"] = digitalio
    from rox_icu.firmware.mocks import canio

    sys.modules["canio"] = canio
