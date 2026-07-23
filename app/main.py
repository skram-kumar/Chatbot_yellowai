from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, chat, projects, prompts

app = FastAPI(title="Chatbot Platform API")

# Frontend is served separately (frontend/, via a static file server) rather
# than from this app, so it talks to the API cross-origin. No cookies/session
# credentials are used (auth is a manually-attached Bearer header), so a
# wildcard origin is safe here; narrow this to the real frontend origin
# before deploying anywhere non-local.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
