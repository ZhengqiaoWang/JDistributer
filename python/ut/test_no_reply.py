import sys, os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import asyncio
import pytest
from config import g_redis_settings
from JDistributer import (
    NoReplyProducer,
    NoReplyConsumer,
    Message,
    ResponseStatus,
    CustomMessage,
)

@pytest.mark.asyncio
async def test_no_reply_producer_no_reply_consumer_success():
    topic_name = "no_reply"

    def cb_func(message: Message) -> ResponseStatus:
        assert message.custom_msg.body == "abc"
        return ResponseStatus(is_ok=True)

    c = NoReplyConsumer(g_redis_settings, topic_name, cb_func)
    c.start()

    p = NoReplyProducer(g_redis_settings, topic_name)
    ret = await p.async_product(CustomMessage(body="abc"))
    print(ret)

    c.release()

@pytest.mark.asyncio
async def test_no_reply_producer_no_reply_consumer_failed():
    topic_name = "no_reply"

    def cb_func(message: Message) -> ResponseStatus:
        assert message.custom_msg.body == "abc"
        return ResponseStatus(is_ok=False, response_msg="error")

    c = NoReplyConsumer(g_redis_settings, topic_name, cb_func)
    c.start()

    p = NoReplyProducer(g_redis_settings, topic_name)
    ret = await p.async_product(CustomMessage(body="abc"))
    print(ret)

    c.release()
