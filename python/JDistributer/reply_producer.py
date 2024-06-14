from dataclasses import dataclass, field, asdict
import json
import random
import socket
import threading
from JDistributer.adapter.mq.redis_adapter import (
    RedisProducerAdapter,
    RedisConsumerAdapter,
    RedisSettings,
)
from collections import defaultdict
import datetime
from JDistributer.common_define import (
    NodeInfo,
    Message,
    MessageMeta,
    MessageDetail,
    ProduceStatus,
    TOPIC_TEMPLATE_REQ,
    TOPIC_TEMPLATE_REQ_RPLY,
    TOPIC_TEMPLATE_RSP,
    OnProductSuccessFuncTemplate,
    OnProductFailedFuncTemplate,
    CustomMessage,
    dict_2_message_consume_status,
    ConsumeStatus,
)

import logging

logger = logging.getLogger("JDistributer")


@dataclass
class ReplyProducerClientStruct:
    req_producer: RedisProducerAdapter
    req_rply_consumer: RedisConsumerAdapter
    rsp_consumer: RedisConsumerAdapter


@dataclass
class ProductStatusStruct:
    msg_detail: MessageDetail = field(default_factory=MessageDetail)
    on_success_func: OnProductSuccessFuncTemplate = field(init=False)
    on_failed_func: OnProductFailedFuncTemplate = field(init=False)
    msg_consume_status_list: list = field(
        default_factory=list
    )  # MessageConsumeStatus list


# 有回复生产者
class ReplyProducer:

    def __init__(
        self,
        redis_settings: RedisSettings,
        topic_name: str,
        producer_name: str = "default_producer",
    ) -> None:
        self._msg_id_2_status_list_dict = defaultdict(ProductStatusStruct)

        self._product_node = NodeInfo(
            name="{}-{}".format(
                producer_name, int(datetime.datetime.now().timestamp())
            ),
            host=socket.gethostname(),
        )
        self._rply_producer_client_struct = ReplyProducerClientStruct(
            req_producer=RedisProducerAdapter(),
            req_rply_consumer=RedisConsumerAdapter(),
            rsp_consumer=RedisConsumerAdapter(),
        )
        self._topic_name = topic_name

        # 注册topic到监听
        self._rply_producer_client_struct.req_producer.init_topic(
            topic_name=TOPIC_TEMPLATE_REQ.format(topic_name)
        )
        self._rply_producer_client_struct.req_rply_consumer.init_topic(
            topic_name=TOPIC_TEMPLATE_REQ_RPLY.format(topic_name)
        )
        self._rply_producer_client_struct.rsp_consumer.init_topic(
            topic_name=TOPIC_TEMPLATE_RSP.format(topic_name)
        )

        # 初始化
        self._rply_producer_client_struct.req_producer.init_client(
            redis_settings.host, redis_settings.port, redis_settings.password
        )
        self._rply_producer_client_struct.req_rply_consumer.init_client_from(
            self._rply_producer_client_struct.req_producer
        )
        self._rply_producer_client_struct.rsp_consumer.init_client_from(
            self._rply_producer_client_struct.req_producer
        )
        self._rply_producer_client_struct.req_rply_consumer.init_cb_func(
            self._on_req_rply_receive
        )
        self._rply_producer_client_struct.rsp_consumer.init_cb_func(self._on_rsp_receive)

    async def async_product(
        self,
        custom_message: CustomMessage,
        on_success_func: OnProductSuccessFuncTemplate,
        on_failed_func: OnProductFailedFuncTemplate,
    ) -> MessageDetail:
        # 对message生成一个ID，为_producer_name-产生消息的时间戳-随机数
        message_id = "{}-{}-{}".format(
            self._product_node.name,
            int(datetime.datetime.now().timestamp()),
            random.randint(0, 100),
        )
        # 将ID缓存到map中，用于标记是自身产生的消息。在回调中随时更新。
        product_status_struct = self._msg_id_2_status_list_dict[message_id]
        product_status_struct.on_success_func = on_success_func
        product_status_struct.on_failed_func = on_failed_func
        product_status_struct.msg_detail = MessageDetail(
            msg=Message(
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

        # 发送消息
        ret_id = self._rply_producer_client_struct.req_producer.produce(
            json.dumps(asdict(product_status_struct.msg_detail.msg))
        )
        logger.debug("produce message id: {}".format(ret_id))

        # 设置状态为发送完成
        product_status_struct.msg_detail.msg_status_statistic.produce_status = (
            ProduceStatus.REQUEST_SENDED
        )

        # 返回msg detail
        return product_status_struct.msg_detail

    def start(self):
        self._rply_producer_client_struct.req_rply_consumer.start()
        self._rply_producer_client_struct.rsp_consumer.start()

    def release(self) -> None:
        # 取消监听注册
        self._rply_producer_client_struct.req_rply_consumer.stop()
        self._rply_producer_client_struct.rsp_consumer.stop()

    def get_consume_status(self, message_id) -> list:
        product_status_struct = self._msg_id_2_status_list_dict.get(message_id)
        if None == product_status_struct:
            # 说明接收到的不是自己生产的，过滤即可
            return None

        return product_status_struct.msg_consume_status_list

    def _on_req_rply_receive(self, resp_str: str):
        resp = json.loads(resp_str)
        logger.debug("receive request reply: {}".format(resp))
        msg_consume_status = dict_2_message_consume_status(resp)
        # 记录状态

        product_status_struct = self._msg_id_2_status_list_dict.get(
            msg_consume_status.msg_meta.msg_id
        )
        if None == product_status_struct:
            # 说明接收到的不是自己生产的，过滤即可
            return

        msg_status_statis = product_status_struct.msg_detail.msg_status_statistic

        msg_status_statis.pending_consumed_num += 1
        # 自己生产的，且状态是已发送，且数量>=最小预期，设置为已回复
        if msg_status_statis.produce_status == ProduceStatus.REQUEST_SENDED:
            msg_status_statis.produce_status = ProduceStatus.REQUEST_REPLIED

    def _on_rsp_receive(self, resp_str: str):
        resp = json.loads(resp_str)
        logger.debug("receive response: {}".format(resp))
        msg_consume_status = dict_2_message_consume_status(resp)

        product_status_struct = self._msg_id_2_status_list_dict.get(
            msg_consume_status.msg_meta.msg_id
        )
        if None == product_status_struct:
            # 说明接收到的不是自己生产的，过滤即可
            return

        product_status_struct.msg_consume_status_list.append(msg_consume_status)
        msg = product_status_struct.msg_detail.msg
        msg_detail = product_status_struct.msg_detail
        msg_status_statis = product_status_struct.msg_detail.msg_status_statistic
        # 是自己生产的

        msg_status_statis.pending_consumed_num -= 1
        if ConsumeStatus.SUCCESS == msg_consume_status.consume_status:
            # 成功
            msg_status_statis.success_consumed_num += 1
        elif ConsumeStatus.FAILED == msg_consume_status.consume_status:
            # 失败
            msg_status_statis.failed_consumed_num += 1
        else:
            assert(False)

        # 如果状态是已回复且成功数量>=expect_min_consume_num，那么标记为成功
        # 如果状态是已回复且失败数量>0，则标记为失败
        if (
            msg_status_statis.produce_status == ProduceStatus.REQUEST_REPLIED
            and msg_status_statis.success_consumed_num
            >= msg.custom_msg.expect_consume_num
        ):
            msg_status_statis.produce_status = ProduceStatus.SUCCESS
            product_status_struct.on_success_func(msg_detail)
        elif (
            msg_status_statis.produce_status == ProduceStatus.REQUEST_REPLIED
            and msg_status_statis.failed_consumed_num > 0
        ):
            msg_status_statis.produce_status = ProduceStatus.FAILED
            product_status_struct.on_failed_func(msg_detail, msg_consume_status)
