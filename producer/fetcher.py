# ──────────────────────────────────────────────────────────────
# fetcher.py — AniList GraphQL API calls
# Pure functions only — no Kafka, no parsing, just fetching
# Exponential backoff handles rate limits (90 req/min)
# ──────────────────────────────────────────────────────────────
import time
import logging
from typing import Optional
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from config import Config

logger = logging.getLogger(__name__)

# ── GraphQL Queries ───────────────────────────────────────────

ACTIVITY_QUERY = """
query ($mediaId: Int!, $page: Int!) {
  Page(page: $page, perPage: 25) {
    activities(mediaId: $mediaId, type: TEXT, sort: ID_DESC) {
      ... on ListActivity {
        id
        type
        createdAt
        user {
          id
          name
        }
      }
      ... on TextActivity {
        id
        type
        text
        createdAt
        user {
          id
          name
        }
      }
    }
  }
}
"""

REVIEW_QUERY = """
query ($mediaId: Int!, $page: Int!) {
  Page(page: $page, perPage: 25) {
    reviews(mediaId: $mediaId, sort: CREATED_AT_DESC) {
      id
      summary
      body
      score
      rating
      createdAt
      user {
        id
        name
      }
      mediaId
    }
  }
}
"""


# ── Pure fetch functions ──────────────────────────────────────

def _post(url: str, query: str, variables: dict) -> dict:
    """Raw HTTP POST to AniList GraphQL endpoint."""
    response = httpx.post(
        url,
        json={"query": query, "variables": variables},
        timeout=30.0,
        headers={"Content-Type": "application/json"},
    )
    response.raise_for_status()
    return response.json()


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
def fetch_activities(config: Config, page: int = 1) -> list[dict]:
    """
    Fetch TEXT activities for the target media.
    Retries with exponential backoff on failure.
    Returns raw list of activity dicts.
    """
    data = _post(
        config.anilist_api_url,
        ACTIVITY_QUERY,
        {"mediaId": int(config.anilist_media_id), "page": page},
    )
    activities = data.get("data", {}).get("Page", {}).get("activities", [])
    logger.info(f"Fetched {len(activities)} activities (page {page})")
    return activities


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
def fetch_reviews(config: Config, page: int = 1) -> list[dict]:
    """
    Fetch reviews for the target media.
    Retries with exponential backoff on failure.
    Returns raw list of review dicts.
    """
    data = _post(
        config.anilist_api_url,
        REVIEW_QUERY,
        {"mediaId": int(config.anilist_media_id), "page": page},
    )
    reviews = data.get("data", {}).get("Page", {}).get("reviews", [])
    logger.info(f"Fetched {len(reviews)} reviews (page {page})")
    return reviews