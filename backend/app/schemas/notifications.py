from pydantic import BaseModel


class SendReportRequest(BaseModel):
    portfolio_id: int
    recipient_email: str


class SendReportResponse(BaseModel):
    success: bool
    message: str
    provider_message_id: str | None = None
