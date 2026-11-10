import re
import logging
from typing import Optional, Any
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
import oracledb

logger = logging.getLogger(__name__)

# Pattern: ORA-20xxx: ERROR_CODE|optional details
ORA_APP_ERROR_REGEX = re.compile(r"ORA-(20\d{3}):\s*([A-Z0-9_]+)\|?(.*)")

# Mapping error codes to HTTP Status codes according to SRS Section 11.2
ERROR_STATUS_MAP: dict[str, int] = {
    # 401 Unauthorized
    "AUTH_INVALID_CREDENTIALS": status.HTTP_401_UNAUTHORIZED,
    "UNAUTHORIZED": status.HTTP_401_UNAUTHORIZED,
    
    # 403 Forbidden
    "AUTH_ACCOUNT_LOCKED": status.HTTP_403_FORBIDDEN,
    "FORBIDDEN": status.HTTP_403_FORBIDDEN,
    "AUDIT_IMMUTABLE": status.HTTP_403_FORBIDDEN,
    
    # 404 Not Found
    "BOOKING_NOT_FOUND": status.HTTP_404_NOT_FOUND,
    "PAYMENT_NOT_FOUND": status.HTTP_404_NOT_FOUND,
    "USER_NOT_FOUND": status.HTTP_404_NOT_FOUND,
    "ROOM_NOT_FOUND": status.HTTP_404_NOT_FOUND,
    "NOT_FOUND": status.HTTP_404_NOT_FOUND,
    
    # 409 Conflict
    "NO_AVAILABILITY": status.HTTP_409_CONFLICT,
    "ROOM_CONFLICT": status.HTTP_409_CONFLICT,
    "PENDING_LIMIT_EXCEEDED": status.HTTP_409_CONFLICT,
    "BOOKING_STATE_INVALID": status.HTTP_409_CONFLICT,
    "CANCEL_NOT_ALLOWED": status.HTTP_409_CONFLICT,
    "CHECKIN_TOO_EARLY": status.HTTP_409_CONFLICT,
    "ROOM_NOT_READY": status.HTTP_409_CONFLICT,
    "EXTEND_CONFLICT": status.HTTP_409_CONFLICT,
    "ROOM_BUSY": status.HTTP_409_CONFLICT,
    "REFUND_EXCEEDS_PAID": status.HTTP_409_CONFLICT,
    "REFUND_STATE_INVALID": status.HTTP_409_CONFLICT,
    "ROOM_STATE_INVALID": status.HTTP_409_CONFLICT,
    "MAINTENANCE_HAS_BOOKINGS": status.HTTP_409_CONFLICT,
    "INVOICE_IMMUTABLE": status.HTTP_409_CONFLICT,
    "CONFLICT": status.HTTP_409_CONFLICT,
    
    # 410 Gone
    "HOLD_EXPIRED": status.HTTP_410_GONE,
    
    # 422 Unprocessable Content
    "VALIDATION_ERROR": 422,
    "HOURLY_NOT_ALLOWED": 422,
    "PRICE_RULE_VIOLATION": 422,
    "PRICE_OVERLAP": 422,
    "CONFIG_OVERLAP": 422,
    
    # 429 Too Many Requests
    "RATE_LIMITED": status.HTTP_429_TOO_MANY_REQUESTS,
    
    # 500 Internal Server Error
    "PRICE_MISSING": status.HTTP_500_INTERNAL_SERVER_ERROR,
    "CONFIG_MISSING": status.HTTP_500_INTERNAL_SERVER_ERROR,
    "INTERNAL_SERVER_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
    
    # 503 Service Unavailable
    "SERVICE_UNAVAILABLE": status.HTTP_503_SERVICE_UNAVAILABLE,
}

class BusinessException(Exception):
    """Business rule violation exception with standardized error code and detail."""
    def __init__(self, code: str, detail: Optional[str] = None, data: Optional[Any] = None):
        self.code = code
        self.detail = detail or ""
        self.data = data
        self.status_code = ERROR_STATUS_MAP.get(code, status.HTTP_400_BAD_REQUEST)
        super().__init__(f"{code}: {self.detail}")

def parse_oracle_error(e: oracledb.DatabaseError) -> BusinessException:
    """Parses Oracle DatabaseError into standard BusinessException."""
    err_obj = e.args[0]
    msg = str(err_obj)
    
    # Check for ORA-20xxx application errors
    match = ORA_APP_ERROR_REGEX.search(msg)
    if match:
        _ora_num, code, detail = match.groups()
        detail = detail.strip() if detail else ""
        return BusinessException(code=code, detail=detail)
    
    # Common Oracle constraint codes
    if "ORA-00001" in msg:  # Unique constraint violated
        return BusinessException(code="CONFLICT", detail="Bản ghi đã tồn tại hoặc vi phạm khóa duy nhất")
    if "ORA-02292" in msg:  # Integrity constraint violated - child record found
        return BusinessException(code="CONFLICT", detail="Không thể xóa do có dữ liệu liên quan")
    if "ORA-02290" in msg:  # Check constraint violated
        return BusinessException(code="VALIDATION_ERROR", detail="Vi phạm ràng buộc dữ liệu")
    if "ORA-01400" in msg:  # Cannot insert NULL
        return BusinessException(code="VALIDATION_ERROR", detail="Thiếu trường dữ liệu bắt buộc")

    # Unrecognized internal DB error
    logger.error(f"Unrecognized Oracle DatabaseError: {msg}", exc_info=True)
    return BusinessException(code="INTERNAL_SERVER_ERROR", detail="Lỗi hệ thống cơ sở dữ liệu")

def create_error_response(code: str, detail: Optional[str] = None, http_status: Optional[int] = None, data: Optional[Any] = None) -> JSONResponse:
    """Creates a consistent JSON error response matching API specifications."""
    status_code = http_status or ERROR_STATUS_MAP.get(code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    content: dict[str, Any] = {
        "success": False,
        "code": code,
        "detail": detail or ""
    }
    if data is not None:
        content["data"] = data
    return JSONResponse(status_code=status_code, content=content)
