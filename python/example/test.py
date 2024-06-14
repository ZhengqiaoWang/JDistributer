from JDistributer import *
import asyncio
import time
import logging

logger = logging.getLogger("JDistributer")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("[%(asctime)s][%(levelname)s][%(name)s] %(message)s")
console_sink = logging.StreamHandler()
console_sink.setLevel(logger.level)
console_sink.setFormatter(formatter)
logger.addHandler(console_sink)


def call_back_success_func(msg_detail: MessageDetail) -> None:
    logger.info("!! call_back_success_func {}".format(msg_detail))
    pass


def call_back_failed_func(
    msg_detail: MessageDetail, consume_status: MessageConsumeStatus
):
    logger.info("!! call_back_failed_func {} {}".format(msg_detail, consume_status))
    pass


def call_back_consume_func_c1(message: Message) -> ResponseStatus:
    logger.info("!! c1 consumer func, sleep 1 {}".format(message))
    time.sleep(1)
    return ResponseStatus(is_ok=True)


def call_back_consume_func_c2(message: Message) -> ResponseStatus:
    logger.info("!! c2 consumer func, sleep 3 {}".format(message))
    time.sleep(3)
    return ResponseStatus(is_ok=True)


async def main():
    c1 = ReplyConsumer(
        RedisSettings(host="localhost", port=6379, password=""),
        topic_name="abc",
        consumer_name="c1",
        on_req_func=call_back_consume_func_c1,
    )
    c2 = ReplyConsumer(
        RedisSettings(host="localhost", port=6379, password=""),
        topic_name="abc",
        consumer_name="c2",
        on_req_func=call_back_consume_func_c2,
    )
    c1.start()
    c2.start()

    p = ReplyProducer(
        RedisSettings(host="localhost", port=6379, password=""), topic_name="abc"
    )
    p.start()
    status = await p.async_product(
        CustomMessage(body="helloworld", expect_consume_num=2),
        on_success_func=call_back_success_func,
        on_failed_func=call_back_failed_func,
    )
    logger.info("! produce: {}".format(status))
    for i in range(10):
        logger.info("{}    produce: {}".format(i, status))
        time.sleep(1)

    p.release()
    c1.release()
    c2.release()
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
