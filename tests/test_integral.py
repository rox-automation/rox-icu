# test ICU class with a mock device

import asyncio

import pytest

from rox_icu.core import ICU
from rox_icu.mock import ICUMockCAN

NODE_ID = 42


@pytest.mark.asyncio
async def test_loopback():
    """set a pin on the mock and await for the event on the ICU"""

    mock = ICUMockCAN(NODE_ID)
    mock_task = asyncio.create_task(mock.main())

    icu = ICU(NODE_ID)
    assert icu.node_id == NODE_ID
    await icu.start()

    icu.check_alive()
    pin = icu.pins[0]
    pin.state = True  # set command over can bus

    await asyncio.wait_for(pin.high_event.wait(), timeout=1.0)
    assert not pin.high_event.is_set()

    # stop the mock
    try:
        mock_task.cancel()
        await mock_task
    except asyncio.CancelledError:
        pass

    await icu.stop()
