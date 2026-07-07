from pathlib import Path

from app.config import get_settings
from app.exceptions import FileTooLargeError, UnsupportedFileTypeError
from app.models.enums import FileType

settings = get_settings()

_MAGIC_BYTES: dict[bytes, FileType] = {
    b"%PDF": FileType.PDF,
    b"PK\x03\x04": FileType.DOCX,  # docx is a zip archive
}

_EXTENSION_MAP = {".pdf": FileType.PDF, ".docx": FileType.DOCX, ".txt": FileType.TXT}


def validate_upload(filename: str, content: bytes) -> FileType:
    """Validates extension, size, and (for pdf/docx) magic bytes before any parsing occurs."""
    extension = Path(filename).suffix.lower()
    if extension not in settings.allowed_extensions:
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{extension}'. Allowed: {', '.join(settings.allowed_extensions)}"
        )

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise FileTooLargeError(f"File exceeds the {settings.max_upload_size_mb}MB upload limit")

    if len(content) == 0:
        raise UnsupportedFileTypeError("Uploaded file is empty")

    file_type = _EXTENSION_MAP[extension]

    if file_type in (FileType.PDF, FileType.DOCX):
        expected_magic = b"%PDF" if file_type == FileType.PDF else b"PK\x03\x04"
        if not content.startswith(expected_magic):
            raise UnsupportedFileTypeError(
                f"File content does not match its extension '{extension}' (magic byte mismatch)"
            )

    return file_type
