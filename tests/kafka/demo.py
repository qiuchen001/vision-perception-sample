from kafka.admin import KafkaAdminClient
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable, KafkaError
import json
import signal
import sys
import time

# Kafka 配置
bootstrap_servers = '10.66.12.37:30094'
security_protocol = 'SASL_PLAINTEXT'
sasl_mechanism = 'PLAIN'
sasl_plain_username = 'client'
sasl_plain_password = 'client-secret'

# 创建 KafkaAdminClient
admin_client = KafkaAdminClient(
    bootstrap_servers=bootstrap_servers,
    security_protocol=security_protocol,
    sasl_mechanism=sasl_mechanism,
    sasl_plain_username=sasl_plain_username,
    sasl_plain_password=sasl_plain_password,
)

# 获取 Topic 列表
topic_list = admin_client.list_topics()
print("Topics:")
for topic in topic_list:
    print(topic)


# 获取 Topic 对应的 Partition 信息
def describe_topic_partitions(topic_name):
    try:
        # 获取 Topic 的描述信息
        topic_description = admin_client.describe_topics([topic_name])
        partitions = topic_description[0]['partitions']
        print(f"\nTopic '{topic_name}' partitions:")
        for partition in partitions:
            print(
                f"  Partition {partition['partition']}: Leader={partition['leader']}, Replicas={partition['replicas']}, ISR={partition['isr']}")
    except Exception as e:
        print(f"Failed to describe partitions for topic '{topic_name}': {e}")


# 删除指定的 Topic
def delete_topic(topic_name):
    try:
        # 确认 Topic 存在
        if topic_name not in topic_list:
            print(f"Topic '{topic_name}' does not exist.")
            return

        # 删除 Topic
        admin_client.delete_topics([topic_name], timeout_ms=5000)
        print(f"Topic '{topic_name}' has been deleted.")
    except Exception as e:
        print(f"Failed to delete topic '{topic_name}': {e}")


# 消费指定 Topic 的消息
def consume_messages(topic_name, max_messages=5, timeout_ms=5000):
    try:
        # 创建 KafkaConsumer 客户端
        consumer = KafkaConsumer(
            topic_name,
            bootstrap_servers=bootstrap_servers,
            security_protocol=security_protocol,
            sasl_mechanism=sasl_mechanism,
            sasl_plain_username=sasl_plain_username,
            sasl_plain_password=sasl_plain_password,
            auto_offset_reset='earliest',  # 从最早的消息开始读取
            enable_auto_commit=False,  # 禁用自动提交偏移量
            value_deserializer=lambda x: x.decode('utf-8'),  # 按 UTF-8 解码
            consumer_timeout_ms=timeout_ms  # 超时自动停止消费
        )

        print(f"\nReading up to {max_messages} messages from topic '{topic_name}':")
        message_count = 0

        # 拉取消息
        for message in consumer:
            print(f"[Partition {message.partition}] Offset {message.offset}: {message.value}")
            message_count += 1
            if message_count >= max_messages:
                break

    except NoBrokersAvailable:
        print("Error: Could not connect to Kafka brokers")
    except Exception as e:
        print(f"Failed to consume messages: {e}")
    finally:
        if 'consumer' in locals():
            consumer.close()


def get_topic_partition_count(topic_name):
    try:
        # 获取 Topic 的描述信息
        topic_description = admin_client.describe_topics([topic_name])
        partitions = topic_description[0]['partitions']
        # 返回 Partition 数量
        return len(partitions)
    except Exception as e:
        print(f"Failed to get partition count for topic '{topic_name}': {e}")
        return None


# # 示例：查看所有 Topic 的 Partition 信息
# for topic in topic_list:
#     describe_topic_partitions(topic)

# 示例：删除名为 'my-topic-to-delete' 的 Topic
# topic_to_delete = 'public-structure-job-trigger'
# delete_topic(topic_to_delete)

# 示例：查看名为 'public-structure-job-trigger' 的 Topic 消息
# consume_messages("public-upload-xosc-trigger", max_messages=3)

# 关闭客户端
admin_client.close()

print("*" * 50)


def send_message(topic_name, message, sync=True, partition=None, key=None):
    """
    向指定的Kafka topic发送消息
    
    Args:
        topic_name (str): Topic名称
        message (str/dict): 要发送的消息,支持字符串或字典
        sync (bool): 是否同步发送,默认True
        partition (int): 指定分区,默认None(由Kafka自动分配)
        key (str): 消息的key,默认None
        
    Returns:
        bool: 同步发送时返回是否发送成功,异步发送时返回None
    """
    try:
        # 创建producer
        producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            security_protocol=security_protocol,
            sasl_mechanism=sasl_mechanism,
            sasl_plain_username=sasl_plain_username,
            sasl_plain_password=sasl_plain_password,
            value_serializer=lambda x: json.dumps(x).encode('utf-8') if isinstance(x, dict) else str(x).encode('utf-8'),
            key_serializer=lambda x: str(x).encode('utf-8') if x else None
        )

        # 定义回调函数
        def on_send_success(record_metadata):
            print(
                f'消息发送成功 - topic: {record_metadata.topic}, partition: {record_metadata.partition}, offset: {record_metadata.offset}')

        def on_send_error(excp):
            print(f'消息发送失败: {excp}')

        # 发送消息
        future = producer.send(
            topic_name,
            value=message,
            partition=partition,
            key=key
        )

        # 处理同步/异步逻辑
        if sync:
            try:
                record_metadata = future.get(timeout=10)
                on_send_success(record_metadata)
                return True
            except KafkaError as e:
                on_send_error(e)
                return False
        else:
            future.add_callback(on_send_success).add_errback(on_send_error)
            return None

    except Exception as e:
        print(f'发送消息时发生错误: {e}')
        return False
    finally:
        # 确保关闭producer
        if 'producer' in locals():
            producer.close()


def consume_latest_messages(topic_name):
    """
    持续消费指定Topic的最新消息
    
    Args:
        topic_name (str): Topic名称
    """
    # 用于处理中断信号
    running = True

    def signal_handler(signum, frame):
        nonlocal running
        print("\n正在优雅退出...")
        running = False

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 创建消费者
        consumer = KafkaConsumer(
            topic_name,
            bootstrap_servers=bootstrap_servers,
            security_protocol=security_protocol,
            sasl_mechanism=sasl_mechanism,
            sasl_plain_username=sasl_plain_username,
            sasl_plain_password=sasl_plain_password,
            auto_offset_reset='latest',  # 从最新的消息开始读取
            enable_auto_commit=True,  # 启用自动提交
            value_deserializer=lambda x: x.decode('utf-8')  # UTF-8解码
        )

        print(f"\n开始消费Topic '{topic_name}'的消息 (按Ctrl+C退出):")
        message_count = 0
        start_time = time.time()

        # 持续消费消息
        while running:
            # 批量获取消息,超时时间1秒
            messages = consumer.poll(timeout_ms=1000)

            for tp, records in messages.items():
                for record in records:
                    print(f"[分区 {record.partition}] 偏移量 {record.offset}: {record.value}")
                    message_count += 1

                    # 每100条消息显示一次统计信息
                    if message_count % 100 == 0:
                        elapsed_time = time.time() - start_time
                        rate = message_count / elapsed_time
                        print(f"\n--- 统计信息 ---")
                        print(f"已消费消息数: {message_count}")
                        print(f"平均消费速率: {rate:.2f} 消息/秒")
                        print("---------------\n")

    except NoBrokersAvailable:
        print("错误: 无法连接到Kafka集群")
    except Exception as e:
        print(f"消费消息时发生错误: {e}")
    finally:
        if 'consumer' in locals():
            consumer.close()
            elapsed_time = time.time() - start_time
            print(f"\n总共消费了 {message_count} 条消息")
            if elapsed_time > 0:
                print(f"平均消费速率: {message_count / elapsed_time:.2f} 消息/秒")


if __name__ == "__main__":
    # 发送消息
    send_message("public-collect-import-success", {
        "taskid": "9cf99967-aa69-44cd-b4f2-d22d886817fb",
        # "raw_id": "9a8afc7e-19de-4e13-8b3c-44794ccb49c6"
        "raw_id": "9a8afc7e-19de-4e13-8b3c-44794ccb49c6"
    })

    # 消费消息
    # 持续消费指定Topic的最新消息
    # consume_latest_messages("public-vision-perception-upload-success")
