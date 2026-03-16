# ──────────────────────────────────────────────────────────────
# config.py — all settings in one place
# Read from environment variables (set in docker-compose.yml)
# ──────────────────────────────────────────────────────────────
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    # Kafka
    kafka_bootstrap_servers: str
    kafka_topic_raw: str
    kafka_topic_dlq: str

    # AniList
    anilist_media_id: str
    poll_interval_seconds: int

    # AniList API
    anilist_api_url: str = "https://graphql.anilist.co"

    # Retry settings (exponential backoff)
    max_retries: int = 5
    base_delay_seconds: float = 1.0


def load_config() -> Config:
    """Pure function — reads env vars and returns immutable Config."""
    return Config(
        kafka_bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
        kafka_topic_raw=os.getenv("KAFKA_TOPIC_RAW", "anilist.activity.raw"),
        kafka_topic_dlq=os.getenv("KAFKA_TOPIC_DLQ", "anilist.activity.dlq"),
        anilist_media_id=os.getenv("ANILIST_MEDIA_ID", "145064"),
        poll_interval_seconds=int(os.getenv("POLL_INTERVAL_SECONDS", "30")),
    )