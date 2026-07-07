class AppException(Exception):
    """Base application exception. Carries an HTTP status code and a stable error code
    so the API always returns a consistent JSON error envelope."""

    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(self, message: str, detail: str | None = None) -> None:
        self.message = message
        self.detail = detail
        super().__init__(message)


class ValidationAppError(AppException):
    status_code = 422
    error_code = "validation_error"


class UnsupportedFileTypeError(AppException):
    status_code = 415
    error_code = "unsupported_file_type"


class FileTooLargeError(AppException):
    status_code = 413
    error_code = "file_too_large"


class DocumentParsingError(AppException):
    status_code = 422
    error_code = "document_parsing_failed"


class ExtractionError(AppException):
    status_code = 502
    error_code = "extraction_failed"


class RiskDetectionError(AppException):
    status_code = 502
    error_code = "risk_detection_failed"


class SummarizationError(AppException):
    status_code = 502
    error_code = "summarization_failed"


class VectorStoreError(AppException):
    status_code = 502
    error_code = "vector_store_failed"


class ReportGenerationError(AppException):
    status_code = 500
    error_code = "report_generation_failed"


class AuthenticationError(AppException):
    status_code = 401
    error_code = "authentication_failed"


class AuthorizationError(AppException):
    status_code = 403
    error_code = "not_authorized"


class NotFoundError(AppException):
    status_code = 404
    error_code = "not_found"


class ConflictError(AppException):
    status_code = 409
    error_code = "conflict"


class GroqAPIError(AppException):
    status_code = 502
    error_code = "groq_api_error"
