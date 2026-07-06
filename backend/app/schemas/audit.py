from datetime import datetime

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None = None
    user_email: str | None = None
    user_role: str | None = None
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    status: str
    ip_address: str | None = None
    user_agent: str | None = None
    metadata: str | None = None
    created_at: datetime
