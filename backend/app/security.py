import bcrypt
from datetime import datetime, timezone, timedelta
from typing import Optional, Any
import jwt
import oracledb
from fastapi import Header, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.config import settings
from app.db import get_conn
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
    def __init__(
        self,
        user_id: int,
        username: str,
        role: str,
        full_name: Optional[str] = None,
        phai_doi_mat_khau: bool = False
    ):
        self.user_id = user_id
        self.username = username
        self.role = role
        self.full_name = full_name
        self.phai_doi_mat_khau = phai_doi_mat_khau

def get_current_user_optional(
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    conn: oracledb.Connection = Depends(get_conn)
) -> Optional[AuthUser]:
    """Optional user dependency. Returns None for guests or unauthenticated requests."""
    if not auth_header or not auth_header.credentials:
        return None
    try:
        payload = decode_access_token(auth_header.credentials)
    except BusinessException:
        return None
    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        return None
    role = payload.get("role")
    if role == "KHACH":
        # Validate guest account from khach_hang table
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT khach_hang_id, ho_ten, email, sdt
                FROM hotel_owner.khach_hang
                WHERE khach_hang_id = :kid
                """,
                kid=int(user_id)
            )
            grow = cur.fetchone()
            if not grow:
                raise BusinessException(code="UNAUTHORIZED", detail="Tài khoản khách hàng không tồn tại")
            return AuthUser(
                user_id=grow[0],
                username=grow[2] or str(grow[0]),
                role="KHACH",
                full_name=grow[1],
                phai_doi_mat_khau=False
            )

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT u.trang_thai, v.ma_vai_tro, u.ho_ten, u.ten_dang_nhap, u.phai_doi_mat_khau
              FROM nguoi_dung u
              JOIN vai_tro v ON u.vai_tro_id = v.vai_tro_id
             WHERE u.nguoi_dung_id = :user_id
            """,
            user_id=int(user_id)
        )
        row = cur.fetchone()
        if not row or row[0] == "KHOA":
            return None
        return AuthUser(
            user_id=int(user_id),
            username=row[3],
            role=row[1],
            full_name=row[2],
            phai_doi_mat_khau=bool(row[4])
        )

def get_current_user(
    request: Request,
    auth_header: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    conn: oracledb.Connection = Depends(get_conn)
) -> AuthUser:
    """
    Strict user dependency.
    Enforces Rule 4: real-time validation of account status and role against Oracle DB.
    Enforces Rule 5: mandatory password change blocks non-auth endpoints if phai_doi_mat_khau is TRUE.
    """
    if not auth_header or not auth_header.credentials:
        raise BusinessException(code="UNAUTHORIZED", detail="Yêu cầu đăng nhập")
    payload = decode_access_token(auth_header.credentials)
    user_id = payload.get("sub") or payload.get("user_id")
    username = payload.get("username", "")
    full_name = payload.get("full_name", "")
    if not user_id:
        raise BusinessException(code="UNAUTHORIZED", detail="Thông tin token không hợp lệ")

    role = payload.get("role")
    if role == "KHACH":
        # Validate guest account from khach_hang table
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT khach_hang_id, ho_ten, email, sdt
                FROM hotel_owner.khach_hang
                WHERE khach_hang_id = :kid
                """,
                kid=int(user_id)
            )
            grow = cur.fetchone()
            if not grow:
                raise BusinessException(code="UNAUTHORIZED", detail="Tài khoản khách hàng không tồn tại")
            return AuthUser(
                user_id=grow[0],
                username=grow[2] or str(grow[0]),
                role="KHACH",
                full_name=grow[1],
                phai_doi_mat_khau=False
            )

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT u.trang_thai, v.ma_vai_tro, u.ho_ten, u.ten_dang_nhap, u.phai_doi_mat_khau
              FROM nguoi_dung u
              JOIN vai_tro v ON u.vai_tro_id = v.vai_tro_id
             WHERE u.nguoi_dung_id = :user_id
            """,
            user_id=int(user_id)
        )
        row = cur.fetchone()
        if not row:
            raise BusinessException(code="UNAUTHORIZED", detail="Tài khoản không tồn tại")
        
        db_status, db_role, db_full_name, db_username, db_phai_doi = row[0], row[1], row[2], row[3], bool(row[4])
        
        if db_status == "KHOA":
            raise BusinessException(code="AUTH_ACCOUNT_LOCKED", detail="Tài khoản đã bị quản lý khóa")
        
        # Rule 5: If phai_doi_mat_khau is True, block access to any endpoint other than change-password, logout, me
        if db_phai_doi:
            allowed_paths = (
                "/api/v1/auth/change-password",
                "/api/v1/auth/logout",
                "/api/v1/auth/me"
            )
            normalized_path = request.url.path.rstrip("/")
            if normalized_path not in [p.rstrip("/") for p in allowed_paths]:
                raise BusinessException(
                    code="PASSWORD_CHANGE_REQUIRED",
                    detail="Tài khoản bắt buộc phải đổi mật khẩu trước khi sử dụng hệ thống"
                )

        return AuthUser(
            user_id=int(user_id),
            username=db_username or username,
            role=db_role,
            full_name=db_full_name or full_name,
            phai_doi_mat_khau=db_phai_doi
        )

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
