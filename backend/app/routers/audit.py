from fastapi import APIRouter, Depends, Query, Request

from app.schemas.audit import AuditLogResponse
from app.services.audit_service import create_audit_log, get_audit_logs
from app.services.auth_service import require_admin


router = APIRouter(prefix="/api", tags=["audit"])


@router.get(
    "/audit-logs",
    response_model=list[AuditLogResponse],
)
def audit_logs(
    request: Request,
    action: str | None = None,
    user_email: str | None = None,
    resource_type: str | None = None,
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    current_user: dict = Depends(require_admin),
):
    create_audit_log(
        action="view_audit_logs",
        status="success",
        user=current_user,
        request=request,
        resource_type="audit_log",
        resource_id="all",
        metadata={
            "filters": {
                "action": action,
                "user_email": user_email,
                "resource_type": resource_type,
                "status": status,
                "limit": limit,
            },
        },
    )
    return get_audit_logs(
        action=action,
        user_email=user_email,
        resource_type=resource_type,
        status=status,
        limit=limit,
    )
