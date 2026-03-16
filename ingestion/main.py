# ──────────────────────────────────────────────────────────────
# main.py — entry point
# Wires config → fetch → transform → publish
# This file contains no business logic — just composition
# ──────────────────────────────────────────────────────────────
import time
import logging
from config import load_config
from fetcher import fetch_activities, fetch_reviews
from transforms import (
    parse_activities,
    parse_reviews,
    serialize,
    serialize_error,
)
from kafka_client import make_producer, publish, publish_to_dlq

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def process_activities(config, producer) -> int:
    """Fetch → parse → publish activities. Returns count published."""
    raw_list = fetch_activities(config)
    events = parse_activities(raw_list)
    published = 0

    for event in events:
        message = serialize(event)
        success = publish(
            producer,
            config.kafka_topic_raw,
            message,
            key=str(event.id).encode(),
        )
        if success:
            published += 1
        else:
            # Failed to publish — send to DLQ
            dlq_message = serialize_error(event.to_dict(), "kafka_publish_failed")
            publish_to_dlq(producer, config.kafka_topic_dlq, dlq_message)

    return published


def process_reviews(config, producer) -> int:
    """Fetch → parse → publish reviews. Returns count published."""
    raw_list = fetch_reviews(config)
    events = parse_reviews(raw_list)
    published = 0

    for event in events:
        message = serialize(event)
        success = publish(
            producer,
            config.kafka_topic_raw,
            message,
            key=str(event.id).encode(),
        )
        if success:
            published += 1
        else:
            dlq_message = serialize_error(event.to_dict(), "kafka_publish_failed")
            publish_to_dlq(producer, config.kafka_topic_dlq, dlq_message)

    return published


def run() -> None:
    """Main loop — polls AniList every N seconds forever."""
    config = load_config()
    producer = make_producer(config)

    logger.info(f"🚀 Producer started — polling every {config.poll_interval_seconds}s")
    logger.info(f"   Media ID : {config.anilist_media_id}")
    logger.info(f"   Kafka    : {config.kafka_bootstrap_servers}")
    logger.info(f"   Topic    : {config.kafka_topic_raw}")

    while True:
        try:
            logger.info("── Poll cycle starting ──")

            activity_count = process_activities(config, producer)
            logger.info(f"✅ Activities published: {activity_count}")

            review_count = process_reviews(config, producer)
            logger.info(f"✅ Reviews published: {review_count}")

        except Exception as e:
            logger.error(f"❌ Unexpected error in poll cycle: {e}", exc_info=True)

        logger.info(f"💤 Sleeping {config.poll_interval_seconds}s...")
        time.sleep(config.poll_interval_seconds)


if __name__ == "__main__":
    run()