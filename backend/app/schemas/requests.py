from pydantic import BaseModel, Field


class StressTestRequest(BaseModel):
    shocks: dict[str, float]


class ChatMessage(BaseModel):
    role: str
    text: str


class AiQuestionRequest(BaseModel):
    question: str
    chat_history: list[ChatMessage] = Field(default_factory=list)


class PortfolioComparisonRequest(BaseModel):
    portfolio_ids: list[int]
