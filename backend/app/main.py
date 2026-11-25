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
    rooms_router,
    prices_router,
    settings_router,
    translations_router,
    users_router,
    reports_router,
    audit_router,
    housekeeping_router,
    refunds_router,
    reconciliation_router,
    system_router,
    guest_auth_router
)
from app.workers.scheduler import BackgroundJobManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages application lifecycle: pool startup, scheduler and shutdown."""
    logger.info("Starting up Hotel Booking API...")
    try:
        init_db_pool()
        logger.info("Oracle DB pool successfully initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize Oracle DB pool: {e}", exc_info=True)
    
    # Start background scheduler for periodic tasks (F13)
    scheduler_mgr = BackgroundJobManager.get_instance()
    scheduler_mgr.start()
    logger.info("Background job scheduler started.")
    
    yield
    
    logger.info("Shutting down Hotel Booking API...")
    scheduler_mgr.stop()
    close_db_pool()

API_DESCRIPTION = """
API hệ thống đặt phòng & quản trị Khách sạn Sài Gòn Star (FR-49, FR-50, AC-18).

### Xác thực
- **Nhân viên (Lễ tân, Buồng phòng, Quản lý):** JWT Bearer Token qua `POST /api/v1/auth/login`.
- **Khách tra cứu/đổi/hủy:** Header `X-Booking-Token` nhận từ `POST /api/v1/bookings/lookup`.
- **Đối tác tích hợp (Kênh API):** Header `X-API-Key` trên các endpoint đặt phòng công khai.

### Mã lỗi nghiệp vụ chuẩn (`code`)
- `400 VALIDATION_ERROR`, `HOURLY_NOT_ALLOWED`, `PRICE_RULE_VIOLATION`
- `401 UNAUTHORIZED`, `AUTH_INVALID_CREDENTIALS`
- `403 FORBIDDEN`, `AUTH_ACCOUNT_LOCKED`
- `404 BOOKING_NOT_FOUND`, `ROOM_NOT_FOUND`
- `409 ROOM_CONFLICT`, `ROOM_BUSY`, `BOOKING_STATE_INVALID`, `REFUND_EXCEEDS_PAID`, `PENDING_LIMIT_EXCEEDED`
- `429 RATE_LIMITED`
"""

OPENAPI_TAGS = [
    {"name": "Health", "description": "Kiểm tra tình trạng API và kết nối Oracle DB"},
    {"name": "Authentication", "description": "Đăng nhập, đổi mật khẩu, phiên làm việc nhân viên"},
    {"name": "Catalog & Availability", "description": "Hạng phòng, tìm phòng trống, bảng tỷ giá ngoại tệ"},
    {"name": "Bookings", "description": "Tạo đơn (WEB/QUAY/API), tra cứu, check-in, check-out, gia hạn, đổi phòng, no-show, gửi lại email"},
    {"name": "Payments", "description": "Thanh toán trực tuyến và callback cổng thanh toán"},
    {"name": "Refunds", "description": "Đề xuất hoàn tiền, duyệt và chi hoàn tiền (F12)"},
    {"name": "Reconciliation", "description": "Đối soát doanh thu theo ngày và xuất CSV (F12)"},
    {"name": "Housekeeping & Maintenance", "description": "Buồng phòng dọn dẹp và bảo trì phòng (F15)"},
    {"name": "System & Jobs", "description": "Tác vụ nền định kỳ, tỷ giá thủ công và đối soát lệch phòng (F13)"},
    {"name": "Reports", "description": "Báo cáo doanh thu, công suất, hủy đơn, ADR/RevPAR (F18)"},
    {"name": "Audit Logs", "description": "Nhật ký kiểm toán bất biến và xem trạng thái tại thời điểm (F19)"},
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=API_DESCRIPTION,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=OPENAPI_TAGS,
    lifespan=lifespan
)

# Security Headers Middleware (F21, NFR-16)
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

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
    sanitized_errors = []
    for err in errors:
        err_copy = dict(err)
        if "input" in err_copy and isinstance(err_copy["input"], bytes):
            err_copy["input"] = err_copy["input"].decode("utf-8", errors="replace")
        if "ctx" in err_copy and isinstance(err_copy["ctx"], dict):
            ctx_copy = {}
            for k, v in err_copy["ctx"].items():
                if isinstance(v, Exception):
                    ctx_copy[k] = str(v)
                else:
                    ctx_copy[k] = v
            err_copy["ctx"] = ctx_copy
        sanitized_errors.append(err_copy)
    return create_error_response(
        code="VALIDATION_ERROR",
        detail=detail,
        http_status=422,
        data=sanitized_errors
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
app.include_router(prices_router, prefix=settings.API_V1_STR)
app.include_router(settings_router, prefix=settings.API_V1_STR)
app.include_router(translations_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)
app.include_router(housekeeping_router, prefix=settings.API_V1_STR)
app.include_router(refunds_router, prefix=settings.API_V1_STR)
app.include_router(reconciliation_router, prefix=settings.API_V1_STR)
app.include_router(system_router, prefix=settings.API_V1_STR)
app.include_router(guest_auth_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "api_v1": settings.API_V1_STR
    }
