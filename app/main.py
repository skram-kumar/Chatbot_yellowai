from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, chat, projects, prompts
from app.core.config import settings

app = FastAPI(title="Chatbot Platform API")

# Frontend is served separately (frontend/, via a static file server) rather
# than from this app, so it talks to the API cross-origin. No cookies/session
# credentials are used (auth is a manually-attached Bearer header). Allowed
# origins default to the local dev static server; set ALLOWED_ORIGINS in .env
# to a comma-separated list including the real frontend URL once deployed.
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
