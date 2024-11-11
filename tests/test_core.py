import asyncio
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


@pytest.mark.asyncio
async def test_on_change() -> None:

    pin = get_pin()
    assert not pin.state

    async def toggle_state_loop(pin: Pin) -> None:
        """toggle state a couple of times"""

        for _ in range(10):
            pin.state = not pin.state
            await asyncio.sleep(0.001)

    async def on_change_counter() -> int:
        """count on_change events with a timeout"""
        count = 0
        try:
            while True:
                await asyncio.wait_for(pin.on_change.wait(), timeout=0.1)
                count += 1
        except asyncio.TimeoutError:
            pass

        return count

    # Run both coroutines concurrently
    counter_task = asyncio.create_task(on_change_counter())
    toggle_task = asyncio.create_task(toggle_state_loop(pin))

    # Wait for toggle_task to complete first
    await toggle_task

    # Then wait for counter_task (it will finish when timeout occurs)
    count = await counter_task

    # Since we toggled 10 times, we should have 10 changes
    assert count == 10
