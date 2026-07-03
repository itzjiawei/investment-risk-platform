import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"


def ask_ollama(prompt: str, timeout: int = 120) -> str:
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

    data = response.json()
    return data.get("response", "")
