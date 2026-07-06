import json
import logging
from typing import Any

from fastapi import Request

from app.database.repository import insert_audit_log, list_audit_logs


logger = logging.getLogger(__name__)


def create_audit_log(
    action: str,
    status: str,
    user: dict | None = None,
    request: Request | None = None,
    resource_type: str | None = None,
    resource_id: str | int | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    try:
        insert_audit_log(
            user_id=user.get("user_id") if user else None,
            user_email=user.get("email") if user else None,
            user_role=user.get("role") if user else None,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else None,
            status=status,
            ip_address=_get_ip_address(request),
            user_agent=_get_user_agent(request),
            metadata=json.dumps(metadata or {}, default=str),
        )
    except Exception:
        logger.exception("Failed to create audit log for action=%s", action)


def get_audit_logs(
    action: str | None = None,
    user_email: str | None = None,
    resource_type: str | None = None,
    status: str | None = None,
    limit: int = 100,
):
    return list_audit_logs(
        action=action,
        user_email=user_email,
        resource_type=resource_type,
        status=status,
        limit=limit,
    )


def _get_ip_address(request: Request | None) -> str | None:
    if request is None:
        return None

    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return request.client.host if request.client else None


def _get_user_agent(request: Request | None) -> str | None:
    if request is None:
        return None

    return request.headers.get("user-agent")
