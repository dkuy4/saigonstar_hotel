from datetime import datetime, timezone, timedelta
import logging
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
import oracledb

from app.config import settings
from app.db import get_conn
from app.errors import BusinessException
from app.security import (
    verify_password,
    hash_password,
    create_access_token,
    get_current_user,
    AuthUser
)
from app.schemas.auth import (
    LoginRequest,
    ChangePasswordRequest
)
from app.repositories import auth_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

VN_TZ = timezone(timedelta(hours=7))

@router.post("/login")
def login(request: LoginRequest, conn: oracledb.Connection = Depends(get_conn)) -> dict:
    """
    POST /api/v1/auth/login (FR-48).
    Processing order according to SRS Section 4:
    1. Check user exists
    2. Check status (admin lock) & temporary lock (khoa_den)
    3. Verify password hash
    4. If wrong: increment counter, lock if exceeded
    5. If correct: reset counter, issue JWT
    """
    # 1. Check user exists
    user = auth_repo.get_user_by_username(conn, request.username)
    if not user:
        raise BusinessException(
            code="AUTH_INVALID_CREDENTIALS",
            detail="Sai tên đăng nhập hoặc mật khẩu"
        )
    
    # 2. Check admin lock
    if user.status == "KHOA":
        raise BusinessException(
            code="AUTH_ACCOUNT_LOCKED",
            detail="Tài khoản đã bị quản lý khóa"
        )
    
    # Check temporary lock (khoa_den)
    now = datetime.now(timezone.utc)
    if user.locked_until:
        # Convert locked_until to timezone aware UTC if needed
        locked_dt = user.locked_until if user.locked_until.tzinfo else user.locked_until.replace(tzinfo=timezone.utc)
        if locked_dt > now:
            raise BusinessException(
                code="AUTH_ACCOUNT_LOCKED",
                detail="Tài khoản đang bị khóa tạm do nhập sai mật khẩu nhiều lần"
            )
        else:
            # Lock has expired, reset counter
            auth_repo.reset_failed_attempts(conn, user.user_id)
            user.failed_attempts = 0

    # 3. Verify password hash
    if not verify_password(request.password, user.password_hash):
        max_attempts, lock_minutes = auth_repo.get_login_config_params(conn)
        is_locked = auth_repo.record_failed_attempt(
            conn=conn,
            user_id=user.user_id,
            current_attempts=user.failed_attempts,
            max_attempts=max_attempts,
            lock_minutes=lock_minutes
        )
        conn.commit()
        if is_locked:
            logger.warning(f"User {user.username} temporarily locked for {lock_minutes} minutes after failed attempts.")
            raise BusinessException(
                code="AUTH_ACCOUNT_LOCKED",
                detail=f"Tài khoản đã bị khóa tạm {lock_minutes} phút do nhập sai {max_attempts} lần liên tiếp"
            )
        raise BusinessException(
            code="AUTH_INVALID_CREDENTIALS",
            detail="Sai tên đăng nhập hoặc mật khẩu"
        )

    # 4. Successful login: reset failed attempts counter
    auth_repo.reset_failed_attempts(conn, user.user_id)
    conn.commit()

    # 5. Issue JWT
    token_payload = {
        "sub": str(user.user_id),
        "user_id": user.user_id,
        "username": user.username,
        "role": user.role,
        "name": user.full_name
    }
    token = create_access_token(token_payload)
    expires_at = (datetime.now(VN_TZ) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)).isoformat()

    return {
        "success": True,
        "token": token,
        "expiresAt": expires_at,
        "user": {
            "id": user.user_id,
            "username": user.username,
            "name": user.full_name,
            "role": user.role
        }
    }

@router.post("/change-password")
def change_password(
    request: ChangePasswordRequest,
    current_user: AuthUser = Depends(get_current_user),
    conn: oracledb.Connection = Depends(get_conn)
) -> dict:
    """
    POST /api/v1/auth/change-password (FR-48).
    Verifies old password and updates to new password hash.
    """
    user = auth_repo.get_user_by_id(conn, current_user.user_id)
    if not user:
        raise BusinessException(code="USER_NOT_FOUND", detail="Không tìm thấy thông tin người dùng")
    
    if not verify_password(request.current_password, user.password_hash):
        raise BusinessException(code="AUTH_INVALID_CREDENTIALS", detail="Mật khẩu hiện tại không chính xác")
    
    if len(request.new_password) < 8:
        raise BusinessException(code="VALIDATION_ERROR", detail="Mật khẩu mới phải có ít nhất 8 ký tự")
    
    new_hash = hash_password(request.new_password)
    auth_repo.update_password_hash(conn, user.user_id, new_hash)
    conn.commit()

    return {
        "success": True,
        "message": "Đổi mật khẩu thành công"
    }

@router.get("/me")
def get_me(current_user: AuthUser = Depends(get_current_user)) -> dict:
    """GET /api/v1/auth/me returns current authenticated user details."""
    return {
        "success": True,
        "user": {
            "id": current_user.user_id,
            "username": current_user.username,
            "name": current_user.full_name,
            "role": current_user.role
        }
    }

@router.post("/logout")
def logout(current_user: AuthUser = Depends(get_current_user)) -> dict:
    """POST /api/v1/auth/logout."""
    return {
        "success": True,
        "message": "Đăng xuất thành công"
    }
