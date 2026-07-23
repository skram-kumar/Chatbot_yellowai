import httpx

from app.core.config import settings

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "llama-3.3-70b-versatile"
REQUEST_TIMEOUT = 30.0


class LLMServiceError(Exception):
    """Raised when the upstream LLM provider fails or returns something unusable."""


async def get_chat_completion(system_prompt: str, messages: list[dict[str, str]]) -> str:
    """Call Groq's OpenAI-compatible chat completions endpoint.

    `messages` is the prior conversation plus the new user message, each
    shaped as {"role": "user" | "assistant", "content": str}.
    """
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "system", "content": system_prompt}, *messages],
    }
    headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{GROQ_BASE_URL}/chat/completions", json=payload, headers=headers
            )
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise LLMServiceError("The AI service timed out") from exc
    except httpx.HTTPStatusError as exc:
        raise LLMServiceError(
            f"The AI service returned an error: {exc.response.status_code}"
        ) from exc
    except httpx.HTTPError as exc:
        raise LLMServiceError("Could not reach the AI service") from exc

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise LLMServiceError("The AI service returned an unexpected response") from exc
