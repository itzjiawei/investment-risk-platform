from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.schemas.requests import PortfolioComparisonRequest, StressTestRequest
from app.services.performance_service import (
    calculate_portfolio_value_duckdb,
    compare_analytics_engines,
)
from app.services.market_data_service import refresh_market_data
from app.services.dashboard_cache_service import (
    get_portfolio_dashboard_data,
    invalidate_portfolio_dashboard_cache,
)
from app.services.auth_service import (
    get_current_user,
    require_market_refresh_permission,
    require_pdf_export_permission,
)
from app.services.audit_service import create_audit_log
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


router = APIRouter(prefix="/api", dependencies=[Depends(get_current_user)])


@router.get("/portfolio/{portfolio_id}/value")
def get_portfolio_value(portfolio_id: int):
    return calculate_portfolio_value(portfolio_id)


@router.get("/portfolio/{portfolio_id}/risk")
def get_portfolio_risk(portfolio_id: int):
    return calculate_portfolio_risk(portfolio_id)


@router.get("/portfolio/{portfolio_id}/dashboard")
def get_portfolio_dashboard(portfolio_id: int):
    return get_portfolio_dashboard_data(portfolio_id)


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


@router.post("/portfolio/{portfolio_id}/market-data/refresh")
def refresh_portfolio_market_prices(
    portfolio_id: int,
    request: Request,
    current_user: dict = Depends(require_market_refresh_permission),
):
    result = refresh_market_data(portfolio_id=portfolio_id)
    invalidate_portfolio_dashboard_cache(portfolio_id)
    create_audit_log(
        action="market_data_refresh",
        status="success",
        user=current_user,
        request=request,
        resource_type="portfolio",
        resource_id=portfolio_id,
        metadata={
            "rows_inserted": result.get("rows_inserted"),
            "updated_tickers": result.get("updated_tickers"),
            "failed_tickers": result.get("failed_tickers"),
        },
    )
    return result


@router.get("/portfolio/{portfolio_id}/risk-report/pdf")
def download_risk_report_pdf(
    portfolio_id: int,
    request: Request,
    current_user: dict = Depends(require_pdf_export_permission),
):
    try:
        pdf_bytes = generate_pdf_risk_report(portfolio_id)
    except ValueError as exc:
        create_audit_log(
            action="pdf_report_export",
            status="failed",
            user=current_user,
            request=request,
            resource_type="portfolio",
            resource_id=portfolio_id,
            metadata={"reason": str(exc)},
        )
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    filename = f"portfolio-{portfolio_id}-risk-report.pdf"
    create_audit_log(
        action="pdf_report_export",
        status="success",
        user=current_user,
        request=request,
        resource_type="portfolio",
        resource_id=portfolio_id,
        metadata={"filename": filename},
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


@router.post("/portfolio/{portfolio_id}/stress-test")
def stress_test_portfolio(
    portfolio_id: int,
    stress_request: StressTestRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    result = run_custom_stress_test(
        portfolio_id,
        stress_request.shocks,
    )
    create_audit_log(
        action="stress_test",
        status="success",
        user=current_user,
        request=request,
        resource_type="portfolio",
        resource_id=portfolio_id,
        metadata={"shocks": stress_request.shocks},
    )
    return result


@router.get("/portfolio/{portfolio_id}/value-fast")
def get_portfolio_value_fast(portfolio_id: int):
    return calculate_portfolio_value_duckdb(portfolio_id)


@router.get("/portfolio/{portfolio_id}/engine-comparison")
def get_engine_comparison(portfolio_id: int):
    return compare_analytics_engines(portfolio_id)


@router.post("/portfolio/compare")
def compare_portfolio_metrics(
    comparison_request: PortfolioComparisonRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    result = compare_portfolios(comparison_request.portfolio_ids)
    create_audit_log(
        action="portfolio_comparison",
        status="success",
        user=current_user,
        request=request,
        resource_type="portfolio_comparison",
        resource_id=",".join(
            str(portfolio_id)
            for portfolio_id in comparison_request.portfolio_ids
        ),
        metadata={"portfolio_ids": comparison_request.portfolio_ids},
    )
    return result
