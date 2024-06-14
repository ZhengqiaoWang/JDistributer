from dataclasses import dataclass, field
from enum import Enum


# topic模板
TOPIC_TEMPLATE_REQ = "JD_REQ_{}"
TOPIC_TEMPLATE_REQ_RPLY = "JD_REQ_RPLY_{}"
TOPIC_TEMPLATE_RSP = "JD_RSP_{}"


@dataclass
class CustomMessage:
    body: str = field(default_factory=str)  # 消息体
    expect_consume_num: int = field(
        default_factory=int
    )  # 最少被消费次数，当组消费且有确定组数量时配置


def dict_2_custom_message(src: dict):
    if None == src:
        return None
    return CustomMessage(
        body=src.get("body"),
        expect_consume_num=src.get("expect_consume_num"),
    )


@dataclass
class NodeInfo:
    name: str = field(default_factory=str)  # 节点名称
    host: str = field(default_factory=str)  # 节点host name
    reach_time: int = field(default_factory=int)  # timestamp sec 到达该节点时间戳


def dict_2_node_info(src: dict):
    if None == src:
        return None
    return NodeInfo(
        name=src.get("name"), host=src.get("host"), reach_time=src.get("reach_time")
    )


@dataclass
class MessageMeta:
    msg_id: str = field(default_factory=str)  # 消息id
    topic: str = field(default_factory=str)  # 消息主题
    product_node: NodeInfo = field(default_factory=NodeInfo)  # 消息生产者节点信息


def dict_2_message_meta(src: dict):
    if None == src:
        return None
    return MessageMeta(
        msg_id=src.get("msg_id"),
        topic=src.get("topic"),
        product_node=dict_2_node_info(src.get("product_node")),
    )


@dataclass
class Message:
    msg_meta: MessageMeta = field(default_factory=MessageMeta)
    custom_msg: CustomMessage = field(default_factory=CustomMessage)


def dict_2_message(src: dict):
    if None == src:
        return None
    return Message(
        msg_meta=dict_2_message_meta(src.get("msg_meta")),
        custom_msg=dict_2_custom_message(src.get("custom_msg")),
    )


# 生产者视角：消息状态
class ProduceStatus(int, Enum):
    UNKNOWN = 0
    REQUEST_SENDED = 1  # 消息已发送
    # 消息已被消费者接受，组消费时任意消费者消费会变为此状态
    REQUEST_REPLIED = 2
    SUCCESS = 3  # 消息消费成功
    FAILED = 4  # 消息消费失败


@dataclass
class MessageStatusStatistic:
    produce_status: ProduceStatus = ProduceStatus.UNKNOWN  # 当前消息状态
    pending_consumed_num: int = 0  # 已被接收且等待被消费的数量
    success_consumed_num: int = 0  # 已被成功消费数量
    failed_consumed_num: int = 0  # 消费失败数量


@dataclass
class MessageDetail:
    msg_status_statistic: MessageStatusStatistic = field(
        default_factory=MessageStatusStatistic
    )
    msg: Message = field(default_factory=Message)


class ConsumeStatus(int, Enum):
    UNKNOWN = 0
    RECEIVED = 1
    REJECT = 2
    SUCCESS = 3
    FAILED = 4


@dataclass
class MessageConsumeStatus:
    msg_meta: MessageMeta = field(default_factory=MessageMeta)
    consume_node: NodeInfo = field(default_factory=NodeInfo)
    consume_status: ConsumeStatus = ConsumeStatus.UNKNOWN
    rsp_msg: str = field(default_factory=str)  # 返回的状态


def dict_2_message_consume_status(src: dict) -> MessageConsumeStatus:
    if None == src:
        return None
    return MessageConsumeStatus(
        msg_meta=dict_2_message_meta(src.get("msg_meta")),
        consume_node=dict_2_node_info(src.get("consume_node")),
        consume_status=ConsumeStatus(src.get("consume_status")),
        rsp_msg=src.get("rsp_msg"),
    )


def OnProductSuccessFuncTemplate(msg_detail: MessageDetail) -> None:
    pass


def OnProductFailedFuncTemplate(
    msg_detail: MessageDetail, consume_status: MessageConsumeStatus
) -> None:
    pass


@dataclass
class ResponseStatus:
    is_ok: bool
    response_msg: str = ""


def OnConsumerRequestReceiveFuncTemplate(message: Message) -> ResponseStatus:
    return ResponseStatus(True)
