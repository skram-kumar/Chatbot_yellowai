from fastapi import FastAPI

from app.api.routes import auth, chat, projects, prompts

app = FastAPI(title="Chatbot Platform API")

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(prompts.router)
app.include_router(chat.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
