from datetime import datetime

from pydantic import BaseModel

from app.models.enums import AuditLevel, UserRole


class AdminUserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None = None
    document_count: int = 0

    model_config = {"from_attributes": True}


class AdminUserUpdateRequest(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None


class AuditLogOut(BaseModel):
    id: int
    user_id: int | None
    action: str
    resource_type: str | None
    resource_id: int | None
    detail: dict | None
    level: AuditLevel
    created_at: datetime

    model_config = {"from_attributes": True}


class SystemStatsOut(BaseModel):
    total_users: int
    total_documents: int
    total_analyses: int
    total_groq_calls: int
    average_processing_time_seconds: float | None
    documents_by_status: dict[str, int]
