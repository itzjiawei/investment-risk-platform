import requests

from app.config import OLLAMA_MODEL, OLLAMA_URL

MODEL_NAME = OLLAMA_MODEL
AI_UNAVAILABLE_MESSAGE = (
    "AI analysis is currently unavailable because the Ollama service could not be reached. "
    "Portfolio analytics are still available, and AI features will work again when Ollama is running."
)


def ask_ollama(prompt: str, timeout: int = 120) -> str:
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
            },
            timeout=timeout,
        )

        response.raise_for_status()
    except requests.RequestException:
        return AI_UNAVAILABLE_MESSAGE

    try:
        data = response.json()
    except ValueError:
        return AI_UNAVAILABLE_MESSAGE

    return data.get("response", "") or AI_UNAVAILABLE_MESSAGE
