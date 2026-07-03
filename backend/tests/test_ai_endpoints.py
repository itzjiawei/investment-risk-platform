from unittest.mock import Mock

import requests

from app.services.ollama_service import AI_UNAVAILABLE_MESSAGE, ask_ollama


MOCK_AI_RESPONSE = "Mock AI response"


def test_post_ai_risk_summary(client, monkeypatch):
    expected_response = {
        "portfolio_id": 1,
        "summary": MOCK_AI_RESPONSE,
    }
    mocked_service = Mock(return_value=expected_response)
    monkeypatch.setattr(
        "app.routers.ai.generate_ai_risk_summary",
        mocked_service,
    )

    response = client.post("/api/portfolio/1/ai-risk-summary")

    assert response.status_code == 200
    data = response.json()
    assert data == expected_response
    assert {"portfolio_id", "summary"} <= data.keys()
    assert data["summary"] == MOCK_AI_RESPONSE
    mocked_service.assert_called_once_with(1)


def test_post_ask_ai(client, monkeypatch):
    expected_response = {
        "portfolio_id": 1,
        "question": "What is the biggest concentration risk?",
        "answer": MOCK_AI_RESPONSE,
    }
    mocked_service = Mock(return_value=expected_response)
    monkeypatch.setattr(
        "app.routers.ai.answer_ai_risk_question",
        mocked_service,
    )

    payload = {
        "question": "What is the biggest concentration risk?",
        "chat_history": [
            {
                "role": "user",
                "text": "Summarize the portfolio first.",
            }
        ],
    }
    response = client.post("/api/portfolio/1/ask-ai", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data == expected_response
    assert {"portfolio_id", "question", "answer"} <= data.keys()
    assert data["answer"] == MOCK_AI_RESPONSE
    mocked_service.assert_called_once()
    call_args = mocked_service.call_args.args
    assert call_args[0] == 1
    assert call_args[1] == payload["question"]
    assert len(call_args[2]) == 1
    assert call_args[2][0].role == "user"
    assert call_args[2][0].text == "Summarize the portfolio first."


def test_post_compare_ai(client, monkeypatch, comparison_response):
    expected_response = {
        "portfolio_ids": [1, 2],
        "comparison": comparison_response,
        "summary": MOCK_AI_RESPONSE,
    }
    mocked_service = Mock(return_value=expected_response)
    monkeypatch.setattr(
        "app.routers.ai.generate_ai_portfolio_comparison",
        mocked_service,
    )

    payload = {"portfolio_ids": [1, 2]}
    response = client.post("/api/portfolio/compare-ai", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data == expected_response
    assert {"portfolio_ids", "comparison", "summary"} <= data.keys()
    assert isinstance(data["comparison"], list)
    assert data["summary"] == MOCK_AI_RESPONSE
    mocked_service.assert_called_once_with(payload["portfolio_ids"])


def test_ollama_unavailable_returns_fallback_message(monkeypatch):
    def raise_connection_error(*args, **kwargs):
        raise requests.ConnectionError("Ollama is not running")

    monkeypatch.setattr(
        "app.services.ollama_service.requests.post",
        raise_connection_error,
    )

    response = ask_ollama("Summarize portfolio risk")

    assert response == AI_UNAVAILABLE_MESSAGE
