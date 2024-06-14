# JDistributer

消息队列载体：Redis-Cluster

支持功能：

1. REQ消息体包含
    1. 生成时间戳
    2. 生成机器
    3. body
2. RPLY消息体包含
    1. REQ/RSP生成时间戳
    2. REQ/RSP生成机器
    3. RPLY生成时间戳
    4. RPLY生成机器
    5. 状态
    6. 消息
3. RSP消息提包含
    1. REQ生成时间戳
    2. REQ生成机器
    3. RSP生成时间戳
    4. RSP生成机器
    3. 状态
    4. 消息
2. 生产者生成消息，接受反馈
3. 


一个主题理论上会创建多个redis主题：
1. JD_REQ_{主题} 组消费模式
2. JD_REQ_RPLY_{主题} 广播消费模式
3. JD_RSP_{主题} 广播消费模式

生产者产生消息：
```c++
enum RequestStatus{
    REQUEST_SENDED,
    REQUEST_REPLIED,
    SUCCESS,
    FAILED
};

class ProductStatus{
public:
RequestStatus status;
std::string message;
};
using ProductStatusPtr = std::shared_ptr<ProductStatus>;

ProductStatusPtr async_product(Message, OnSuccessFunc, OnFailedFunc);
```

```python
class RequestStatus(Enum):
    REQUEST_SENDED,
    REQUEST_REPLIED,
    SUCCESS,
    FAILED



```