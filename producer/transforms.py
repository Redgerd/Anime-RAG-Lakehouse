# ──────────────────────────────────────────────────────────────
# transforms.py — pure functions only
# No API calls, no Kafka. Just data in → data out.
# This is the heart of the Functional Programming approach.
# ──────────────────────────────────────────────────────────────
import json
import logging
from typing import Optional
from pydantic import ValidationError
from models import ActivityEvent, ReviewEvent, AniListUser

logger = logging.getLogger(__name__)


# ── Activity transforms ───────────────────────────────────────

def parse_activity(raw: dict) -> Optional[ActivityEvent]:
    """
    Pure function — takes a raw API dict, returns a validated
    ActivityEvent or None if invalid.
    No side effects.
    """
    try:
        # AniList returns different activity types — we only want TEXT
        if raw.get("type") not in ("TEXT", "ANIME_LIST", "MANGA_LIST"):
            return None

        # Some activity types don't have text
        text = raw.get("text", "")
        if not text:
            return None

        user_raw = raw.get("user", {})

        return ActivityEvent(
            id=raw["id"],
            type=raw["type"],
            text=text,
            created_at=raw["createdAt"],
            user=AniListUser(
                id=user_raw["id"],
                name=user_raw["name"],
            ),
            media_id=raw.get("mediaId"),
        )
    except (ValidationError, KeyError, TypeError) as e:
        logger.warning(f"Failed to parse activity {raw.get('id')}: {e}")
        return None


def parse_activities(raw_list: list[dict]) -> list[ActivityEvent]:
    """
    Pure function — maps parse_activity over a list.
    Filters out None values (invalid records).
    """
    return [
        event
        for raw in raw_list
        if (event := parse_activity(raw)) is not None
    ]


# ── Review transforms ─────────────────────────────────────────

def parse_review(raw: dict) -> Optional[ReviewEvent]:
    """
    Pure function — takes a raw API dict, returns a validated
    ReviewEvent or None if invalid.
    """
    try:
        user_raw = raw.get("user", {})

        return ReviewEvent(
            id=raw["id"],
            summary=raw.get("summary", ""),
            body=raw["body"],
            score=raw["score"],
            rating=raw.get("rating", 0),
            created_at=raw["createdAt"],
            user=AniListUser(
                id=user_raw["id"],
                name=user_raw["name"],
            ),
            media_id=raw.get("mediaId"),
        )
    except (ValidationError, KeyError, TypeError) as e:
        logger.warning(f"Failed to parse review {raw.get('id')}: {e}")
        return None


def parse_reviews(raw_list: list[dict]) -> list[ReviewEvent]:
    """
    Pure function — maps parse_review over a list.
    Filters out None values (invalid records).
    """
    return [
        event
        for raw in raw_list
        if (event := parse_review(raw)) is not None
    ]


# ── Serialization ─────────────────────────────────────────────

def serialize(event: ActivityEvent | ReviewEvent) -> bytes:
    """
    Pure function — converts a validated event to JSON bytes
    ready to be sent to Kafka.
    """
    return json.dumps(event.to_dict()).encode("utf-8")


def serialize_error(raw: dict, error: str) -> bytes:
    """
    Pure function — wraps a failed record + error message
    into bytes for the Dead Letter Queue.
    """
    return json.dumps({
        "raw": raw,
        "error": error,
    }).encode("utf-8")