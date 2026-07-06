from fastapi import APIRouter, Depends, Request

from app.schemas.requests import AiQuestionRequest, PortfolioComparisonRequest
from app.services.auth_service import require_ai_permission
from app.services.audit_service import create_audit_log
from app.services.ai_analysis_service import (
    answer_ai_risk_question,
    generate_ai_portfolio_comparison,
    generate_ai_risk_summary,
)


router = APIRouter(prefix="/api", dependencies=[Depends(require_ai_permission)])


@router.post("/portfolio/{portfolio_id}/ai-risk-summary")
def get_ai_risk_summary(
    portfolio_id: int,
    request: Request,
    current_user: dict = Depends(require_ai_permission),
):
    result = generate_ai_risk_summary(portfolio_id)
    create_audit_log(
        action="ai_risk_summary",
        status="success",
        user=current_user,
        request=request,
        resource_type="portfolio",
        resource_id=portfolio_id,
    )
    return result


@router.post("/portfolio/{portfolio_id}/ask-ai")
def ask_ai_risk_analyst(
    portfolio_id: int,
    ai_request: AiQuestionRequest,
    request: Request,
    current_user: dict = Depends(require_ai_permission),
):
    result = answer_ai_risk_question(
        portfolio_id,
        ai_request.question,
        ai_request.chat_history,
    )
    create_audit_log(
        action="ai_question",
        status="success",
        user=current_user,
        request=request,
        resource_type="portfolio",
        resource_id=portfolio_id,
        metadata={
            "question_length": len(ai_request.question),
            "chat_history_count": len(ai_request.chat_history),
        },
    )
    return result


@router.post("/portfolio/compare-ai")
def compare_portfolios_with_ai(
    comparison_request: PortfolioComparisonRequest,
    request: Request,
    current_user: dict = Depends(require_ai_permission),
):
    result = generate_ai_portfolio_comparison(comparison_request.portfolio_ids)
    create_audit_log(
        action="ai_portfolio_comparison",
        status="success",
        user=current_user,
        request=request,
        resource_type="portfolio_comparison",
        resource_id=",".join(str(id_) for id_ in comparison_request.portfolio_ids),
        metadata={"portfolio_ids": comparison_request.portfolio_ids},
    )
    return result
