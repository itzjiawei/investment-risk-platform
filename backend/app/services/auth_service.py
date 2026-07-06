from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError
from passlib.context import CryptContext

from app.config import (
    DEMO_USER_EMAIL,
    DEMO_USER_FULL_NAME,
    DEMO_USER_PASSWORD,
    JWT_ALGORITHM,
    JWT_EXPIRE_MINUTES,
    JWT_SECRET_KEY,
)
from app.database.repository import (
    create_user,
    ensure_users_table,
    get_user_by_email,
    update_user_role,
)
from app.services.audit_service import create_audit_log


ROLE_ADMIN = "admin"
ROLE_PORTFOLIO_MANAGER = "portfolio_manager"
ROLE_ANALYST = "analyst"
ROLE_VIEWER = "viewer"

VALID_ROLES = {
    ROLE_ADMIN,
    ROLE_PORTFOLIO_MANAGER,
    ROLE_ANALYST,
    ROLE_VIEWER,
}
MARKET_REFRESH_ROLES = {ROLE_ADMIN, ROLE_PORTFOLIO_MANAGER}
AI_ROLES = {ROLE_ADMIN, ROLE_PORTFOLIO_MANAGER, ROLE_ANALYST}
PDF_EXPORT_ROLES = {ROLE_ADMIN, ROLE_PORTFOLIO_MANAGER, ROLE_ANALYST}

DEMO_USERS = [
    {
        "email": "admin@example.com",
        "password": "admin123",
        "full_name": "Demo Admin",
        "role": ROLE_ADMIN,
    },
    {
        "email": "manager@example.com",
        "password": "manager123",
        "full_name": "Demo Portfolio Manager",
        "role": ROLE_PORTFOLIO_MANAGER,
    },
    {
        "email": "analyst@example.com",
        "password": "analyst123",
        "full_name": "Demo Analyst",
        "role": ROLE_ANALYST,
    },
    {
        "email": "viewer@example.com",
        "password": "viewer123",
        "full_name": "Demo Viewer",
        "role": ROLE_VIEWER,
    },
]

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)
_auth_storage_initialized = False


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_context.verify(password, hashed_password)


def create_access_token(email: str, role: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=JWT_EXPIRE_MINUTES,
    )
    payload = {
        "sub": email,
        "role": role,
        "exp": expires_at,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def initialize_auth_storage() -> None:
    global _auth_storage_initialized

    if _auth_storage_initialized:
        return

    ensure_users_table()
    seed_demo_user()
    _auth_storage_initialized = True


def seed_demo_user() -> None:
    demo_users = [
        {
            "email": DEMO_USER_EMAIL,
            "password": DEMO_USER_PASSWORD,
            "full_name": DEMO_USER_FULL_NAME,
            "role": ROLE_ADMIN,
        },
        *DEMO_USERS,
    ]

    seeded_emails = set()
    for demo_user in demo_users:
        email = demo_user["email"]

        if email in seeded_emails:
            continue

        seeded_emails.add(email)

        existing_user = get_user_by_email(email)

        if existing_user is not None:
            if email == DEMO_USER_EMAIL and existing_user.get("role") != ROLE_ADMIN:
                update_user_role(email, ROLE_ADMIN)

            continue

        create_user(
            email=email,
            full_name=demo_user["full_name"],
            hashed_password=hash_password(demo_user["password"]),
            role=demo_user["role"],
        )


def authenticate_user(email: str, password: str):
    initialize_auth_storage()
    user = get_user_by_email(email)

    if user is None:
        return None

    if not user["is_active"]:
        return None

    if not verify_password(password, user["hashed_password"]):
        return None

    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    if credentials is None:
        raise _auth_error()

    try:
        payload = jwt.decode(
            credentials.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
    except PyJWTError as exc:
        raise _auth_error() from exc

    email = payload.get("sub")

    if not email:
        raise _auth_error()

    user = get_user_by_email(str(email))

    if user is None or not user["is_active"]:
        raise _auth_error()

    return user


def require_roles(*roles: str):
    allowed_roles = set(roles)

    def dependency(
        request: Request,
        current_user=Depends(get_current_user),
    ):
        if current_user.get("role") not in allowed_roles:
            create_audit_log(
                action="unauthorized_access",
                status="forbidden",
                user=current_user,
                request=request,
                resource_type="endpoint",
                resource_id=request.url.path,
                metadata={
                    "method": request.method,
                    "required_roles": sorted(allowed_roles),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return dependency


def require_admin(request: Request, current_user=Depends(get_current_user)):
    return require_roles(ROLE_ADMIN)(request, current_user)


def require_market_refresh_permission(
    request: Request,
    current_user=Depends(get_current_user),
):
    return require_roles(*MARKET_REFRESH_ROLES)(request, current_user)


def require_ai_permission(request: Request, current_user=Depends(get_current_user)):
    return require_roles(*AI_ROLES)(request, current_user)


def require_pdf_export_permission(
    request: Request,
    current_user=Depends(get_current_user),
):
    return require_roles(*PDF_EXPORT_ROLES)(request, current_user)


def _auth_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
