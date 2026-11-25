from datetime import datetime
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
import oracledb

from app.db import get_conn
from app.context import set_db_context
from app.security import require_role, AuthUser
from app.schemas.room import (
    RoomBoardResponse, RoomAdminListResponse, RoomAdminItem,
    RoomCreateRequest, RoomUpdateRequest, AffectedBooking,
    MaintenanceRequest, MaintenanceResponse
)
from app.repositories.room_repo import RoomRepository
from app.errors import BusinessException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rooms", tags=["Rooms"])

@router.get(
    "/board",
    response_model=RoomBoardResponse,
    summary="Sơ đồ phòng trực quan theo tầng tại một thời điểm (FR-12, US-15, BR-40)"
)
def get_room_board(
    at: Optional[datetime] = Query(None, description="Thời điểm xem sơ đồ phòng (ISO 8601). Mặc định là hiện tại."),
    user: AuthUser = Depends(require_role("LE_TAN", "QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="QUAY")
    board = RoomRepository.get_room_board(conn, at_time=at)
    return board

# --- F16.1 Admin Endpoints for Room Management (Chỉ Quản lý) ---

@router.get(
    "",
    response_model=RoomAdminListResponse,
    summary="Danh sách phòng quản trị có lọc và phân trang (F16.1)"
)
def get_rooms_admin(
    floor: Optional[int] = Query(None, description="Lọc theo tầng"),
    room_type: Optional[str] = Query(None, alias="roomType", description="Lọc theo mã hạng (STANDARD, SUPERIOR...)"),
    status: Optional[str] = Query(None, description="Lọc theo trạng thái (TRONG, DANG_O...)"),
    is_active: Optional[bool] = Query(None, alias="isActive", description="Lọc theo hoạt động"),
    q: Optional[str] = Query(None, description="Tìm kiếm mã phòng hoặc ghi chú"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    user: AuthUser = Depends(require_role("QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="QUAY")
    res = RoomRepository.get_rooms_admin(
        conn,
        floor=floor,
        room_type=room_type,
        status=status,
        is_active=is_active,
        query=q,
        page=page,
        page_size=page_size
    )
    return res

@router.get(
    "/{room_id}",
    response_model=RoomAdminItem,
    summary="Chi tiết một phòng (F16.1)"
)
def get_room_detail(
    room_id: int,
    user: AuthUser = Depends(require_role("QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="QUAY")
    room = RoomRepository.get_room_by_id(conn, room_id)
    if not room:
        raise BusinessException(code="ROOM_NOT_FOUND", detail=f"Không tìm thấy phòng id {room_id}")
    return room

@router.get(
    "/{room_id}/affected-bookings",
    response_model=List[AffectedBooking],
    summary="Danh sách các đơn tương lai bị ảnh hưởng của phòng (F15, F16.1, BR-41)"
)
def get_room_affected_bookings(
    room_id: int,
    user: AuthUser = Depends(require_role("LE_TAN", "QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="QUAY")
    return RoomRepository.get_affected_bookings(conn, room_id)

@router.post(
    "/{room_id}/maintenance",
    response_model=MaintenanceResponse,
    summary="Đưa phòng vào trạng thái bảo trì (F15, BR-40, BR-41)"
)
def set_room_maintenance(
    room_id: int,
    data: MaintenanceRequest,
    user: AuthUser = Depends(require_role("LE_TAN", "QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="QUAY")
    existing = RoomRepository.get_room_by_id(conn, room_id)
    if not existing:
        raise BusinessException(code="ROOM_NOT_FOUND", detail=f"Không tìm thấy phòng id {room_id}")

    if not data.ignore_affected_bookings:
        affected = RoomRepository.get_affected_bookings(conn, room_id)
        if affected:
            raise BusinessException(
                code="MAINTENANCE_HAS_BOOKINGS",
                detail=f"Phòng hiện có {len(affected)} đơn đặt tương lai bị ảnh hưởng, vui lòng xác nhận chuyển phòng hoặc tiếp tục",
                data=affected
            )

    RoomRepository.start_maintenance(
        conn,
        room_id=room_id,
        reason=data.reason,
        ignore_affected_bookings=data.ignore_affected_bookings
    )
    return {
        "success": True,
        "message": f"Phòng {existing['roomNumber']} đã được đưa vào trạng thái bảo trì",
        "roomId": room_id,
        "status": "BAO_TRI"
    }

@router.post(
    "/{room_id}/end-maintenance",
    response_model=MaintenanceResponse,
    summary="Kết thúc bảo trì phòng (F15, BR-40)"
)
def end_room_maintenance(
    room_id: int,
    user: AuthUser = Depends(require_role("LE_TAN", "QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="QUAY")
    existing = RoomRepository.get_room_by_id(conn, room_id)
    if not existing:
        raise BusinessException(code="ROOM_NOT_FOUND", detail=f"Không tìm thấy phòng id {room_id}")

    RoomRepository.end_maintenance(conn, room_id)
    return {
        "success": True,
        "message": f"Phòng {existing['roomNumber']} đã kết thúc bảo trì và trở về trạng thái trống",
        "roomId": room_id,
        "status": "TRONG"
    }

@router.post(
    "",
    response_model=RoomAdminItem,
    status_code=201,
    summary="Thêm phòng mới (F16.1)"
)
def create_room(
    data: RoomCreateRequest,
    user: AuthUser = Depends(require_role("QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="QUAY")
    new_id = RoomRepository.create_room(
        conn,
        room_number=data.room_number,
        floor=data.floor,
        room_type_id=data.room_type_id,
        notes=data.notes
    )
    room = RoomRepository.get_room_by_id(conn, new_id)
    return room

@router.put(
    "/{room_id}",
    response_model=RoomAdminItem,
    summary="Cập nhật thông tin phòng hoặc ngưng dùng (F16.1)"
)
def update_room(
    room_id: int,
    data: RoomUpdateRequest,
    user: AuthUser = Depends(require_role("QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="QUAY")
    existing = RoomRepository.get_room_by_id(conn, room_id)
    if not existing:
        raise BusinessException(code="ROOM_NOT_FOUND", detail=f"Không tìm thấy phòng id {room_id}")

    # Check if deactivating or changing room type while future bookings exist
    will_deactivate = data.is_active is False and existing["isActive"] is True
    will_change_type = data.room_type_id is not None and data.room_type_id != existing["roomTypeId"]

    if will_deactivate or will_change_type:
        affected = RoomRepository.get_affected_bookings(conn, room_id)
        if affected:
            raise BusinessException(
                code="ROOM_HAS_BOOKINGS",
                detail=f"Phòng hiện có {len(affected)} đơn đặt tương lai, vui lòng chuyển phòng trước khi thay đổi",
                data=affected
            )

    RoomRepository.update_room(
        conn,
        room_id=room_id,
        room_number=data.room_number,
        floor=data.floor,
        room_type_id=data.room_type_id,
        is_active=data.is_active,
        notes=data.notes
    )
    updated = RoomRepository.get_room_by_id(conn, room_id)
    return updated
