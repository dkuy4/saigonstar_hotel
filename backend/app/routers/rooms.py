from datetime import datetime
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
import oracledb

from app.db import get_conn
from app.context import set_db_context
from app.security import require_role, AuthUser
from app.schemas.room import RoomBoardResponse
from app.repositories.room_repo import RoomRepository

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
