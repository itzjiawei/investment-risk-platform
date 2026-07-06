from datetime import datetime, timezone
import logging
from typing import Any

from fastapi import Request

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import (
    MARKET_REFRESH_DAYS,
    MARKET_REFRESH_ENABLED,
    MARKET_REFRESH_HOUR_UTC,
    MARKET_REFRESH_MINUTE_UTC,
)
from app.services.audit_service import create_audit_log
from app.services.dashboard_cache_service import invalidate_all_dashboard_cache
from app.services.market_data_service import refresh_market_data
from app.services.notification_service import send_scheduled_daily_risk_reports


logger = logging.getLogger(__name__)

MARKET_REFRESH_JOB_ID = "scheduled_market_data_refresh"
VALID_WEEKDAYS = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}

_scheduler: BackgroundScheduler | None = None
_last_run: dict[str, Any] = {
    "status": "never_run",
    "summary": None,
    "started_at": None,
    "completed_at": None,
    "error": None,
}


def parse_market_refresh_days(days: str) -> str:
    parsed_days = [
        day.strip().lower()
        for day in days.split(",")
        if day.strip()
    ]

    invalid_days = [day for day in parsed_days if day not in VALID_WEEKDAYS]
    if invalid_days:
        raise ValueError(
            f"Invalid MARKET_REFRESH_DAYS values: {', '.join(invalid_days)}"
        )

    if not parsed_days:
        raise ValueError("MARKET_REFRESH_DAYS must include at least one day")

    return ",".join(parsed_days)


def get_market_refresh_job_config() -> dict[str, Any]:
    return {
        "enabled": MARKET_REFRESH_ENABLED,
        "days": parse_market_refresh_days(MARKET_REFRESH_DAYS),
        "hour_utc": MARKET_REFRESH_HOUR_UTC,
        "minute_utc": MARKET_REFRESH_MINUTE_UTC,
    }


def run_market_refresh_job(
    triggered_by: str = "scheduler",
    user: dict | None = None,
    request: Request | None = None,
) -> dict[str, Any]:
    started_at = _utc_now()
    action = (
        "scheduled_market_data_refresh"
        if triggered_by == "scheduler"
        else "market_data_refresh_run_now"
    )

    try:
        summary = refresh_market_data()
        invalidate_all_dashboard_cache()
        email_results = send_scheduled_daily_risk_reports(summary)
        completed_at = _utc_now()
        summary_with_notifications = {
            **summary,
            "email_notifications": email_results,
        }
        _set_last_run(
            status="success",
            summary=summary_with_notifications,
            started_at=started_at,
            completed_at=completed_at,
            error=None,
        )
        create_audit_log(
            action=action,
            status="success",
            user=user,
            request=request,
            resource_type="market_data",
            resource_id="global",
            metadata={
                "triggered_by": triggered_by,
                "rows_inserted": summary.get("rows_inserted"),
                "updated_tickers": summary.get("updated_tickers"),
                "failed_tickers": summary.get("failed_tickers"),
                "email_notifications": email_results,
            },
        )
        return get_market_refresh_last_run()
    except Exception as exc:
        logger.exception("Scheduled market data refresh failed")
        completed_at = _utc_now()
        summary = {
            "updated_tickers": [],
            "failed_tickers": [],
            "rows_inserted": 0,
            "message": "Market data refresh failed",
        }
        _set_last_run(
            status="failed",
            summary=summary,
            started_at=started_at,
            completed_at=completed_at,
            error=str(exc),
        )
        create_audit_log(
            action=action,
            status="failed",
            user=user,
            request=request,
            resource_type="market_data",
            resource_id="global",
            metadata={
                "triggered_by": triggered_by,
                "error": str(exc),
            },
        )
        return get_market_refresh_last_run()


def start_market_refresh_scheduler() -> None:
    global _scheduler

    config = get_market_refresh_job_config()
    if not config["enabled"]:
        logger.info("Scheduled market refresh is disabled")
        return

    if _scheduler is not None and _scheduler.running:
        return

    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        run_market_refresh_job,
        CronTrigger(
            day_of_week=config["days"],
            hour=config["hour_utc"],
            minute=config["minute_utc"],
            timezone="UTC",
        ),
        id=MARKET_REFRESH_JOB_ID,
        name="Scheduled market data refresh",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info("Scheduled market refresh started")


def stop_market_refresh_scheduler() -> None:
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)

    _scheduler = None


def get_jobs_status() -> dict[str, Any]:
    config = get_market_refresh_job_config()
    scheduler_running = _scheduler is not None and _scheduler.running
    jobs = []

    if _scheduler is not None:
        for job in _scheduler.get_jobs():
            jobs.append(
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": (
                        job.next_run_time.isoformat()
                        if job.next_run_time is not None
                        else None
                    ),
                }
            )

    return {
        "scheduler_enabled": config["enabled"],
        "scheduler_running": scheduler_running,
        "schedule": {
            "days": config["days"],
            "hour_utc": config["hour_utc"],
            "minute_utc": config["minute_utc"],
        },
        "registered_jobs": jobs,
        "last_run_status": _last_run["status"],
        "last_run_summary": _last_run["summary"],
        "last_run_started_at": _last_run["started_at"],
        "last_run_completed_at": _last_run["completed_at"],
        "last_run_error": _last_run["error"],
    }


def get_market_refresh_last_run() -> dict[str, Any]:
    return {
        "status": _last_run["status"],
        "summary": _last_run["summary"],
        "started_at": _last_run["started_at"],
        "completed_at": _last_run["completed_at"],
        "error": _last_run["error"],
    }


def _set_last_run(
    status: str,
    summary: dict[str, Any] | None,
    started_at: str,
    completed_at: str,
    error: str | None,
) -> None:
    _last_run.update(
        {
            "status": status,
            "summary": summary,
            "started_at": started_at,
            "completed_at": completed_at,
            "error": error,
        }
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
