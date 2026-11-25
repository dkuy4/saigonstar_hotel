import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
import oracledb

from app.db import get_conn
from app.errors import BusinessException
from app.security import require_role, AuthUser
from app.schemas.audit import AuditLogsResponse, StateAtResponse
from app.repositories import audit_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs (F19)"])


def _parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    val = dt_str.strip()
    try:
        return datetime.fromisoformat(val)
    except ValueError:
        # Try YYYY-MM-DD
        try:
            return datetime.strptime(val, "%Y-%m-%d")
        except ValueError:
            raise BusinessException(
                code="VALIDATION_ERROR",
                detail=f"Định dạng ngày giờ không hợp lệ: {dt_str}. Vui lòng dùng chuẩn ISO hoặc YYYY-MM-DD."
            )


@router.get("", response_model=AuditLogsResponse)
def get_audit_logs(
    page: int = Query(1, ge=1, description="Số thứ tự trang"),
    page_size: int = Query(20, ge=5, le=100, alias="pageSize", description="Số dòng mỗi trang"),
    bang: Optional[str] = Query(None, description="Lọc theo tên bảng (DAT_PHONG, PHONG...)"),
    khoa_dong: Optional[str] = Query(None, alias="khoaDong", description="Lọc theo khóa bản ghi"),
    vai_tro: Optional[str] = Query(None, alias="vaiTro", description="Lọc theo vai trò thực hiện"),
    kenh: Optional[str] = Query(None, description="Lọc theo kênh (WEB, QUAY, HE_THONG)"),
    hanh_dong: Optional[str] = Query(None, alias="hanhDong", description="Lọc theo hành động (TAO, SUA, DOI_TRANG_THAI, XOA)"),
    nguoi_dung: Optional[str] = Query(None, alias="nguoiDung", description="Lọc theo tên đăng nhập hoặc họ tên"),
    tu_ngay: Optional[str] = Query(None, alias="tuNgay", description="Từ thời điểm (ISO/YYYY-MM-DD)"),
    den_ngay: Optional[str] = Query(None, alias="denNgay", description="Đến thời điểm (ISO/YYYY-MM-DD)"),
    conn: oracledb.Connection = Depends(get_conn),
    current_user: AuthUser = Depends(require_role("QUAN_LY")),
):
    """
    GET /api/v1/audit-logs (FR-45, FR-47, US-23, AC-14)
    Retrieve paginated audit logs with multi-attribute filtering.
    Requires QUAN_LY role.
    """
    dt_from = _parse_datetime(tu_ngay)
    dt_to = _parse_datetime(den_ngay)
    if dt_from and dt_to and dt_from > dt_to:
        raise BusinessException(
            code="VALIDATION_ERROR",
            detail="Thời điểm bắt đầu không được lớn hơn thời điểm kết thúc."
        )

    return audit_repo.list_audit_logs(
        conn=conn,
        page=page,
        page_size=page_size,
        bang=bang,
        khoa_dong=khoa_dong,
        vai_tro=vai_tro,
        kenh=kenh,
        hanh_dong=hanh_dong,
        nguoi_dung=nguoi_dung,
        tu_ngay=dt_from,
        den_ngay=dt_to,
    )


@router.get("/state-at", response_model=StateAtResponse)
def get_state_at(
    bang: str = Query(..., description="Tên bảng đối tượng (vd: DAT_PHONG, PHONG)"),
    khoa_dong: str = Query(..., alias="khoaDong", description="Khóa chính dòng đối tượng (vd: 1054, 101)"),
    thoi_diem: Optional[str] = Query(None, alias="thoiDiem", description="Thời điểm cần xem trạng thái (ISO)"),
    target_time: Optional[str] = Query(None, alias="targetTime", description="Alias cho thoiDiem"),
    conn: oracledb.Connection = Depends(get_conn),
    current_user: AuthUser = Depends(require_role("QUAN_LY")),
):
    """
    GET /api/v1/audit-logs/state-at (BR-46, AC-14)
    Point-in-time state recovery. Returns the object's state at any historical moment T.
    Requires QUAN_LY role.
    """
    raw_time = thoi_diem or target_time
    if not raw_time:
        raise BusinessException(
            code="VALIDATION_ERROR",
            detail="Vui lòng cung cấp tham số thời điểm (thoiDiem hoặc targetTime)."
        )

    dt_target = _parse_datetime(raw_time)
    if not dt_target:
        raise BusinessException(
            code="VALIDATION_ERROR",
            detail="Thời điểm tra cứu không hợp lệ."
        )

    return audit_repo.get_state_at(
        conn=conn,
        bang=bang,
        khoa_dong=khoa_dong,
        target_time=dt_target,
    )
