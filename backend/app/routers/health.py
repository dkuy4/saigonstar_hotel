from datetime import datetime, timezone, timedelta
import logging
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
import oracledb

from app.db import get_pool
from app.schemas.common import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health Check"])

VN_TZ = timezone(timedelta(hours=7))

@router.get("/health", response_model=HealthResponse)
def health_check() -> JSONResponse:
    """
    GET /api/v1/health (NFR-27).
    Executes SELECT 1 FROM dual.
    Returns 200 if database is reachable, 503 if unreachable.
    """
    now_iso = datetime.now(VN_TZ).isoformat()
    try:
        pool = get_pool()
        with pool.acquire() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM dual")
                res = cur.fetchone()
                if res and res[0] == 1:
                    logger.info("Health check passed: Oracle DB is responsive.")
                    return JSONResponse(
                        status_code=status.HTTP_200_OK,
                        content={
                            "status": "healthy",
                            "database": "connected",
                            "timestamp": now_iso
                        }
                    )
        raise Exception("Database returned invalid result")
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "timestamp": now_iso
            }
        )
