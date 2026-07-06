from unittest.mock import Mock

import pytest

from app.services import market_refresh_job_service
from app.services.auth_service import create_access_token, hash_password


def _auth_headers_for_role(role: str, monkeypatch):
    user = {
        "user_id": 1,
        "email": f"{role}@example.com",
        "full_name": f"Demo {role}",
        "hashed_password": hash_password("password123"),
        "role": role,
        "is_active": True,
    }
    token = create_access_token(user["email"], role)
    monkeypatch.setattr(
        "app.services.auth_service.get_user_by_email",
        Mock(return_value=user),
    )
    return {"Authorization": f"Bearer {token}"}


def test_scheduler_config_parsing():
    assert market_refresh_job_service.parse_market_refresh_days(
        "mon,tue,wed,thu,fri"
    ) == "mon,tue,wed,thu,fri"
    assert market_refresh_job_service.parse_market_refresh_days(
        " Mon, FRI "
    ) == "mon,fri"


def test_scheduler_config_rejects_invalid_day():
    with pytest.raises(ValueError):
        market_refresh_job_service.parse_market_refresh_days("mon,funday")


def test_jobs_status_endpoint(client, monkeypatch):
    expected_response = {
        "scheduler_enabled": True,
        "scheduler_running": True,
        "schedule": {
            "days": "mon,tue,wed,thu,fri",
            "hour_utc": 22,
            "minute_utc": 0,
        },
        "registered_jobs": [
            {
                "id": "scheduled_market_data_refresh",
                "name": "Scheduled market data refresh",
                "next_run_time": "2026-07-06T22:00:00+00:00",
            }
        ],
        "last_run_status": "success",
        "last_run_summary": {
            "updated_tickers": ["AAPL"],
            "failed_tickers": [],
            "rows_inserted": 1,
            "message": "Market data refresh completed",
        },
        "last_run_started_at": "2026-07-06T21:59:00+00:00",
        "last_run_completed_at": "2026-07-06T22:00:00+00:00",
        "last_run_error": None,
    }
    monkeypatch.setattr(
        "app.routers.jobs.get_jobs_status",
        Mock(return_value=expected_response),
    )

    response = client.get("/api/jobs/status")

    assert response.status_code == 200
    assert response.json() == expected_response


def test_run_now_endpoint_requires_admin(unauthenticated_client, monkeypatch):
    response = unauthenticated_client.post(
        "/api/jobs/market-refresh/run-now",
        headers=_auth_headers_for_role("portfolio_manager", monkeypatch),
    )

    assert response.status_code == 403


def test_admin_can_run_market_refresh_now(unauthenticated_client, monkeypatch):
    expected_response = {
        "status": "success",
        "summary": {
            "updated_tickers": ["AAPL"],
            "failed_tickers": [],
            "rows_inserted": 1,
            "message": "Market data refresh completed",
        },
        "started_at": "2026-07-06T21:59:00+00:00",
        "completed_at": "2026-07-06T22:00:00+00:00",
        "error": None,
    }
    mocked_job = Mock(return_value=expected_response)
    monkeypatch.setattr(
        "app.routers.jobs.run_market_refresh_job",
        mocked_job,
    )

    response = unauthenticated_client.post(
        "/api/jobs/market-refresh/run-now",
        headers=_auth_headers_for_role("admin", monkeypatch),
    )

    assert response.status_code == 200
    assert response.json() == expected_response
    assert mocked_job.call_args.kwargs["triggered_by"] == "admin_run_now"


def test_scheduled_job_calls_market_refresh_and_invalidates_cache(monkeypatch):
    expected_summary = {
        "updated_tickers": ["AAPL"],
        "failed_tickers": [],
        "rows_inserted": 1,
        "message": "Market data refresh completed",
    }
    mocked_refresh = Mock(return_value=expected_summary)
    mocked_invalidate_cache = Mock()

    monkeypatch.setattr(
        market_refresh_job_service,
        "refresh_market_data",
        mocked_refresh,
    )
    monkeypatch.setattr(
        market_refresh_job_service,
        "invalidate_all_dashboard_cache",
        mocked_invalidate_cache,
    )
    monkeypatch.setattr(
        market_refresh_job_service,
        "create_audit_log",
        Mock(),
    )
    monkeypatch.setattr(
        market_refresh_job_service,
        "send_scheduled_daily_risk_reports",
        Mock(return_value=[]),
    )

    result = market_refresh_job_service.run_market_refresh_job()

    assert result["status"] == "success"
    assert result["summary"] == {
        **expected_summary,
        "email_notifications": [],
    }
    mocked_refresh.assert_called_once_with()
    mocked_invalidate_cache.assert_called_once_with()


def test_failed_ticker_does_not_crash_scheduled_job(monkeypatch):
    failed_summary = {
        "updated_tickers": [],
        "failed_tickers": [
            {
                "ticker": "BAD",
                "yfinance_ticker": "BAD",
                "reason": "No price data returned",
            }
        ],
        "rows_inserted": 0,
        "message": "Market data refresh completed",
    }
    monkeypatch.setattr(
        market_refresh_job_service,
        "refresh_market_data",
        Mock(return_value=failed_summary),
    )
    monkeypatch.setattr(
        market_refresh_job_service,
        "invalidate_all_dashboard_cache",
        Mock(),
    )
    monkeypatch.setattr(
        market_refresh_job_service,
        "create_audit_log",
        Mock(),
    )
    monkeypatch.setattr(
        market_refresh_job_service,
        "send_scheduled_daily_risk_reports",
        Mock(return_value=[]),
    )

    result = market_refresh_job_service.run_market_refresh_job()

    assert result["status"] == "success"
    assert result["summary"]["failed_tickers"][0]["ticker"] == "BAD"


def test_scheduled_job_includes_email_notification_results(monkeypatch):
    summary = {
        "updated_tickers": ["AAPL"],
        "failed_tickers": [],
        "rows_inserted": 1,
        "message": "Market data refresh completed",
    }
    email_results = [
        {
            "portfolio_id": 1,
            "recipient_email": "admin@example.com",
            "status": "success",
            "message": "Email sent",
        }
    ]
    mocked_email_flow = Mock(return_value=email_results)
    monkeypatch.setattr(
        market_refresh_job_service,
        "refresh_market_data",
        Mock(return_value=summary),
    )
    monkeypatch.setattr(
        market_refresh_job_service,
        "invalidate_all_dashboard_cache",
        Mock(),
    )
    monkeypatch.setattr(
        market_refresh_job_service,
        "create_audit_log",
        Mock(),
    )
    monkeypatch.setattr(
        market_refresh_job_service,
        "send_scheduled_daily_risk_reports",
        mocked_email_flow,
    )

    result = market_refresh_job_service.run_market_refresh_job()

    assert result["status"] == "success"
    assert result["summary"]["email_notifications"] == email_results
    mocked_email_flow.assert_called_once_with(summary)
