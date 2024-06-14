from dataclasses import dataclass, field, asdict
import json
import random
import socket
from JDistributer.adapter.mq.redis_adapter import (
    RedisProducerAdapter,
    RedisSettings,
)
import datetime
from JDistributer.common_define import (
    NodeInfo,
    Message,
    MessageMeta,
    TOPIC_TEMPLATE_REQ,
    CustomMessage,
)

import logging

logger = logging.getLogger("JDistributer")


@dataclass
class NoReplyProducerClientStruct:
    req_producer: RedisProducerAdapter


# 无回复生产者
class NoReplyProducer:

    def __init__(
        self,
        redis_settings: RedisSettings,
        topic_name: str,
        producer_name: str = "default_producer",
    ) -> None:
        self._product_node = NodeInfo(
            name="{}-{}".format(
                producer_name, int(datetime.datetime.now().timestamp())
            ),
            host=socket.gethostname(),
        )
        self._rply_producer_client_struct = NoReplyProducerClientStruct(
            req_producer=RedisProducerAdapter(),
        )
        self._topic_name = topic_name

        # 注册topic到监听
        self._rply_producer_client_struct.req_producer.init_topic(
            topic_name=TOPIC_TEMPLATE_REQ.format(topic_name)
        )

        # 初始化
        self._rply_producer_client_struct.req_producer.init_client(
            redis_settings.host, redis_settings.port, redis_settings.password
        )

    async def async_product(
        self,
        custom_message: CustomMessage,
    ) -> None:
        # 对message生成一个ID，为_producer_name-产生消息的时间戳-随机数
        message_id = "{}-{}-{}".format(
            self._product_node.name,
            int(datetime.datetime.now().timestamp()),
            random.randint(0, 100),
        )

        # 发送消息
        ret_id = self._rply_producer_client_struct.req_producer.produce(
            json.dumps(
                asdict(
                    Message(
                        msg_meta=MessageMeta(
                            msg_id=message_id,
                            topic=self._topic_name,
                            product_node=NodeInfo(
                                self._product_node.name,
                                self._product_node.host,
                                reach_time=int(datetime.datetime.now().timestamp()),
                            ),
                        ),
                        custom_msg=custom_message,
                    )
                )
            )
        )
        logger.debug("produce message id: {}".format(ret_id))
