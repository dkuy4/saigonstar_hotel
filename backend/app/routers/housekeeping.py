import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
import oracledb

from app.db import get_conn
from app.context import set_db_context
from app.security import require_role, AuthUser
from app.schemas.housekeeping import (
    HousekeepingTaskListResponse,
    HousekeepingActionResponse
)
from app.repositories.housekeeping_repo import HousekeepingRepository
from app.repositories.room_repo import RoomRepository
from app.errors import BusinessException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/housekeeping", tags=["Housekeeping"])

@router.get(
    "/tasks",
    response_model=HousekeepingTaskListResponse,
    summary="Danh sách phòng cần xử lý buồng phòng (F15, FR-24, FR-25, AC-16)"
)
def get_housekeeping_tasks(
    status: Optional[str] = Query(
        None,
        description="Lọc theo trạng thái (DANG_DON, TRONG, BAO_TRI, ALL). Mặc định là DANG_DON."
    ),
    floor: Optional[int] = Query(None, description="Lọc theo số tầng"),
    user: AuthUser = Depends(require_role("BUONG_PHONG", "QUAN_LY", "LE_TAN")),
    conn: oracledb.Connection = Depends(get_conn)
):
    """
    Danh sách phòng dành cho nhân viên buồng phòng.
    Quy định bảo mật AC-16, FR-25: Tuyệt đối không trả về thông tin khách hàng hoặc giá tiền phòng.
    """
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="QUAY")
    tasks = HousekeepingRepository.get_tasks(conn, status=status, floor=floor)
    return {
        "items": tasks,
        "total": len(tasks)
    }

@router.post(
    "/{room_id}/start",
    response_model=HousekeepingActionResponse,
    summary="Ghi nhận bắt đầu dọn phòng (F15, FR-24, US-16)"
)
def start_cleaning(
    room_id: int,
    user: AuthUser = Depends(require_role("BUONG_PHONG", "QUAN_LY", "LE_TAN")),
    conn: oracledb.Connection = Depends(get_conn)
):
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="QUAY")
    existing = RoomRepository.get_room_by_id(conn, room_id)
    if not existing:
        raise BusinessException(code="ROOM_NOT_FOUND", detail=f"Không tìm thấy phòng id {room_id}")

    HousekeepingRepository.start_cleaning(conn, room_id)
    return {
        "success": True,
        "message": f"Bắt đầu dọn phòng {existing['roomNumber']}",
        "roomId": room_id,
        "status": "DANG_DON"
    }

@router.post(
    "/{room_id}/done",
    response_model=HousekeepingActionResponse,
    summary="Xác nhận hoàn tất dọn phòng, đưa phòng về trạng thái TRONG (F15, FR-24, US-16)"
)
def finish_cleaning(
    room_id: int,
    user: AuthUser = Depends(require_role("BUONG_PHONG", "QUAN_LY", "LE_TAN")),
    conn: oracledb.Connection = Depends(get_conn)
):
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="QUAY")
    existing = RoomRepository.get_room_by_id(conn, room_id)
    if not existing:
        raise BusinessException(code="ROOM_NOT_FOUND", detail=f"Không tìm thấy phòng id {room_id}")

    HousekeepingRepository.finish_cleaning(conn, room_id)
    return {
        "success": True,
        "message": f"Đã dọn xong phòng {existing['roomNumber']}, phòng đã sẵn sàng đón khách",
        "roomId": room_id,
        "status": "TRONG"
    }
