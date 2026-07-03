from fastapi import APIRouter, HTTPException, Response

from app.schemas.requests import PortfolioComparisonRequest, StressTestRequest
from app.services.performance_service import (
    calculate_portfolio_value_duckdb,
    compare_analytics_engines,
)
from app.services.pdf_report_service import generate_pdf_risk_report
from app.services.portfolio_service import (
    calculate_portfolio_holdings,
    calculate_portfolio_returns,
    calculate_portfolio_risk,
    calculate_portfolio_value,
    calculate_risk_contribution,
    calculate_sector_exposure,
    compare_portfolios,
    run_custom_stress_test,
)


router = APIRouter(prefix="/api")


@router.get("/portfolio/{portfolio_id}/value")
def get_portfolio_value(portfolio_id: int):
    return calculate_portfolio_value(portfolio_id)


@router.get("/portfolio/{portfolio_id}/risk")
def get_portfolio_risk(portfolio_id: int):
    return calculate_portfolio_risk(portfolio_id)


@router.get("/portfolio/{portfolio_id}/returns")
def get_portfolio_returns(portfolio_id: int):
    return calculate_portfolio_returns(portfolio_id)


@router.get("/portfolio/{portfolio_id}/holdings")
def get_portfolio_holdings(portfolio_id: int):
    return calculate_portfolio_holdings(portfolio_id)


@router.get("/portfolio/{portfolio_id}/sector-exposure")
def get_sector_exposure(portfolio_id: int):
    return calculate_sector_exposure(portfolio_id)


@router.get("/portfolio/{portfolio_id}/risk-contribution")
def get_risk_contribution(portfolio_id: int):
    return calculate_risk_contribution(portfolio_id)


@router.get("/portfolio/{portfolio_id}/risk-report/pdf")
def download_risk_report_pdf(portfolio_id: int):
    try:
        pdf_bytes = generate_pdf_risk_report(portfolio_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    filename = f"portfolio-{portfolio_id}-risk-report.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


@router.post("/portfolio/{portfolio_id}/stress-test")
def stress_test_portfolio(portfolio_id: int, request: StressTestRequest):
    return run_custom_stress_test(
        portfolio_id,
        request.shocks,
    )


@router.get("/portfolio/{portfolio_id}/value-fast")
def get_portfolio_value_fast(portfolio_id: int):
    return calculate_portfolio_value_duckdb(portfolio_id)


@router.get("/portfolio/{portfolio_id}/engine-comparison")
def get_engine_comparison(portfolio_id: int):
    return compare_analytics_engines(portfolio_id)


@router.post("/portfolio/compare")
def compare_portfolio_metrics(request: PortfolioComparisonRequest):
    return compare_portfolios(request.portfolio_ids)
