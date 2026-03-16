# ──────────────────────────────────────────────────────────────
# models.py — Pydantic V2 schemas
# Validates raw AniList API responses before they hit Kafka
# ──────────────────────────────────────────────────────────────
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class AniListUser(BaseModel):
    id: int
    name: str


class ActivityEvent(BaseModel):
    """Represents a TEXT activity on AniList (comment/status)."""
    id: int
    type: str
    text: str
    created_at: int
    user: AniListUser
    media_id: Optional[int] = None

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("text must not be empty")
        return v.strip()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "text": self.text,
            "created_at": self.created_at,
            "user_id": self.user.id,
            "user_name": self.user.name,
            "media_id": self.media_id,
            "ingested_at": int(datetime.utcnow().timestamp()),
            "source": "activity",
        }


class ReviewEvent(BaseModel):
    """Represents a Review on AniList."""
    id: int
    summary: str
    body: str
    score: int
    rating: int
    created_at: int
    user: AniListUser
    media_id: Optional[int] = None

    @field_validator("score")
    @classmethod
    def score_must_be_valid(cls, v: int) -> int:
        if not (0 <= v <= 100):
            raise ValueError(f"score must be between 0 and 100, got {v}")
        return v

    @field_validator("body")
    @classmethod
    def body_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("body must not be empty")
        return v.strip()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "summary": self.summary,
            "body": self.body,
            "score": self.score,
            "rating": self.rating,
            "created_at": self.created_at,
            "user_id": self.user.id,
            "user_name": self.user.name,
            "media_id": self.media_id,
            "ingested_at": int(datetime.utcnow().timestamp()),
            "source": "review",
        }