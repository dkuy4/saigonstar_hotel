import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
import oracledb

from app.db import get_conn
from app.context import set_db_context
from app.security import require_role, AuthUser
from app.workers.scheduler import BackgroundJobManager
from app.workers.ty_gia import ExchangeRateService
from app.schemas.system import (
    JobStatusResponse,
    JobRunResponse,
    RoomDiscrepancyItem,
    ManualExchangeRatesRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["System & Jobs"])

@router.get(
    "/jobs",
    response_model=List[JobStatusResponse],
    summary="Liệt kê trạng thái các tác vụ nền định kỳ (F13, FR-52, NFR-27)"
)
def get_background_jobs(
    user: AuthUser = Depends(require_role("QUAN_LY"))
):
    mgr = BackgroundJobManager.get_instance()
    jobs = mgr.get_all_jobs()
    return [JobStatusResponse(**j) for j in jobs]

@router.post(
    "/jobs/{job_id}/run",
    response_model=JobRunResponse,
    summary="Kích hoạt chạy ngay một tác vụ nền (F13, FR-52)"
)
def run_background_job_now(
    job_id: str,
    user: AuthUser = Depends(require_role("QUAN_LY"))
):
    mgr = BackgroundJobManager.get_instance()
    try:
        res = mgr.execute_job(job_id)
        return JobRunResponse(**res)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tác vụ không tồn tại: {job_id}"
        )
    except Exception as e:
        logger.error(f"Error running job {job_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi thực thi tác vụ: {str(e)}"
        )

@router.get(
    "/discrepancies",
    response_model=List[RoomDiscrepancyItem],
    summary="Kiểm tra sai lệch giữa trạng thái phòng và lịch đặt (F13, NFR-03)"
)
def get_room_schedule_discrepancies(
    user: AuthUser = Depends(require_role("QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    mgr = BackgroundJobManager.get_instance()
    discrepancies = mgr.get_discrepancies(conn)
    return [RoomDiscrepancyItem(**d) for d in discrepancies]

@router.post(
    "/exchange-rates/manual",
    summary="Nhập tay tỷ giá ngoại tệ (F13, FR-10, D-37)"
)
def update_manual_exchange_rates(
    payload: ManualExchangeRatesRequest,
    user: AuthUser = Depends(require_role("QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="API", ly_do="Cập nhật tỷ giá ngoại tệ thủ công")
    rates_dict = {item.currency: item.rate_vnd for item in payload.rates}
    updated = ExchangeRateService.save_manual_rates(conn, rates_dict)
    return {
        "status": "success",
        "message": f"Đã cập nhật {len(rates_dict)} tỷ giá ngoại tệ thành công.",
        "rates": updated
    }
