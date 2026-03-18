# ──────────────────────────────────────────────────────────────
# kafka_client.py — Kafka producer + Dead Letter Queue
# Only responsibility: publish messages to Kafka topics
# ──────────────────────────────────────────────────────────────
import logging
from kafka import KafkaProducer
from kafka.errors import KafkaError
from config import Config
from typing import Optional

logger = logging.getLogger(__name__)


def make_producer(config: Config) -> KafkaProducer:
    """
    Pure factory function — creates and returns a KafkaProducer.
    Message values are raw bytes (serialized in transforms.py).
    """
    return KafkaProducer(
        bootstrap_servers=config.kafka_bootstrap_servers,
        acks="all",                  # wait for all replicas to confirm
        retries=5,
        max_in_flight_requests_per_connection=1,
        compression_type="gzip",
    )


def publish(
    producer: KafkaProducer,
    topic: str,
    message: bytes,
    key: Optional[bytes] = None,
) -> bool:
    """
    Sends a message to a Kafka topic.
    Returns True on success, False on failure.
    """
    try:
        future = producer.send(topic, value=message, key=key)
        future.get(timeout=10)       # block until confirmed
        return True
    except KafkaError as e:
        logger.error(f"Failed to publish to {topic}: {e}")
        return False


def publish_to_dlq(
    producer: KafkaProducer,
    dlq_topic: str,
    message: bytes,
) -> None:
    """
    Sends a poison/failed message to the Dead Letter Queue.
    Logs but does not raise — DLQ failures should never crash the pipeline.
    """
    try:
        producer.send(dlq_topic, value=message)
        producer.flush()
        logger.warning(f"Message sent to DLQ: {dlq_topic}")
    except KafkaError as e:
        logger.error(f"Failed to publish to DLQ {dlq_topic}: {e}")


