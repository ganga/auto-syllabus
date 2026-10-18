# Auto-Syllabus

Auto-Syllabus turns a learning goal into a paced, personalized YouTube curriculum. A LangGraph workflow profiles the learner, maps lessons, curates videos, and loops back to revise lessons when the available videos do not fit the requested pace.

## Local development

Backend (Python 3.10+):

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Frontend (Node 20+):

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

The API runs in local demo mode when `LOCAL_DEMO_MODE=true`: authentication is replaced with a local development identity and deterministic sample video links are used when no YouTube key is configured. Turn demo mode off before deployment.

## Google Cloud setup

1. Create a Firebase project and enable Google authentication.
2. Create Firestore in Native mode and enable the YouTube Data API v3.
3. Deploy the API with a runtime service account that can call Vertex AI and Firestore.
4. Configure `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `YOUTUBE_API_KEY`, and `CORS_ORIGINS` on Cloud Run. Do not put the YouTube API key in the frontend.
5. Configure Firebase client variables in `frontend/.env` and deploy the built frontend to Firebase Hosting or another static host.

`GEMINI_MODEL` defaults to `gemini-2.5-flash`; set it to a Vertex model available to your project if needed. The workflow has a deterministic fallback so the app remains usable when Vertex credentials are absent locally.

YouTube `search.list` calls are limited to five per authenticated user per Pacific calendar day by default. Set `YOUTUBE_USER_DAILY_SEARCH_LIMIT` and `YOUTUBE_PROJECT_DAILY_SEARCH_LIMIT` on Cloud Run to tune the guardrail without exceeding the YouTube project quota.

## Recording the local demo

Keep `LOCAL_DEMO_MODE=true` in `backend/.env` and `VITE_LOCAL_DEMO_MODE=true` in `frontend/.env`. The frontend presents three preset scenarios: **Learn Gen AI / beginner**, **Learn guitar / intermediate**, and **Learn SFMC / advanced**. These use deterministic presentation fixtures and make no YouTube API requests. Set both flags to `false` for production; the curator then makes the authenticated, quota-protected YouTube API search.
