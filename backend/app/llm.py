"""Small Vertex AI JSON adapter with an offline-safe fallback."""
from __future__ import annotations

import json
from typing import Any

from .config import get_settings


def vertex_json(prompt: str, fallback: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    if not settings.google_cloud_project:
        return fallback
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(vertexai=True, project=settings.google_cloud_project, location=settings.google_cloud_location)
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.3),
        )
        parsed = json.loads(response.text)
        return parsed if isinstance(parsed, dict) else fallback
    except Exception:
        # Generation must not prevent a user from receiving a plan; production logs
        # should capture this through Cloud Run's structured request logs.
        return fallback
