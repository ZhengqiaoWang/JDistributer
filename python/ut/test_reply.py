import sys, os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import time
import asyncio
import pytest
from config import g_redis_settings
from JDistributer import (
    ReplyProducer,
    ReplyConsumer,
    Message,
    MessageDetail,
    MessageConsumeStatus,
    ResponseStatus,
    CustomMessage,
    ProduceStatus,
    ConsumeStatus,
)

flag_consume_num1 = 0
flag_consume_num2 = 0


@pytest.mark.asyncio
async def test_reply_producer_reply_consumer_success():
    global flag_consume_num1
    topic_name = "reply_success"

    def cb_func(message: Message) -> ResponseStatus:
        assert message.custom_msg.body == "abc"
        return ResponseStatus(is_ok=True)

    def cb_func_success(msg_detail: MessageDetail) -> None:
        assert msg_detail.msg.custom_msg.body == "abc"
        assert msg_detail.msg.custom_msg.expect_consume_num == 1
        assert msg_detail.msg.msg_meta.topic == topic_name

        global flag_consume_num1
        flag_consume_num1 += 1

    def cb_func_failed(msg_detail: MessageDetail, consume_status: MessageConsumeStatus):
        assert msg_detail.msg.custom_msg.body == "abc"
        assert msg_detail.msg.custom_msg.expect_consume_num == 1
        assert msg_detail.msg.msg_meta.topic == topic_name

        global flag_consume_num1
        flag_consume_num1 += 1

    c1 = ReplyConsumer(g_redis_settings, topic_name, cb_func)
    c1.start()
    c2 = ReplyConsumer(g_redis_settings, topic_name, cb_func)
    c2.start()

    p = ReplyProducer(g_redis_settings, topic_name)
    p.start()
    ret = await p.async_product(
        CustomMessage(body="abc", expect_consume_num=1),
        on_success_func=cb_func_success,
        on_failed_func=cb_func_failed,
    )

    for i in range(3):
        if flag_consume_num1 == 1:
            assert ret.msg_status_statistic.produce_status == ProduceStatus.SUCCESS
            break
        print(flag_consume_num1, ret)
        time.sleep(1)

    assert flag_consume_num1 == 1

    print(ret)

    p.release()
    c1.release()
    c2.release()


@pytest.mark.asyncio
async def test_reply_producer_reply_consumer_failed():
    global flag_consume_num2
    topic_name = "reply_failed"

    def cb_func(message: Message) -> ResponseStatus:
        assert message.custom_msg.body == "abc"
        return ResponseStatus(is_ok=False, response_msg="error")

    def cb_func_success(msg_detail: MessageDetail) -> None:
        assert msg_detail.msg.custom_msg.body == "abc"
        assert msg_detail.msg.custom_msg.expect_consume_num == 1
        assert msg_detail.msg.msg_meta.topic == topic_name

        global flag_consume_num2
        flag_consume_num2 += 1

    def cb_func_failed(msg_detail: MessageDetail, consume_status: MessageConsumeStatus):
        assert msg_detail.msg.custom_msg.body == "abc"
        assert msg_detail.msg.custom_msg.expect_consume_num == 1
        assert msg_detail.msg.msg_meta.topic == topic_name

        assert consume_status.consume_status == ConsumeStatus.FAILED

        global flag_consume_num2
        flag_consume_num2 += 1

    c1 = ReplyConsumer(g_redis_settings, topic_name, cb_func)
    c1.start()
    c2 = ReplyConsumer(g_redis_settings, topic_name, cb_func)
    c2.start()

    p = ReplyProducer(g_redis_settings, topic_name)
    p.start()
    ret = await p.async_product(
        CustomMessage(body="abc", expect_consume_num=1),
        on_success_func=cb_func_success,
        on_failed_func=cb_func_failed,
    )

    for i in range(3):
        print(flag_consume_num2, ret)
        if flag_consume_num2 == 1:
            assert ret.msg_status_statistic.produce_status == ProduceStatus.FAILED
            break
        time.sleep(1)

    assert flag_consume_num2 == 1

    print(ret)

    p.release()
    c1.release()
    c2.release()
