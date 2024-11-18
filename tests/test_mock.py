import asyncio
import json
import os
import aiomqtt
import pytest

from rox_icu.mock import ICUMock

NODE_ID = 10


@pytest.mark.skipif(os.getenv("CI") is not None, reason="Skipped in CI environment")
@pytest.mark.asyncio
async def test_mqtt_commands():

    mock = ICUMock(NODE_ID, simulate_inputs=False, mqtt_broker="localhost")

    asyncio.create_task(mock.main())

    assert mock.io_state == 0

    async with aiomqtt.Client("localhost") as mqtt:
        await asyncio.sleep(0.1)

        cmd_topic = f"{ICUMock.MQTT_BASE_TOPIC}/{NODE_ID}/cmd"
        msg = {"cmd": "set_pin", "args": {"pin": 0, "state": 1}}
        await mqtt.publish(cmd_topic, json.dumps(msg))
        await asyncio.sleep(0.1)
        assert mock.io_state == 0x01

        # set pin 2
        msg = {"cmd": "set_pin", "args": {"pin": 1, "state": 1}}
        await mqtt.publish(cmd_topic, json.dumps(msg))
        await asyncio.sleep(0.1)
        assert mock.io_state == 0x03
