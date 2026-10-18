"""Firestore-backed, Pacific-time daily YouTube search limits."""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from google.cloud import firestore

from .config import get_settings


class YouTubeSearchLimitExceeded(Exception):
    """The caller or project has exhausted the configured search allowance."""


def reserve_search(user_id: str) -> None:
    """Atomically reserve one search.list call before calling YouTube."""
    settings = get_settings()
    if settings.local_demo_mode:
        return
    day = datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
    client = firestore.Client(project=settings.google_cloud_project or None)
    day_ref = client.collection("youtube_quota_days").document(day)
    user_ref = day_ref.collection("users").document(user_id)
    transaction = client.transaction()

    @firestore.transactional
    def reserve(transaction):
        day_snapshot = day_ref.get(transaction=transaction)
        user_snapshot = user_ref.get(transaction=transaction)
        project_searches = day_snapshot.to_dict().get("searches", 0) if day_snapshot.exists else 0
        user_searches = user_snapshot.to_dict().get("searches", 0) if user_snapshot.exists else 0
        if project_searches >= settings.youtube_project_daily_search_limit:
            raise YouTubeSearchLimitExceeded("The service has reached its daily YouTube search allowance. Please try again after midnight Pacific Time.")
        if user_searches >= settings.youtube_user_daily_search_limit:
            raise YouTubeSearchLimitExceeded("You have reached today's video-search limit. Please try again after midnight Pacific Time.")
        transaction.set(day_ref, {"searches": project_searches + 1, "updated_at": datetime.now(timezone.utc).isoformat()}, merge=True)
        transaction.set(user_ref, {"searches": user_searches + 1, "updated_at": datetime.now(timezone.utc).isoformat()}, merge=True)

    reserve(transaction)
