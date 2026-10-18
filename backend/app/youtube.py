from __future__ import annotations

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import get_settings
from .youtube_quota import YouTubeSearchLimitExceeded, reserve_search


def search_youtube(query: str, user_id: str, max_results: int = 5) -> list[dict]:
    """Return short, embeddable candidates for the curator agent."""
    settings = get_settings()
    if settings.local_demo_mode or not settings.youtube_api_key:
        return _demo_videos(query)

    reserve_search(user_id)
    youtube = build("youtube", "v3", developerKey=settings.youtube_api_key.strip())
    try:
        result = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            videoEmbeddable="true",
            maxResults=max_results,
            order="relevance",
        ).execute()
        ids = [item["id"]["videoId"] for item in result.get("items", [])]
        if not ids:
            return []
        details = youtube.videos().list(part="contentDetails,snippet", id=",".join(ids)).execute()
    except HttpError as exc:
        # Never relay provider URLs: they can contain the API key in query parameters.
        if exc.resp.status in {403, 429}:
            raise YouTubeSearchLimitExceeded("YouTube's daily search quota is currently exhausted. Please try again after midnight Pacific Time.") from exc
        raise
    return [
        {
            "video_id": item["id"],
            "title": item["snippet"]["title"],
            "channel": item["snippet"]["channelTitle"],
            "thumbnail": item["snippet"]["thumbnails"].get("medium", item["snippet"]["thumbnails"]["default"])["url"],
            "duration": item["contentDetails"]["duration"],
            "url": f"https://www.youtube.com/watch?v={item['id']}",
        }
        for item in details.get("items", [])
    ]


def _demo_videos(query: str) -> list[dict]:
    return [
        {
            "video_id": "aircAruvnKk",
            "title": f"{query}: a practical introduction",
            "channel": "Auto-Syllabus demo library",
            "thumbnail": "https://i.ytimg.com/vi/aircAruvnKk/mqdefault.jpg",
            "duration": "PT18M",
            "url": "https://www.youtube.com/watch?v=aircAruvnKk",
        }
    ]
