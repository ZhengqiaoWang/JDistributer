# from redis.cluster import RedisCluster as Redis
from redis import Redis
from redis.retry import Retry
from redis.backoff import ExponentialBackoff
import threading
import logging
import time
from dataclasses import dataclass

logger = logging.getLogger("JDistributer")


@dataclass
class RedisSettings:
    """Redis 连接设置"""

    host: str
    port: int
    password: str


class RedisAdapterBase:
    def init_client(self, host: str, port: int, password: str) -> None:
        self._host = host
        self._port = port
        self._password = password

        self.connect()

    def init_client_from(self, src) -> None:
        self._client = src._client

    def connect(self) -> None:
        self._client = Redis(
            host=self._host,
            port=self._port,
            password=self._password,
            retry=Retry(ExponentialBackoff(cap=5 * 60, base=5), retries=-1),
        )
        logger.debug("try to connect redis: {}:{}".format(self._host, self._port))


class RedisTopicAdapterBase(RedisAdapterBase):
    def __init__(self) -> None:
        super().__init__()
        self._topic_name = None

    def init_topic(self, topic_name: str) -> None:
        self._topic_name = topic_name


class RedisConsumerAdapter(RedisTopicAdapterBase):
    def __init__(self) -> None:
        super().__init__()
        self._run_flag = False
        self._thread = None
        self._cb_func = None

    def init_cb_func(self, cb_func) -> None:
        self._cb_func = cb_func

    def start(self):
        self._run_flag = True

        self._thread = threading.Thread(target=self._thread_func)
        self._thread.start()

    def stop(self):
        self._run_flag = False
        if self._thread is not None and self._thread.is_alive():
            self._thread.join()

    def _thread_func(self):
        logger.debug("start to xread topic[{}] from redis".format(self._topic_name))
        try:
            stream_info = self._client.xinfo_stream(self._topic_name)
            next_id = stream_info.get("last-entry")[0]
        except:
            next_id = 0

        while self._run_flag:
            try:
                ret = self._client.xread(
                    {self._topic_name: next_id}, count=1, block=1000
                )
                if len(ret) == 0:
                    continue
            except Exception as e:
                logger.warn("Failed to read message, {}".format(e))
                time.sleep(0.5)
                continue

            message = ret[0][1][0]
            next_id = message[0]

            response = dict(message[1])
            self._call_funcs(response.get(b"body"))
        logger.debug("stop to xread topic[{}] from redis".format(self._topic_name))

    def _call_funcs(self, message):
        self._cb_func(message)


class RedisProducerAdapter(RedisTopicAdapterBase):
    def produce(self, message: str):
        produce_msg = {"body": message}
        logger.debug(
            "try to xadd topic[{}] to redis: {}".format(self._topic_name, produce_msg)
        )
        return self._client.xadd(self._topic_name, produce_msg)


class RedisGroupAdapterBase(RedisTopicAdapterBase):
    def __init__(self) -> None:
        super().__init__()
        self._group_name = None

    def init_group_name(self, group_name: str) -> None:
        self._group_name = group_name


class RedisGroupConsumerAdapter(RedisConsumerAdapter, RedisGroupAdapterBase):
    def __init__(self) -> None:
        super().__init__()
        self._consumer_name = None

    def init_consumer(self, consumer_name: str) -> None:
        self._consumer_name = consumer_name

    def connect(self) -> None:
        ret = super().connect()
        try:
            logger.debug(
                "try to xgroup_create topic[{}] group[{}] to redis".format(
                    self._topic_name, self._group_name
                )
            )
            self._client.xgroup_create(
                self._topic_name, self._group_name, mkstream=True
            )
        except:
            pass

        return ret

    def _thread_func(self):
        logger.debug(
            "start to xreadgroup topic[{}] group[{}] as consumer[{}] from redis".format(
                self._topic_name,
                self._group_name,
                self._consumer_name,
            )
        )
        while self._run_flag:
            try:
                ret = self._client.xreadgroup(
                    self._group_name,
                    self._consumer_name,
                    {self._topic_name: ">"},
                    count=1,
                    block=1000,
                )
                if len(ret) == 0:
                    continue
            except Exception as e:
                logger.warn("Failed to group read message, {}".format(e))
                time.sleep(0.5)
                continue

            message = ret[0][1][0]
            self._client.xack(self._topic_name, self._group_name, message[0])

            response = dict(message[1])
            self._call_funcs(response.get(b"body"))
        logger.debug(
            "stop to xreadgroup topic[{}] group[{}] as consumer[{}] from redis".format(
                self._topic_name,
                self._group_name,
                self._consumer_name,
            )
        )
