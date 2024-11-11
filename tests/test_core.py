import pytest

from rox_icu.core import Pin


def get_pin() -> Pin:
    return Pin(5)


def test_pin_initial_state():
    pin = get_pin()
    assert not pin.state
    assert pin.number == 5
    assert pin.on_high is not None
    assert pin.on_low is not None
    assert pin.on_change is not None


@pytest.mark.asyncio
async def test_pin_set_state():
    pin = get_pin()
    pin.state = True
    assert pin.state
    pin.state = False
    assert not pin.state


@pytest.mark.asyncio
async def test_on_high_event():
    pin = get_pin()
    assert not pin.state

    # both events should be cleared
    assert not pin.on_low.is_set()
    assert not pin.on_high.is_set()

    # set low, no events should be triggered
    pin.state = False
    assert not pin.on_low.is_set()
    assert not pin.on_high.is_set()

    # set high, on_high event should be triggered
    pin.state = True
    assert not pin.on_low.is_set()
    assert pin.on_high.is_set()

    # check auto-clearing
    await pin.on_high.wait()
    assert not pin.on_high.is_set()  # AutoClearEvent should be cleared


@pytest.mark.asyncio
async def test_on_low_event():
    pin = get_pin()

    # both events should be cleared
    assert not pin.on_low.is_set()
    assert not pin.on_high.is_set()

    # set high, on_high should be triggered
    pin.state = True
    assert not pin.on_low.is_set()
    assert pin.on_high.is_set()

    await pin.on_high.wait()
    assert not pin.on_high.is_set()

    # set low, on_low should be triggered
    pin.state = False
    assert pin.on_low.is_set()
    assert not pin.on_high.is_set()

    # check auto-clearing
    await pin.on_low.wait()
    assert not pin.on_low.is_set()
