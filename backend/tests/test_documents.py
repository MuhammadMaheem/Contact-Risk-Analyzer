import pytest

pytestmark = pytest.mark.asyncio


async def test_upload_rejects_unsupported_extension(client, auth_headers):
    response = await client.post(
        "/api/documents",
        headers=auth_headers,
        files={"file": ("malware.exe", b"not a real exe", "application/octet-stream")},
    )
    assert response.status_code == 415


async def test_upload_rejects_empty_file(client, auth_headers):
    response = await client.post(
        "/api/documents",
        headers=auth_headers,
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert response.status_code == 415


async def test_upload_rejects_oversized_file(client, auth_headers):
    from app.config import get_settings

    settings = get_settings()
    oversized = b"a" * (settings.max_upload_size_mb * 1024 * 1024 + 1)
    response = await client.post(
        "/api/documents",
        headers=auth_headers,
        files={"file": ("big.txt", oversized, "text/plain")},
    )
    assert response.status_code == 413


async def test_upload_accepts_txt_and_returns_uploaded_status(client, auth_headers):
    content = b"This is a simple contract text with enough characters to pass the OCR threshold check."
    response = await client.post(
        "/api/documents",
        headers=auth_headers,
        files={"file": ("contract.txt", content, "text/plain")},
    )
    assert response.status_code == 202
    body = response.json()["document"]
    assert body["file_type"] == "txt"
    assert body["status"] == "uploaded"


async def test_document_not_accessible_by_other_user(client, auth_headers):
    upload = await client.post(
        "/api/documents",
        headers=auth_headers,
        files={"file": ("contract.txt", b"Some contract content for validation purposes here.", "text/plain")},
    )
    document_id = upload.json()["document"]["id"]

    await client.post(
        "/api/auth/register",
        json={"email": "other@test.com", "password": "password123", "full_name": "Other User"},
    )
    other_login = await client.post(
        "/api/auth/login", json={"email": "other@test.com", "password": "password123"}
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    response = await client.get(f"/api/documents/{document_id}", headers=other_headers)
    assert response.status_code == 403


async def test_get_nonexistent_document_404s(client, auth_headers):
    response = await client.get("/api/documents/999999", headers=auth_headers)
    assert response.status_code == 404
