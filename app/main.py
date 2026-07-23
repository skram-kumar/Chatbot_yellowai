from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import auth, chat, projects, prompts
from app.core.config import settings

app = FastAPI(title="Chatbot Platform API")

# The frontend is normally served by this same app (mounted at "/" below), so
# API calls from it are same-origin and don't need CORS at all. This stays
# in place for the case where frontend/ is instead served separately (e.g. a
# static host, or `python -m http.server` during frontend-only development).
# Set ALLOWED_ORIGINS in .env to a comma-separated list if that origin isn't
# one of the defaults.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(prompts.router)
app.include_router(chat.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


# Mounted last and at "/" so it only catches requests that don't match one of
# the API routes registered above — Starlette matches routes in registration
# order, and a Mount at "/" would otherwise shadow everything after it.
# Resolved from __file__ (not cwd) so it's correct no matter what directory
# the production start command launches uvicorn from.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
