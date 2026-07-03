from fastapi import APIRouter

from app.schemas.requests import AiQuestionRequest, PortfolioComparisonRequest
from app.services.ai_analysis_service import (
    answer_ai_risk_question,
    generate_ai_portfolio_comparison,
    generate_ai_risk_summary,
)


router = APIRouter(prefix="/api")


@router.post("/portfolio/{portfolio_id}/ai-risk-summary")
def get_ai_risk_summary(portfolio_id: int):
    return generate_ai_risk_summary(portfolio_id)


@router.post("/portfolio/{portfolio_id}/ask-ai")
def ask_ai_risk_analyst(portfolio_id: int, request: AiQuestionRequest):
    return answer_ai_risk_question(
        portfolio_id,
        request.question,
        request.chat_history,
    )


@router.post("/portfolio/compare-ai")
def compare_portfolios_with_ai(request: PortfolioComparisonRequest):
    return generate_ai_portfolio_comparison(request.portfolio_ids)
