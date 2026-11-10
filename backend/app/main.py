import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import oracledb

from app.config import settings
from app.db import init_db_pool, close_db_pool
from app.errors import (
    BusinessException,
    parse_oracle_error,
    create_error_response,
)
from app.routers import (
    health_router,
    auth_router,
    catalog_router,
    bookings_router,
    payments_router,
    rooms_router
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages application lifecycle: pool startup and shutdown."""
    logger.info("Starting up Hotel Booking API...")
    try:
        init_db_pool()
        logger.info("Oracle DB pool successfully initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize Oracle DB pool: {e}", exc_info=True)
    yield
    logger.info("Shutting down Hotel Booking API...")
    close_db_pool()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Global Exception Handlers ----------

@app.exception_handler(BusinessException)
async def business_exception_handler(request: Request, exc: BusinessException):
    return create_error_response(
        code=exc.code,
        detail=exc.detail,
        http_status=exc.status_code,
        data=exc.data
    )

@app.exception_handler(oracledb.DatabaseError)
async def oracle_database_error_handler(request: Request, exc: oracledb.DatabaseError):
    biz_exc = parse_oracle_error(exc)
    return create_error_response(
        code=biz_exc.code,
        detail=biz_exc.detail,
        http_status=biz_exc.status_code,
        data=biz_exc.data
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first_error = errors[0] if errors else {}
    field = ".".join(str(loc) for loc in first_error.get("loc", []))
    msg = first_error.get("msg", "Dữ liệu không hợp lệ")
    detail = f"{field}: {msg}" if field else msg
    return create_error_response(
        code="VALIDATION_ERROR",
        detail=detail,
        http_status=422,
        data=errors
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        return create_error_response(
            code="NOT_FOUND",
            detail="Tài nguyên hoặc đường dẫn API không tồn tại",
            http_status=status.HTTP_404_NOT_FOUND
        )
    return create_error_response(
        code="HTTP_ERROR",
        detail=str(exc.detail),
        http_status=exc.status_code
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return create_error_response(
        code="INTERNAL_SERVER_ERROR",
        detail="Đã xảy ra lỗi hệ thống, vui lòng thử lại sau",
        http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles

# Ensure upload directories exist
Path("uploads/documents").mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Mount API Routers
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(catalog_router, prefix=settings.API_V1_STR)
app.include_router(bookings_router, prefix=settings.API_V1_STR)
app.include_router(payments_router, prefix=settings.API_V1_STR)
app.include_router(rooms_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "api_v1": settings.API_V1_STR
    }
