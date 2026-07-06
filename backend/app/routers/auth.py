import logging
from time import monotonic

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.database.repository import list_users
from app.schemas.auth import LoginRequest, TokenResponse, UserListItem, UserResponse
from app.services.audit_service import create_audit_log
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    get_current_user,
    require_admin,
)


router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/login", response_model=TokenResponse)
def login(login_request: LoginRequest, request: Request):
    started_at = monotonic()
    user = authenticate_user(login_request.email, login_request.password)
    auth_duration = monotonic() - started_at

    if user is None:
        logger.info(
            "Login failed for email=%s duration_seconds=%.3f",
            login_request.email,
            auth_duration,
        )
        create_audit_log(
            action="login",
            status="failed",
            request=request,
            resource_type="auth",
            resource_id=login_request.email,
            metadata={"email": login_request.email},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    logger.info(
        "Login succeeded for email=%s role=%s duration_seconds=%.3f",
        user["email"],
        user["role"],
        auth_duration,
    )
    create_audit_log(
        action="login",
        status="success",
        user=user,
        request=request,
        resource_type="auth",
        resource_id=user["email"],
    )

    return {
        "access_token": create_access_token(user["email"], user["role"]),
        "token_type": "bearer",
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"],
    }


@router.get("/me", response_model=UserResponse)
def me(current_user=Depends(get_current_user)):
    return {
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "role": current_user["role"],
    }


@router.get("/users", response_model=list[UserListItem])
def users(
    request: Request,
    current_user: dict = Depends(require_admin),
):
    create_audit_log(
        action="view_users",
        status="success",
        user=current_user,
        request=request,
        resource_type="user",
        resource_id="all",
    )
    return list_users()
