# pylint: disable=protected-access
import asyncio
import pytest

from rox_icu.core import Pin


def get_pin() -> Pin:
    return Pin(5)


def test_pin_initial_state():
    pin = get_pin()
    assert not pin.state
    assert pin.number == 5
    assert pin.high_event is not None
    assert pin.low_event is not None
    assert pin.change_event is not None


@pytest.mark.asyncio
async def test_pin_set_state():
    pin = get_pin()
    pin._update(True)
    assert not pin.is_input
    assert pin.state
    pin._update(False)
    assert not pin.state


@pytest.mark.asyncio
async def test_on_high_event():
    pin = get_pin()
    assert not pin.state

    # both events should be cleared
    assert not pin.low_event.is_set()
    assert not pin.high_event.is_set()

    # set low, no events should be triggered
    pin._update(False)
    assert not pin.low_event.is_set()
    assert not pin.high_event.is_set()

    # set high, on_high event should be triggered
    pin._update(True)
    assert not pin.low_event.is_set()
    assert pin.high_event.is_set()

    # check auto-clearing
    await pin.high_event.wait()
    assert not pin.high_event.is_set()  # AutoClearEvent should be cleared


@pytest.mark.asyncio
async def test_on_low_event():
    pin = get_pin()

    # both events should be cleared
    assert not pin.low_event.is_set()
    assert not pin.high_event.is_set()

    # set high, on_high should be triggered
    pin._update(True)
    assert not pin.low_event.is_set()
    assert pin.high_event.is_set()

    await pin.high_event.wait()
    assert not pin.high_event.is_set()

    # set low, on_low should be triggered
    pin._update(False)
    assert pin.low_event.is_set()
    assert not pin.high_event.is_set()

    # check auto-clearing
    await pin.low_event.wait()
    assert not pin.low_event.is_set()


@pytest.mark.asyncio
async def test_on_change() -> None:

    pin = get_pin()
    assert not pin.state

    async def toggle_state_loop(pin: Pin) -> None:
        """toggle state a couple of times"""

        for _ in range(10):
            pin._update(not pin.state)
            await asyncio.sleep(0.001)

    async def on_change_counter() -> int:
        """count on_change events with a timeout"""
        count = 0
        try:
            while True:
                await asyncio.wait_for(pin.change_event.wait(), timeout=0.1)
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


# @pytest.mark.asyncio
# async def test_heartbeat() -> None:

#     node_id = 42
#     icu = ICU(node_id)

#     # no mock is running, so this should raise an error
#     with pytest.raises(HeartbeatError):
#         await icu.start()
