from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.enums import AuditLevel


class AuditService:
    """Writes AuditLog rows — doubles as the system log surfaced in the admin panel."""

    async def log(
        self,
        db: AsyncSession,
        action: str,
        user_id: int | None = None,
        resource_type: str | None = None,
        resource_id: int | None = None,
        detail: dict | None = None,
        level: AuditLevel = AuditLevel.INFO,
        ip_address: str | None = None,
        commit: bool = True,
    ) -> None:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail,
            level=level,
            ip_address=ip_address,
        )
        db.add(entry)
        if commit:
            await db.commit()


audit_service = AuditService()
