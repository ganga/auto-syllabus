"""Job persistence with an in-memory local-development fallback."""
from __future__ import annotations

from typing import Any

from .config import get_settings


class JobStore:
    def __init__(self) -> None:
        self._memory: dict[str, dict[str, Any]] = {}
        self._client = None

    def _firestore(self):
        settings = get_settings()
        if settings.local_demo_mode:
            return None
        if self._client is None:
            from google.cloud import firestore

            self._client = firestore.Client(project=settings.google_cloud_project or None)
        return self._client

    def create(self, job: dict[str, Any]) -> None:
        client = self._firestore()
        if client:
            client.collection("curriculum_jobs").document(job["jobId"]).set(job)
        else:
            self._memory[job["jobId"]] = job.copy()

    def update(self, job_id: str, values: dict[str, Any]) -> None:
        client = self._firestore()
        if client:
            client.collection("curriculum_jobs").document(job_id).update(values)
        elif job_id in self._memory:
            self._memory[job_id].update(values)

    def get(self, job_id: str) -> dict[str, Any] | None:
        client = self._firestore()
        if client:
            snapshot = client.collection("curriculum_jobs").document(job_id).get()
            return snapshot.to_dict() if snapshot.exists else None
        return self._memory.get(job_id)
