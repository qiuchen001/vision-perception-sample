#!/usr/bin/env python3

"""
Simple CLI to list existing Kafka topics.

Requirements:
  pip install kafka-python

Usage examples:
  python tools/kafka_list_topics.py --bootstrap 10.66.12.37:30096
  python tools/kafka_list_topics.py --bootstrap 10.66.12.37:30096 --details

Notes:
  - This script assumes PLAINTEXT (no authentication).
  - For multiple brokers, pass comma-separated: host1:port,host2:port
"""

import argparse
import sys
from typing import List

try:
    from kafka import KafkaConsumer
    from kafka.errors import NoBrokersAvailable
except Exception as e:  # pragma: no cover
    print("Missing dependency 'kafka-python'. Install with: pip install kafka-python")
    raise


def list_topics(bootstrap_servers: List[str], timeout_ms: int, details: bool) -> int:
    """Connect to Kafka and print topics (optionally with partition counts).

    Returns process exit code (0 on success, non-zero on failure).
    """
    try:
        consumer = KafkaConsumer(
            bootstrap_servers=bootstrap_servers,
            client_id="topic-lister",
            security_protocol="PLAINTEXT",
            request_timeout_ms=timeout_ms,
            api_version_auto_timeout_ms=min(timeout_ms, 5000),
        )
    except NoBrokersAvailable as e:
        print(f"ERROR: No brokers available at {','.join(bootstrap_servers)}")
        return 2
    except Exception as e:
        print(f"ERROR: Failed to create KafkaConsumer: {e}")
        return 3

    try:
        topics = sorted(consumer.topics())
    except Exception as e:
        print(f"ERROR: Failed to fetch topics: {e}")
        consumer.close()
        return 4

    if not topics:
        print("No topics found.")
        consumer.close()
        return 0

    if details:
        # Fetch partition count for each topic
        print("Topics (with partition count):")
        for t in topics:
            try:
                parts = consumer.partitions_for_topic(t) or set()
                print(f"- {t} (partitions: {len(parts)})")
            except Exception:
                print(f"- {t} (partitions: unknown)")
    else:
        print("Topics:")
        for t in topics:
            print(f"- {t}")

    consumer.close()
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List Kafka topics")
    parser.add_argument(
        "--bootstrap",
        default="10.66.12.37:30094",
        required=False,
        help="Bootstrap servers, e.g. '10.66.12.37:30094' or 'host1:port,host2:port'",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=10000,
        help="Client request timeout in milliseconds (default: 10000)",
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="Show partition count per topic",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bootstrap_servers = [s.strip() for s in args.bootstrap.split(",") if s.strip()]
    if not bootstrap_servers:
        print("ERROR: --bootstrap must provide at least one 'host:port'.")
        sys.exit(1)

    rc = list_topics(bootstrap_servers, args.timeout_ms, args.details)
    sys.exit(rc)


if __name__ == "__main__":
    main()