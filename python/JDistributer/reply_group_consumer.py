from dataclasses import dataclass, asdict
import json
import random
import socket
import datetime
import logging
from JDistributer.adapter.mq.redis_adapter import (
    RedisProducerAdapter,
    RedisGroupConsumerAdapter,
    RedisSettings,
)
from JDistributer.common_define import (
    NodeInfo,
    dict_2_message,
    TOPIC_TEMPLATE_REQ,
    TOPIC_TEMPLATE_REQ_RPLY,
    TOPIC_TEMPLATE_RSP,
    MessageConsumeStatus,
    ConsumeStatus,
    OnConsumerRequestReceiveFuncTemplate,
)


logger = logging.getLogger("JDistributer")


@dataclass
class GroupConsumerClientStruct:
    req_group_consumer: RedisGroupConsumerAdapter
    req_rply_producer: RedisProducerAdapter
    rsp_producer: RedisProducerAdapter


# TODO 继承自reply_consumer
# 有回复组消费者
class ReplyGroupConsumer:

    def __init__(
        self,
        redis_settings: RedisSettings,
        topic_name: str,
        group_name: str,
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
        self._consumer_client_struct = GroupConsumerClientStruct(
            req_group_consumer=RedisGroupConsumerAdapter(),
            req_rply_producer=RedisProducerAdapter(),
            rsp_producer=RedisProducerAdapter(),
        )
        self._group_name = group_name
        self._topic_name = topic_name
        self._on_req_func = on_req_func

        # 注册topic到监听
        self._consumer_client_struct.req_group_consumer.init_topic(
            topic_name=TOPIC_TEMPLATE_REQ.format(topic_name)
        )
        self._consumer_client_struct.req_rply_producer.init_topic(
            topic_name=TOPIC_TEMPLATE_REQ_RPLY.format(topic_name)
        )
        self._consumer_client_struct.rsp_producer.init_topic(
            topic_name=TOPIC_TEMPLATE_RSP.format(topic_name)
        )
        self._consumer_client_struct.req_group_consumer.init_group_name(
            group_name=self._group_name
        )
        self._consumer_client_struct.req_group_consumer.init_consumer(
            consumer_name=self._consumer_node.name
        )

        # 初始化
        self._consumer_client_struct.req_group_consumer.init_client(
            redis_settings.host, redis_settings.port, redis_settings.password
        )
        self._consumer_client_struct.req_rply_producer.init_client_from(
            self._consumer_client_struct.req_group_consumer
        )
        self._consumer_client_struct.rsp_producer.init_client_from(
            self._consumer_client_struct.req_group_consumer
        )

        self._consumer_client_struct.req_group_consumer.init_cb_func(
            self._on_req_receive
        )

    def start(self):
        self._consumer_client_struct.req_group_consumer.start()

    def release(self) -> None:
        # 取消监听注册
        self._consumer_client_struct.req_group_consumer.stop()

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

        # RPLY返回
        ret_id = self._consumer_client_struct.req_rply_producer.produce(
            json.dumps(asdict(msg_consume_status))
        )
        ret = self._on_req_func(message)
        logger.debug("reply request: {} as ret_id: {}".format(resp, ret_id))

        msg_consume_status.consume_status = (
            ConsumeStatus.SUCCESS if ret.is_ok else ConsumeStatus.FAILED
        )
        msg_consume_status.rsp_msg = ret.response_msg

        # RSP返回
        ret_id = self._consumer_client_struct.rsp_producer.produce(
            json.dumps(asdict(msg_consume_status))
        )
        logger.debug("response request: {} as ret_id: {}".format(resp, ret_id))
