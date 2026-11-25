from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Request, status
import oracledb

from app.db import get_conn
from app.security import require_role, AuthUser
from app.schemas.price import (
    PriceItem,
    PriceChangeRequest,
    PriceRuleValidationRequest,
    PriceRuleValidationResponse
)
from app.repositories.price_repo import PriceRepository

router = APIRouter(prefix="/prices", tags=["Prices (Bảng giá)"])

@router.get("", response_model=List[PriceItem])
def get_prices(
    maHang: Optional[str] = Query(None, description="Lọc theo mã hạng phòng (STANDARD, SUPERIOR, DELUXE, SUITE)"),
    loaiGia: Optional[str] = Query(None, description="Lọc theo loại giá (NGAY, GIO)"),
    at: Optional[str] = Query(None, description="Xem bảng giá tại một thời điểm (YYYY-MM-DD)"),
    current_user: AuthUser = Depends(require_role("QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    """
    Lấy danh sách bảng giá phòng và lịch sử hiệu lực (yêu cầu quyền QUAN_LY).
    Tự động tính thuế VAT và đơn giá gồm VAT tương ứng tại thời điểm hiệu lực.
    """
    return PriceRepository.get_prices(conn, ma_hang=maHang, loai_gia=loaiGia, at=at)

@router.post("/validate-rule", response_model=PriceRuleValidationResponse)
def validate_price_rule(
    req: PriceRuleValidationRequest,
    current_user: AuthUser = Depends(require_role("QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    """
    Kiểm tra tức thì quy tắc giá giờ (5 lần giá giờ không vượt giá ngày).
    """
    res = PriceRepository.validate_price_rule(
        conn,
        ma_hang=req.ma_hang,
        loai_gia=req.loai_gia,
        don_gia=req.don_gia,
        hieu_luc_tu=req.hieu_luc_tu
    )
    return PriceRuleValidationResponse(**res)

@router.post("", status_code=status.HTTP_201_CREATED)
def change_price(
    req: PriceChangeRequest,
    request: Request,
    current_user: AuthUser = Depends(require_role("QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    """
    Thực hiện điều chỉnh bảng giá phòng (yêu cầu quyền QUAN_LY):
    - Kiểm tra loại giá phù hợp với hạng phòng.
    - Kiểm tra quy tắc 5 x giá giờ <= giá ngày.
    - Chặn trùng lặp / chồng chéo thời gian hiệu lực (PRICE_OVERLAP).
    - Cập nhật hiệu lực dòng cũ đến (hieuLucTu - 1 ngày) và thêm dòng giá mới.
    - Tự động ghi nhật ký kiểm toán NHAT_KY_KIEM_TOAN kèm danh tính và lý do.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    user_id = current_user.user_id if hasattr(current_user, "user_id") else current_user.get("user_id")
    user_role = current_user.role if hasattr(current_user, "role") else current_user.get("role", "QUAN_LY")
    res = PriceRepository.doi_gia(
        conn=conn,
        ma_hang=req.ma_hang,
        loai_gia=req.loai_gia,
        don_gia=req.don_gia,
        hieu_luc_tu=req.hieu_luc_tu,
        ly_do=req.ly_do,
        user_id=user_id,
        user_role=user_role,
        ip=client_ip
    )
    return res
