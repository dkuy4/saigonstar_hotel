import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
import oracledb

from app.db import get_conn
from app.errors import BusinessException
from app.security import require_role, AuthUser
from app.schemas.user import (
    UserItem,
    UserListResponse,
    UserCreateRequest,
    UserCreateResponse,
    UserUpdateRequest,
    UserLockRequest,
    UserResetPasswordResponse
)
from app.repositories import user_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Staff Management (F17)"])


@router.get("", response_model=UserListResponse)
def get_users(
    vaiTro: Optional[str] = Query(None, alias="vaiTro"),
    trangThai: Optional[str] = Query(None, alias="trangThai"),
    q: Optional[str] = Query(None),
    conn: oracledb.Connection = Depends(get_conn),
    current_user: AuthUser = Depends(require_role("QUAN_LY"))
):
    """
    GET /api/v1/users
    Lists employee accounts with filters for role, status, and search query.
    Requires QUAN_LY role.
    """
    users = user_repo.list_users(conn, vai_tro=vaiTro, trang_thai=trangThai, q=q)
    return UserListResponse(
        success=True,
        total=len(users),
        data=users
    )


@router.post("", response_model=UserCreateResponse)
def create_user(
    body: UserCreateRequest,
    request: Request,
    conn: oracledb.Connection = Depends(get_conn),
    current_user: AuthUser = Depends(require_role("QUAN_LY"))
):
    """
    POST /api/v1/users
    Creates a new employee account with temporary password and phai_doi_mat_khau=TRUE.
    Requires QUAN_LY role.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    user, temp_password = user_repo.create_user(
        conn=conn,
        username=body.tenDangNhap,
        full_name=body.hoTen,
        role=body.vaiTro,
        password=body.matKhau,
        current_user=current_user,
        ip=client_ip
    )
    conn.commit()
    return UserCreateResponse(
        success=True,
        user=user,
        matKhauTam=temp_password,
        message="Tạo tài khoản thành công"
    )


@router.put("/{user_id}", response_model=dict)
def update_user(
    user_id: int,
    body: UserUpdateRequest,
    request: Request,
    conn: oracledb.Connection = Depends(get_conn),
    current_user: AuthUser = Depends(require_role("QUAN_LY"))
):
    """
    PUT /api/v1/users/{user_id}
    Updates employee full name and role.
    Requires QUAN_LY role.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    updated_user = user_repo.update_user(
        conn=conn,
        user_id=user_id,
        full_name=body.hoTen,
        new_role=body.vaiTro,
        current_user=current_user,
        ip=client_ip
    )
    conn.commit()
    return {
        "success": True,
        "user": updated_user,
        "message": "Cập nhật tài khoản thành công"
    }


@router.post("/{user_id}/lock", response_model=dict)
def lock_user(
    user_id: int,
    body: UserLockRequest,
    request: Request,
    conn: oracledb.Connection = Depends(get_conn),
    current_user: AuthUser = Depends(require_role("QUAN_LY"))
):
    """
    POST /api/v1/users/{user_id}/lock
    Locks or unlocks an employee account.
    Requires QUAN_LY role.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    updated_user = user_repo.toggle_lock(
        conn=conn,
        user_id=user_id,
        khoa=body.khoa,
        current_user=current_user,
        ip=client_ip
    )
    conn.commit()
    action = "Khóa" if body.khoa else "Mở khóa"
    return {
        "success": True,
        "user": updated_user,
        "message": f"{action} tài khoản thành công"
    }


@router.post("/{user_id}/reset-password", response_model=UserResetPasswordResponse)
def reset_password(
    user_id: int,
    request: Request,
    conn: oracledb.Connection = Depends(get_conn),
    current_user: AuthUser = Depends(require_role("QUAN_LY"))
):
    """
    POST /api/v1/users/{user_id}/reset-password
    Generates new temporary password for employee and marks phai_doi_mat_khau=TRUE.
    Requires QUAN_LY role.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    temp_password = user_repo.reset_password(
        conn=conn,
        user_id=user_id,
        current_user=current_user,
        ip=client_ip
    )
    conn.commit()
    return UserResetPasswordResponse(
        success=True,
        matKhauTam=temp_password,
        message="Đặt lại mật khẩu thành công"
    )
