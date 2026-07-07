import os
import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

_TMP_DIR = tempfile.mkdtemp(prefix="contract_analyzer_test_")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TMP_DIR}/test.db"
os.environ["CHROMA_DIR"] = f"{_TMP_DIR}/chroma"
os.environ["UPLOAD_DIR"] = f"{_TMP_DIR}/uploads"
os.environ["REPORTS_DIR"] = f"{_TMP_DIR}/reports"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["GROQ_API_KEY"] = "test-key-not-used-directly"
os.environ["ADMIN_EMAIL"] = "admin@test.com"
os.environ["ADMIN_PASSWORD"] = "AdminTestPass123!"

from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.database import Base, engine, init_db  # noqa: E402
from app.main import app  # noqa: E402

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest_asyncio.fixture
async def db_ready():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_ready):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(client):
    await client.post(
        "/api/auth/register",
        json={"email": "user@test.com", "password": "password123", "full_name": "Test User"},
    )
    response = await client.post(
        "/api/auth/login", json={"email": "user@test.com", "password": "password123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
