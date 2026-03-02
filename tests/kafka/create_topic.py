from kafka.admin import KafkaAdminClient, NewTopic
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import NoBrokersAvailable, KafkaError
import json
import signal
import sys
import time

# Kafka 配置
# bootstrap_servers = '10.66.12.37:30094'
# bootstrap_servers = '10.66.8.51:30096'
# bootstrap_servers = '10.66.12.37:30096'
bootstrap_servers = '10.66.12.37:30092'
# bootstrap_servers = '10.66.12.37:30095'
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


def create_kafka_topic(topic_name, num_partitions=1, replication_factor=1):
    """
    创建Kafka主题

    参数:
        topic_name: 主题名称
        num_partitions: 分区数量，默认为1
        replication_factor: 副本因子，默认为1
    """
    try:
        # 创建Topic配置
        topic = NewTopic(
            name=topic_name,
            num_partitions=num_partitions,
            replication_factor=replication_factor
        )

        # 创建主题
        admin_client.create_topics(new_topics=[topic], validate_only=False)
        print(f"主题创建成功：{topic_name}")

    except Exception as e:
        print(f"创建主题失败：{str(e)}")


# 使用示例
if __name__ == "__main__":
    # 配置参数
    prefix = "public-"
    topic_name = prefix + "data-sync-trigger"  # 替换为您的主题名称
    partitions = 1  # 分区数量
    replication = 1  # 副本因子

    # 创建主题
    create_kafka_topic(topic_name, partitions, replication)

    # 关闭连接
    admin_client.close()