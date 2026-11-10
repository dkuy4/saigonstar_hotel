import bcrypt
from datetime import datetime, timezone, timedelta
from typing import Optional, Any
import jwt
from fastapi import Header, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings
from app.errors import BusinessException

# HTTP Bearer for staff JWT
security_bearer = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    """Hashes password with salt using bcrypt (NFR-11)."""
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against hashed password."""
    try:
        pwd_bytes = plain_password.encode('utf-8')[:72]
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False

def create_access_token(data: dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JWT access token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"iat": now, "exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict[str, Any]:
    """Decodes and validates JWT token. Raises BusinessException if invalid or expired."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise BusinessException(code="UNAUTHORIZED", detail="Phiên đăng nhập đã hết hạn")
    except jwt.InvalidTokenError:
        raise BusinessException(code="UNAUTHORIZED", detail="Mã xác thực không hợp lệ")

def create_booking_token(booking_code: str, email: str) -> str:
    """Issues a short-lived token (2 hours) for customer booking management (F05)."""
    return create_access_token(
        {
            "type": "booking_guest",
            "booking_code": booking_code.upper(),
            "email": email.strip().lower()
        },
        expires_delta=timedelta(hours=2)
    )

class AuthUser:
    def __init__(self, user_id: int, username: str, role: str, full_name: Optional[str] = None):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.full_name = full_name

def get_current_user_optional(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)
) -> Optional[AuthUser]:
    """Optional user dependency. Returns None for guests or unauthenticated requests."""
    if not auth_header or not auth_header.credentials:
        return None
    payload = decode_access_token(auth_header.credentials)
    user_id = payload.get("sub") or payload.get("user_id")
    role = payload.get("role")
    username = payload.get("username", "")
    full_name = payload.get("full_name", "")
    if not user_id or not role:
        return None
    return AuthUser(user_id=int(user_id), username=username, role=role, full_name=full_name)

def get_current_user(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)
) -> AuthUser:
    """Strict user dependency. Raises 401 UNAUTHORIZED if not authenticated."""
    if not auth_header or not auth_header.credentials:
        raise BusinessException(code="UNAUTHORIZED", detail="Yêu cầu đăng nhập")
    payload = decode_access_token(auth_header.credentials)
    user_id = payload.get("sub") or payload.get("user_id")
    role = payload.get("role")
    username = payload.get("username", "")
    full_name = payload.get("full_name", "")
    if not user_id or not role:
        raise BusinessException(code="UNAUTHORIZED", detail="Thông tin token không hợp lệ")
    return AuthUser(user_id=int(user_id), username=username, role=role, full_name=full_name)

def require_role(*allowed_roles: str):
    """Dependency factory checking user role against allowed roles."""
    def role_checker(user: AuthUser = Depends(get_current_user)) -> AuthUser:
        if user.role not in allowed_roles:
            raise BusinessException(code="FORBIDDEN", detail="Không có quyền truy cập chức năng này")
        return user
    return role_checker

def verify_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")) -> str:
    """Dependency verifying X-API-Key header for external integration channel."""
    if not x_api_key or x_api_key != settings.API_KEY_INTEGRATION:
        raise BusinessException(code="UNAUTHORIZED", detail="Khóa API không hợp lệ")
    return x_api_key
