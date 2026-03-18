# ──────────────────────────────────────────────────────────────
# sentiment_job.py — PyFlink Sentiment Processing Job
# Reads from Kafka → VADER sentiment → writes to Kafka + MinIO
# ──────────────────────────────────────────────────────────────
import json
import logging
from datetime import datetime

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import (
    KafkaSource,
    KafkaSink,
    KafkaRecordSerializationSchema,
    DeliveryGuarantee,
)
from pyflink.datastream.formats.json import JsonRowDeserializationSchema
from pyflink.common import WatermarkStrategy, SimpleStringSchema, Types
from pyflink.common.serialization import SimpleStringSchema
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────
KAFKA_BROKERS = "kafka:9092"
TOPIC_RAW = "anilist.activity.raw"
TOPIC_ENRICHED = "anilist.activity.enriched"


# ── Pure Functions ────────────────────────────────────────────

def get_text(message: dict) -> str:
    """
    Pure function — extracts the correct text field
    based on message source type.
    Reviews use 'body', activities use 'text'.
    """
    if message.get("source") == "review":
        return message.get("body", "")
    return message.get("text", "")


def analyze_sentiment(text: str) -> dict:
    """
    Pure function — runs VADER on text.
    Returns all 4 scores: compound, pos, neg, neu.
    No side effects.
    """
    analyzer = SentimentIntensityAnalyzer()
    scores = analyzer.polarity_scores(text)
    return scores


def get_sentiment_label(compound: float) -> str:
    """
    Pure function — converts compound score to human readable label.
    VADER standard thresholds:
      >= 0.05  → positive
      <= -0.05 → negative
      else     → neutral
    """
    if compound >= 0.05:
        return "positive"
    elif compound <= -0.05:
        return "negative"
    return "neutral"


def enrich_message(raw_json: str) -> str:
    """
    Pure function — takes a raw JSON string, adds sentiment columns,
    returns enriched JSON string.
    This is the main .map() function.
    """
    try:
        message = json.loads(raw_json)

        # Get correct text field based on source
        text = get_text(message)

        if not text or not text.strip():
            # No text to analyze — return as-is with neutral sentiment
            message["sentiment_score"] = 0.0
            message["sentiment_label"] = "neutral"
            message["sentiment_pos"] = 0.0
            message["sentiment_neg"] = 0.0
            message["sentiment_neu"] = 1.0
            message["text_length"] = 0
            return json.dumps(message)

        # Run VADER
        scores = analyze_sentiment(text)

        # Add enriched columns
        message["sentiment_score"] = round(scores["compound"], 4)
        message["sentiment_label"] = get_sentiment_label(scores["compound"])
        message["sentiment_pos"]   = round(scores["pos"], 4)
        message["sentiment_neg"]   = round(scores["neg"], 4)
        message["sentiment_neu"]   = round(scores["neu"], 4)
        message["text_length"]     = len(text)

        return json.dumps(message)

    except Exception as e:
        logger.error(f"Failed to enrich message: {e}")
        return raw_json  # return original if enrichment fails


# ── Flink Job ─────────────────────────────────────────────────

def main():
    # Set up Flink environment
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(2)

    # ── Kafka Source ──────────────────────────────────────────
    kafka_source = KafkaSource.builder() \
        .set_bootstrap_servers(KAFKA_BROKERS) \
        .set_topics(TOPIC_RAW) \
        .set_group_id("flink-sentiment-consumer") \
        .set_value_only_deserializer(SimpleStringSchema()) \
        .build()

    # Read stream from Kafka
    raw_stream = env.from_source(
        kafka_source,
        WatermarkStrategy.no_watermarks(),
        "Kafka Raw Source"
    )

    # ── Sentiment Enrichment (.map) ───────────────────────────
    enriched_stream = raw_stream.map(
        enrich_message,
        output_type=Types.STRING()
    )

    # ── Kafka Sink (enriched topic) ───────────────────────────
    kafka_sink = KafkaSink.builder() \
        .set_bootstrap_servers(KAFKA_BROKERS) \
        .set_record_serializer(
            KafkaRecordSerializationSchema.builder()
                .set_topic(TOPIC_ENRICHED)
                .set_value_serialization_schema(SimpleStringSchema())
                .build()
        ) \
        .set_delivery_guarantee(DeliveryGuarantee.AT_LEAST_ONCE) \
        .build()

    enriched_stream.sink_to(kafka_sink)

    # ── Execute ───────────────────────────────────────────────
    logger.info("🚀 Starting Sentiment Job...")
    env.execute("Anime Sentiment Job")


if __name__ == "__main__":
    main()