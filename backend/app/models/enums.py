import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class FileType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"


class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    ANALYZED = "analyzed"
    PARTIAL = "partial"
    FAILED = "failed"


class RiskCategory(str, enum.Enum):
    MISSING_CLAUSE = "missing_clause"
    HIGH_RISK_CONDITION = "high_risk_condition"
    AMBIGUOUS_STATEMENT = "ambiguous_statement"
    UNUSUAL_PAYMENT_TERM = "unusual_payment_term"
    LEGAL_RED_FLAG = "legal_red_flag"


class RiskSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReportFormat(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"


class AuditLevel(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
