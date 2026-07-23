from fastapi import FastAPI

from app.api.routes import auth

app = FastAPI(title="Chatbot Platform API")

app.include_router(auth.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
