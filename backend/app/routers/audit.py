from fastapi import APIRouter, Depends, Query

from app.schemas.audit import AuditLogResponse
from app.services.audit_service import get_audit_logs
from app.services.auth_service import require_admin


router = APIRouter(prefix="/api", tags=["audit"])


@router.get(
    "/audit-logs",
    response_model=list[AuditLogResponse],
    dependencies=[Depends(require_admin)],
)
def audit_logs(
    action: str | None = None,
    user_email: str | None = None,
    resource_type: str | None = None,
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
):
    return get_audit_logs(
        action=action,
        user_email=user_email,
        resource_type=resource_type,
        status=status,
        limit=limit,
    )
