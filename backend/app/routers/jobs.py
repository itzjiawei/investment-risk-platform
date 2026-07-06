from fastapi import APIRouter, Depends, Request

from app.services.auth_service import get_current_user, require_admin
from app.services.market_refresh_job_service import (
    get_jobs_status,
    run_market_refresh_job,
)


router = APIRouter(prefix="/api", tags=["jobs"])


@router.get("/jobs/status")
def jobs_status(_: dict = Depends(get_current_user)):
    return get_jobs_status()


@router.post("/jobs/market-refresh/run-now")
def run_market_refresh_now(
    request: Request,
    current_user: dict = Depends(require_admin),
):
    return run_market_refresh_job(
        triggered_by="admin_run_now",
        user=current_user,
        request=request,
    )
