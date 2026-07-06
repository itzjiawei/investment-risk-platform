from unittest.mock import Mock

from app.services.auth_service import create_access_token, hash_password
from app.services.notification_service import NotificationError, NotificationResult


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


def test_admin_can_send_report(unauthenticated_client, monkeypatch):
    mocked_service = Mock()
    mocked_service.return_value.send_portfolio_risk_report.return_value = (
        NotificationResult(
            success=True,
            message="Email sent",
            provider_message_id="message-123",
        )
    )
    monkeypatch.setattr(
        "app.routers.notifications.NotificationService",
        mocked_service,
    )

    response = unauthenticated_client.post(
        "/api/notifications/send-report",
        headers=_auth_headers_for_role("admin", monkeypatch),
        json={
            "portfolio_id": 1,
            "recipient_email": "admin@example.com",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "Email sent",
        "provider_message_id": "message-123",
    }


def test_non_admin_cannot_send_report(unauthenticated_client, monkeypatch):
    response = unauthenticated_client.post(
        "/api/notifications/send-report",
        headers=_auth_headers_for_role("portfolio_manager", monkeypatch),
        json={
            "portfolio_id": 1,
            "recipient_email": "admin@example.com",
        },
    )

    assert response.status_code == 403


def test_send_report_returns_error_when_provider_fails(
    unauthenticated_client,
    monkeypatch,
):
    mocked_service = Mock()
    mocked_service.return_value.send_portfolio_risk_report.side_effect = (
        NotificationError("Notification provider failed")
    )
    monkeypatch.setattr(
        "app.routers.notifications.NotificationService",
        mocked_service,
    )

    response = unauthenticated_client.post(
        "/api/notifications/send-report",
        headers=_auth_headers_for_role("admin", monkeypatch),
        json={
            "portfolio_id": 1,
            "recipient_email": "admin@example.com",
        },
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "Notification provider failed"
