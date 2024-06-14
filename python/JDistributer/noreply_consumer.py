from dataclasses import dataclass, asdict
import json
import random
import socket
import datetime
import logging
from JDistributer.adapter.mq.redis_adapter import (
    RedisConsumerAdapter,
    RedisSettings,
)
from JDistributer.common_define import (
    NodeInfo,
    dict_2_message,
    TOPIC_TEMPLATE_REQ,
    MessageConsumeStatus,
    ConsumeStatus,
    OnConsumerRequestReceiveFuncTemplate,
)


logger = logging.getLogger("JDistributer")


@dataclass
class NoReplyConsumerClientStruct:
    req_consumer: RedisConsumerAdapter


# 无回复消费者
class NoReplyConsumer:

    def __init__(
        self,
        redis_settings: RedisSettings,
        topic_name: str,
        on_req_func: OnConsumerRequestReceiveFuncTemplate,
        consumer_name: str = "default_consumer",
    ) -> None:
        self._consumer_node = NodeInfo(
            name="{}-{}-{}".format(
                consumer_name,
                int(datetime.datetime.now().timestamp()),
                random.randint(0, 100),
            ),
            host=socket.gethostname(),
        )
        self._consumer_client_struct = NoReplyConsumerClientStruct(
            req_consumer=RedisConsumerAdapter(),
        )
        self._topic_name = topic_name
        self._on_req_func = on_req_func

        # 注册topic到监听
        self._consumer_client_struct.req_consumer.init_topic(
            topic_name=TOPIC_TEMPLATE_REQ.format(topic_name)
        )

        # 初始化
        self._consumer_client_struct.req_consumer.init_client(
            redis_settings.host, redis_settings.port, redis_settings.password
        )

        self._consumer_client_struct.req_consumer.init_cb_func(self._on_req_receive)

    def start(self):
        self._consumer_client_struct.req_consumer.start()

    def release(self) -> None:
        # 取消监听注册
        self._consumer_client_struct.req_consumer.stop()

    def _on_req_receive(self, resp_str: str):
        resp = json.loads(resp_str)
        logger.debug("receive request: {}".format(resp))
        # 需要将json转换成Message类型

        message = dict_2_message(resp)
        msg_consume_status = MessageConsumeStatus(
            msg_meta=message.msg_meta,
            consume_node=self._consumer_node,
            consume_status=ConsumeStatus.RECEIVED,
        )
        msg_consume_status.consume_node.reach_time = int(
            datetime.datetime.now().timestamp()
        )

        ret = self._on_req_func(message)
