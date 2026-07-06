from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.schemas.notifications import SendReportRequest, SendReportResponse
from app.services.auth_service import require_admin
from app.services.notification_service import NotificationError, NotificationService


router = APIRouter(prefix="/api", tags=["notifications"])


@router.post(
    "/notifications/send-report",
    response_model=SendReportResponse,
)
def send_report(
    report_request: SendReportRequest,
    request: Request,
    current_user: dict = Depends(require_admin),
):
    try:
        result = NotificationService().send_portfolio_risk_report(
            portfolio_id=report_request.portfolio_id,
            recipient_email=report_request.recipient_email,
            triggered_by="manual_admin",
            user=current_user,
            request=request,
        )
    except NotificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return {
        "success": result.success,
        "message": result.message,
        "provider_message_id": result.provider_message_id,
    }
