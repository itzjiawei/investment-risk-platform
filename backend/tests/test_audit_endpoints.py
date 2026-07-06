from unittest.mock import Mock

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


def test_audit_log_created_on_successful_login(unauthenticated_client, monkeypatch):
    mocked_user = {
        "user_id": 1,
        "email": "admin@example.com",
        "full_name": "Demo Admin",
        "hashed_password": "not-used",
        "role": "admin",
        "is_active": True,
    }
    mocked_audit = Mock()
    monkeypatch.setattr(
        "app.routers.auth.authenticate_user",
        Mock(return_value=mocked_user),
    )
    monkeypatch.setattr("app.routers.auth.create_audit_log", mocked_audit)

    response = unauthenticated_client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "admin123"},
    )

    assert response.status_code == 200
    mocked_audit.assert_called_once()
    assert mocked_audit.call_args.kwargs["action"] == "login"
    assert mocked_audit.call_args.kwargs["status"] == "success"
    assert mocked_audit.call_args.kwargs["user"] == mocked_user


def test_audit_log_created_on_pdf_export(unauthenticated_client, monkeypatch):
    mocked_audit = Mock()
    monkeypatch.setattr(
        "app.routers.portfolio.generate_pdf_risk_report",
        Mock(return_value=b"%PDF-1.4 test"),
    )
    monkeypatch.setattr("app.routers.portfolio.create_audit_log", mocked_audit)

    response = unauthenticated_client.get(
        "/api/portfolio/1/risk-report/pdf",
        headers=_auth_headers_for_role("analyst", monkeypatch),
    )

    assert response.status_code == 200
    mocked_audit.assert_called_once()
    assert mocked_audit.call_args.kwargs["action"] == "pdf_report_export"
    assert mocked_audit.call_args.kwargs["resource_id"] == 1
    assert mocked_audit.call_args.kwargs["status"] == "success"


def test_audit_log_created_on_market_refresh(unauthenticated_client, monkeypatch):
    mocked_audit = Mock()
    monkeypatch.setattr(
        "app.routers.market_data.refresh_market_data",
        Mock(
            return_value={
                "updated_tickers": ["AAPL"],
                "failed_tickers": [],
                "rows_inserted": 1,
                "message": "Market data refresh completed",
            }
        ),
    )
    monkeypatch.setattr("app.routers.market_data.create_audit_log", mocked_audit)

    response = unauthenticated_client.post(
        "/api/market-data/refresh",
        headers=_auth_headers_for_role("admin", monkeypatch),
    )

    assert response.status_code == 200
    mocked_audit.assert_called_once()
    assert mocked_audit.call_args.kwargs["action"] == "market_data_refresh"
    assert mocked_audit.call_args.kwargs["resource_id"] == "global"
    assert mocked_audit.call_args.kwargs["metadata"]["rows_inserted"] == 1


def test_non_admin_cannot_view_audit_logs(unauthenticated_client, monkeypatch):
    monkeypatch.setattr("app.services.auth_service.create_audit_log", Mock())

    response = unauthenticated_client.get(
        "/api/audit-logs",
        headers=_auth_headers_for_role("portfolio_manager", monkeypatch),
    )

    assert response.status_code == 403


def test_admin_can_view_audit_logs(unauthenticated_client, monkeypatch):
    expected_logs = [
        {
            "id": 1,
            "user_id": 1,
            "user_email": "admin@example.com",
            "user_role": "admin",
            "action": "login",
            "resource_type": "auth",
            "resource_id": "admin@example.com",
            "status": "success",
            "ip_address": "127.0.0.1",
            "user_agent": "pytest",
            "metadata": "{}",
            "created_at": "2026-07-06T03:11:00",
        }
    ]
    mocked_get_logs = Mock(return_value=expected_logs)
    monkeypatch.setattr("app.routers.audit.get_audit_logs", mocked_get_logs)

    response = unauthenticated_client.get(
        "/api/audit-logs?limit=50&action=login",
        headers=_auth_headers_for_role("admin", monkeypatch),
    )

    assert response.status_code == 200
    assert response.json() == expected_logs
    mocked_get_logs.assert_called_once_with(
        action="login",
        user_email=None,
        resource_type=None,
        status=None,
        limit=50,
    )
