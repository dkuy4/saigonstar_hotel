from typing import List
from fastapi import APIRouter, Depends, Request, status
import oracledb

from app.db import get_conn
from app.security import require_role, AuthUser
from app.schemas.setting import (
    SettingItem,
    SettingUpdateRequest,
    SettingUpdateResponse
)
from app.repositories.setting_repo import SettingRepository

router = APIRouter(prefix="/settings", tags=["Settings (Tham số cấu hình & VAT)"])

@router.get("", response_model=List[SettingItem])
def get_settings(
    current_user: AuthUser = Depends(require_role("QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    """
    Lấy toàn bộ danh sách tham số cấu hình hệ thống và thuế suất VAT (yêu cầu quyền QUAN_LY).
    Bao gồm giá trị hiện hành, khoảng giới hạn, đơn vị, cảnh báo và toàn bộ lịch sử thay đổi.
    """
    return SettingRepository.get_settings(conn)

@router.put("/{ma}", response_model=SettingUpdateResponse)
def update_setting(
    ma: str,
    req: SettingUpdateRequest,
    request: Request,
    current_user: AuthUser = Depends(require_role("QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    """
    Cập nhật giá trị tham số cấu hình hoặc thuế suất VAT (yêu cầu quyền QUAN_LY):
    - Kiểm tra tính hợp lệ của giá trị (khoảng số, định dạng giờ...).
    - Kiểm tra ngày hiệu lực không ở quá khứ.
    - Chặn chồng chéo thời gian hiệu lực (CONFIG_OVERLAP).
    - Cập nhật hiệu lực dòng cũ và thêm dòng giá trị mới.
    - Ghi nhận đầy đủ vào nhật ký kiểm toán NHAT_KY_KIEM_TOAN kèm lý do.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    user_id = current_user.user_id if hasattr(current_user, "user_id") else current_user.get("user_id")
    user_role = current_user.role if hasattr(current_user, "role") else current_user.get("role", "QUAN_LY")
    
    res = SettingRepository.update_setting(
        conn=conn,
        ma=ma,
        gia_tri=req.gia_tri,
        hieu_luc_tu=req.hieu_luc_tu,
        ly_do=req.ly_do,
        user_id=user_id,
        user_role=user_role,
        ip=client_ip
    )
    return SettingUpdateResponse(**res)
