from unittest.mock import Mock

from app.services import auth_service
from app.services.auth_service import create_access_token, hash_password


def _user_for_role(role: str):
    return {
        "user_id": 1,
        "email": f"{role}@example.com",
        "full_name": f"Demo {role}",
        "hashed_password": hash_password("password123"),
        "role": role,
        "is_active": True,
    }


def _auth_headers_for_role(role: str, monkeypatch):
    user = _user_for_role(role)
    token = create_access_token(user["email"], role)
    monkeypatch.setattr(
        "app.services.auth_service.get_user_by_email",
        Mock(return_value=user),
    )
    return {"Authorization": f"Bearer {token}"}


def test_login_success(unauthenticated_client, monkeypatch):
    mocked_user = {
        "user_id": 1,
        "email": "demo@example.com",
        "full_name": "Demo User",
        "hashed_password": "not-used",
        "role": "admin",
        "is_active": True,
    }
    monkeypatch.setattr(
        "app.routers.auth.authenticate_user",
        Mock(return_value=mocked_user),
    )

    response = unauthenticated_client.post(
        "/api/auth/login",
        json={
            "email": "demo@example.com",
            "password": "demo123",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert data["access_token"]
    assert data["email"] == "demo@example.com"
    assert data["full_name"] == "Demo User"
    assert data["role"] == "admin"


def test_login_failure(unauthenticated_client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.auth.authenticate_user",
        Mock(return_value=None),
    )

    response = unauthenticated_client.post(
        "/api/auth/login",
        json={
            "email": "demo@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_me_returns_current_user(unauthenticated_client, monkeypatch):
    token = create_access_token("demo@example.com", "admin")
    monkeypatch.setattr(
        "app.services.auth_service.get_user_by_email",
        Mock(
            return_value={
                "user_id": 1,
                "email": "demo@example.com",
                "full_name": "Demo User",
                "hashed_password": hash_password("demo123"),
                "role": "admin",
                "is_active": True,
            }
        ),
    )

    response = unauthenticated_client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "email": "demo@example.com",
        "full_name": "Demo User",
        "role": "admin",
    }


def test_me_requires_token(unauthenticated_client):
    response = unauthenticated_client.get("/api/auth/me")

    assert response.status_code == 401


def test_protected_endpoint_requires_token(unauthenticated_client):
    response = unauthenticated_client.get("/api/portfolio/1/dashboard")

    assert response.status_code == 401


def test_seed_demo_user_skips_hash_when_user_exists(monkeypatch):
    monkeypatch.setattr(
        auth_service,
        "get_user_by_email",
        Mock(return_value={"email": "demo@example.com", "role": "admin"}),
    )
    mocked_hash = Mock()
    monkeypatch.setattr(auth_service, "hash_password", mocked_hash)
    monkeypatch.setattr(auth_service, "create_user", Mock())
    monkeypatch.setattr(auth_service, "update_user_role", Mock())

    auth_service.seed_demo_user()

    mocked_hash.assert_not_called()


def test_seed_demo_user_updates_legacy_demo_role(monkeypatch):
    mocked_update_role = Mock()
    monkeypatch.setattr(
        auth_service,
        "get_user_by_email",
        Mock(return_value={"email": "demo@example.com", "role": "viewer"}),
    )
    monkeypatch.setattr(auth_service, "hash_password", Mock())
    monkeypatch.setattr(auth_service, "create_user", Mock())
    monkeypatch.setattr(auth_service, "update_user_role", mocked_update_role)

    auth_service.seed_demo_user()

    mocked_update_role.assert_called_once_with("demo@example.com", "admin")


def test_admin_can_access_user_management(unauthenticated_client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.auth.list_users",
        Mock(
            return_value=[
                {
                    "user_id": 1,
                    "email": "admin@example.com",
                    "full_name": "Demo Admin",
                    "role": "admin",
                    "is_active": True,
                }
            ]
        ),
    )

    response = unauthenticated_client.get(
        "/api/auth/users",
        headers=_auth_headers_for_role("admin", monkeypatch),
    )

    assert response.status_code == 200
    assert response.json()[0]["role"] == "admin"


def test_portfolio_manager_can_refresh_but_cannot_manage_users(
    unauthenticated_client,
    monkeypatch,
):
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

    headers = _auth_headers_for_role("portfolio_manager", monkeypatch)
    refresh_response = unauthenticated_client.post(
        "/api/market-data/refresh",
        headers=headers,
    )
    users_response = unauthenticated_client.get(
        "/api/auth/users",
        headers=headers,
    )

    assert refresh_response.status_code == 200
    assert users_response.status_code == 403


def test_analyst_can_use_ai_and_export_pdf_but_cannot_refresh(
    unauthenticated_client,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.routers.ai.generate_ai_risk_summary",
        Mock(return_value={"portfolio_id": 1, "summary": "Mock AI response"}),
    )
    monkeypatch.setattr(
        "app.routers.portfolio.generate_pdf_risk_report",
        Mock(return_value=b"%PDF-1.4 test"),
    )

    headers = _auth_headers_for_role("analyst", monkeypatch)
    ai_response = unauthenticated_client.post(
        "/api/portfolio/1/ai-risk-summary",
        headers=headers,
    )
    pdf_response = unauthenticated_client.get(
        "/api/portfolio/1/risk-report/pdf",
        headers=headers,
    )
    refresh_response = unauthenticated_client.post(
        "/api/market-data/refresh",
        headers=headers,
    )

    assert ai_response.status_code == 200
    assert pdf_response.status_code == 200
    assert refresh_response.status_code == 403


def test_viewer_can_read_dashboard_but_cannot_use_restricted_features(
    unauthenticated_client,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.routers.portfolio.get_portfolio_dashboard_data",
        Mock(
            return_value={
                "risk": {},
                "returns": [],
                "holdings": [],
                "sector_exposure": [],
                "risk_contribution": [],
            }
        ),
    )

    headers = _auth_headers_for_role("viewer", monkeypatch)
    dashboard_response = unauthenticated_client.get(
        "/api/portfolio/1/dashboard",
        headers=headers,
    )
    ai_response = unauthenticated_client.post(
        "/api/portfolio/1/ai-risk-summary",
        headers=headers,
    )
    pdf_response = unauthenticated_client.get(
        "/api/portfolio/1/risk-report/pdf",
        headers=headers,
    )
    refresh_response = unauthenticated_client.post(
        "/api/market-data/refresh",
        headers=headers,
    )

    assert dashboard_response.status_code == 200
    assert ai_response.status_code == 403
    assert pdf_response.status_code == 403
    assert refresh_response.status_code == 403
