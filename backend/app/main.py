import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.api import admin, analysis, auth, dashboard, documents, reports, search
from app.config import get_settings
from app.database import AsyncSessionLocal, init_db
from app.exceptions import AppException
from app.models.enums import UserRole
from app.models.user import User
from app.security import PasswordHasher
from app.services.document_processing_pipeline import mark_stale_processing_documents_as_failed
from app.services.embedding_service import embedding_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


async def _bootstrap_admin() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.role == UserRole.ADMIN))
        if result.scalar_one_or_none() is not None:
            return
        admin_user = User(
            email=settings.admin_email,
            hashed_password=PasswordHasher.hash(settings.admin_password),
            full_name=settings.admin_full_name,
            role=UserRole.ADMIN,
        )
        db.add(admin_user)
        await db.commit()
        logger.info("Bootstrap admin account created: %s", settings.admin_email)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    await _bootstrap_admin()
    await mark_stale_processing_documents_as_failed()
    embedding_service.warm_up()
    logger.info("%s started.", settings.app_name)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.error_code, "message": exc.message, "detail": exc.detail},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"error_code": "internal_error", "message": "An unexpected error occurred", "detail": None},
    )


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": settings.app_name}


app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(analysis.router)
app.include_router(search.router)
app.include_router(reports.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
