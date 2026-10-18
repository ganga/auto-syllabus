from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import firebase_admin
from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth
from pydantic import BaseModel, Field

from .config import get_settings
from .job_store import JobStore
from .workflow import workflow
from .youtube_quota import YouTubeSearchLimitExceeded

settings = get_settings()
app = FastAPI(title="Auto-Syllabus Vertex AI Multi-Agent API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
job_store = JobStore()
bearer_auth = HTTPBearer(auto_error=False, scheme_name="BearerAuth")


class GenerateRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=160)
    timeframe_days: int = Field(ge=1, le=30)
    current_skill_level: str = Field(pattern="^(beginner|intermediate|advanced)$")


class RefineRequest(BaseModel):
    message: str = Field(min_length=3, max_length=800)


def current_user(credentials: HTTPAuthorizationCredentials | None = Security(bearer_auth)) -> str:
    if settings.local_demo_mode:
        return "local-demo-user"
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
    try:
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        return auth.verify_id_token(credentials.credentials)["uid"]
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Firebase token") from exc


async def run_job(job_id: str, request: GenerateRequest, user_id: str) -> None:
    await asyncio.to_thread(job_store.update, job_id, {"status": "processing", "current_agent": "Learner Profiler", "message": "Understanding your learning goal"})
    try:
        result = await asyncio.to_thread(workflow.invoke, request.model_dump() | {"feedback_attempts": 0, "user_id": user_id})
        await asyncio.to_thread(job_store.update, job_id, {"status": "completed", "current_agent": "Lesson Planner", "message": "Your curriculum is ready", "result": result["result"]})
    except YouTubeSearchLimitExceeded as exc:
        await asyncio.to_thread(job_store.update, job_id, {"status": "failed", "current_agent": "Video Curator", "message": str(exc)})
    except Exception as exc:
        await asyncio.to_thread(job_store.update, job_id, {"status": "failed", "current_agent": "", "message": str(exc)})


async def run_refinement(job_id: str, request: GenerateRequest, message: str, conversation: list[dict], user_id: str) -> None:
    await asyncio.to_thread(job_store.update, job_id, {"status": "processing", "current_agent": "Learner Profiler", "message": "Applying your additional context", "conversation": conversation})
    try:
        enriched = request.model_copy(update={"topic": f"{request.topic}. Additional learner context: {message}"})
        result = await asyncio.to_thread(workflow.invoke, enriched.model_dump() | {"feedback_attempts": 0, "user_id": user_id})
        conversation.append({"role": "assistant", "content": "I updated the plan using your additional context."})
        await asyncio.to_thread(job_store.update, job_id, {"status": "completed", "current_agent": "Lesson Planner", "message": "Your updated curriculum is ready", "result": result["result"], "conversation": conversation})
    except YouTubeSearchLimitExceeded as exc:
        await asyncio.to_thread(job_store.update, job_id, {"status": "failed", "current_agent": "Video Curator", "message": str(exc), "conversation": conversation})
    except Exception as exc:
        await asyncio.to_thread(job_store.update, job_id, {"status": "failed", "current_agent": "", "message": str(exc), "conversation": conversation})


@app.post("/curriculum/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_curriculum(request: GenerateRequest, user_id: str = Depends(current_user)) -> dict:
    job_id = str(uuid4())
    await asyncio.to_thread(job_store.create, {"jobId": job_id, "status": "processing", "current_agent": "Queued", "message": "Starting curriculum generation", "user_id": user_id, "created_at": datetime.now(timezone.utc).isoformat(), "request": request.model_dump(), "conversation": []})
    asyncio.create_task(run_job(job_id, request, user_id))
    return {"jobId": job_id}


@app.get("/curriculum/job/{job_id}")
async def get_job(job_id: str, user_id: str = Depends(current_user)) -> dict:
    job = await asyncio.to_thread(job_store.get, job_id)
    if not job or job["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return {key: value for key, value in job.items() if key != "user_id"}


@app.post("/curriculum/job/{job_id}/refine", status_code=status.HTTP_202_ACCEPTED)
async def refine_curriculum(job_id: str, refinement: RefineRequest, user_id: str = Depends(current_user)) -> dict:
    job = await asyncio.to_thread(job_store.get, job_id)
    if not job or job["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.get("status") == "processing":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This curriculum is still being generated")
    request = GenerateRequest.model_validate(job["request"])
    conversation = [*job.get("conversation", []), {"role": "user", "content": refinement.message}]
    asyncio.create_task(run_refinement(job_id, request, refinement.message, conversation, user_id))
    return {"jobId": job_id}


@app.get("/healthz")
async def healthz() -> dict:
    return {"ok": True}
