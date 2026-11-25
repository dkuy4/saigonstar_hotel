import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Literal, List
from fastapi import APIRouter, Depends, Query, status
import oracledb

from app.db import get_conn
from app.errors import BusinessException
from app.security import require_role, get_current_user_optional, AuthUser
from app.context import set_db_context
from app.repositories.catalog_repo import CatalogRepository
from app.schemas.catalog import (
    RoomTypeOut, ExchangeRateOut, AvailabilityItem, AvailabilityResponse,
    RoomTypeAdminDetail, RoomTypeUpdateRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Catalog & Availability"])

@router.get(
    "/room-types",
    summary="Danh sách hạng phòng và bảng giá hiện hành (FR-02, FR-51, F16.2)"
)
def get_room_types(
    lang: str = Query("vi", description="Mã ngôn ngữ (vi, en, zh-CN, ko, ja, es, fr) hoặc 'all' cho quản trị"),
    user: Optional[AuthUser] = Depends(get_current_user_optional),
    conn: oracledb.Connection = Depends(get_conn)
):
    if lang == "all":
        # Requires manager role
        if not user or user.role != "QUAN_LY":
            raise BusinessException("FORBIDDEN", "Chỉ quản lý mới được xem đầy đủ bản dịch 7 ngôn ngữ")
        set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="QUAY")
        return CatalogRepository.get_room_types_admin(conn)

    return CatalogRepository.get_room_types(conn, lang=lang)

@router.put(
    "/room-types/{room_type_id}",
    summary="Cập nhật sức chứa và bản dịch 7 ngôn ngữ của hạng phòng (F16.2)"
)
def update_room_type(
    room_type_id: int,
    data: RoomTypeUpdateRequest,
    user: AuthUser = Depends(require_role("QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="QUAY")
    CatalogRepository.update_room_type(
        conn,
        room_type_id=room_type_id,
        capacity=data.capacity,
        image_url=data.image_url,
        translations=[t.model_dump() for t in data.translations]
    )
    # Return updated list
    return CatalogRepository.get_room_types_admin(conn)

@router.get(
    "/exchange-rates",
    response_model=List[ExchangeRateOut],
    summary="Bảng tỷ giá ngoại tệ hiện hành (FR-10)"
)
def get_exchange_rates(
    conn: oracledb.Connection = Depends(get_conn)
):
    return CatalogRepository.get_exchange_rates(conn)

@router.post(
    "/exchange-rates/manual",
    summary="Nhập tay tỷ giá ngoại tệ (F13, FR-10, D-37)"
)
def update_manual_exchange_rates(
    payload: dict,
    user: AuthUser = Depends(require_role("QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    from app.workers.ty_gia import ExchangeRateService
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="API", ly_do="Cập nhật tỷ giá ngoại tệ thủ công")
    rates_raw = payload.get("rates", [])
    if isinstance(rates_raw, list):
        rates_dict = {item.get("currency"): item.get("rateVnd") or item.get("rate_vnd") for item in rates_raw}
    elif isinstance(rates_raw, dict):
        rates_dict = rates_raw
    else:
        rates_dict = {}
    updated = ExchangeRateService.save_manual_rates(conn, rates_dict)
    return {
        "status": "success",
        "message": f"Đã cập nhật {len(rates_dict)} tỷ giá ngoại tệ thành công.",
        "rates": updated
    }

@router.get(
    "/availability",
    response_model=AvailabilityResponse,
    summary="Tìm kiếm phòng trống và tính giá đã gồm VAT (FR-03, FR-11, AC-04, AC-05)"
)
def search_availability(
    type: Literal["NGAY", "GIO"] = Query(..., description="Loại đặt: NGAY hoặc GIO"),
    checkin: datetime = Query(..., description="Thời điểm nhận phòng (ISO 8601)"),
    checkout: datetime = Query(..., description="Thời điểm trả phòng (ISO 8601)"),
    guests: Optional[int] = Query(None, ge=1, le=10, description="Số khách"),
    room_type: Optional[str] = Query(None, description="Lọc theo mã hạng (STANDARD, SUPERIOR, DELUXE, SUITE)"),
    lang: str = Query("vi", description="Ngôn ngữ hiển thị"),
    conn: oracledb.Connection = Depends(get_conn)
):
    # Ensure timezone awareness (Default Vietnam UTC+7 if naive)
    if checkin.tzinfo is None:
        checkin = checkin.replace(tzinfo=timezone(timedelta(hours=7)))
    if checkout.tzinfo is None:
        checkout = checkout.replace(tzinfo=timezone(timedelta(hours=7)))

    if checkout <= checkin:
        raise BusinessException("VALIDATION_ERROR", "Thời điểm trả phòng phải sau thời điểm nhận phòng")

    # Business Rule BR-02, AC-05: Hourly only allowed for Standard
    if type == "GIO":
        if room_type and room_type.upper() != "STANDARD":
            raise BusinessException("HOURLY_NOT_ALLOWED", f"Hạng {room_type} không cho thuê theo giờ (AC-05)")

        # BR-03: 15-minute intervals
        if checkin.minute % 15 != 0 or checkin.second != 0:
            raise BusinessException("VALIDATION_ERROR", "Giờ nhận phòng theo giờ phải theo bước 15 phút (BR-03)")

        # BR-03: Whole hours
        diff_seconds = (checkout - checkin).total_seconds()
        if diff_seconds % 3600 != 0:
            raise BusinessException("VALIDATION_ERROR", "Thời gian thuê theo giờ phải là số giờ nguyên (BR-03)")

        hours = diff_seconds / 3600
        if hours < 1:
            raise BusinessException("VALIDATION_ERROR", "Thời gian thuê theo giờ tối thiểu 1 giờ")
        if hours > 24:
            raise BusinessException("VALIDATION_ERROR", "Thời gian thuê theo giờ tối đa 24 giờ (BR-05)")

    items = CatalogRepository.get_availability(
        conn=conn,
        loai_dat=type,
        checkin=checkin,
        checkout=checkout,
        guests=guests,
        lang=lang
    )

    if room_type:
        items = [item for item in items if item["code"].upper() == room_type.upper()]

    return AvailabilityResponse(
        type=type,
        checkin=checkin,
        checkout=checkout,
        guests=guests,
        items=items
    )


@router.get(
    "/availability/rooms",
    summary="Danh sách số phòng còn trống cho hạng phòng và khoảng thời gian lưu trú đã chọn"
)
def get_available_rooms_for_type(
    room_type: str = Query(..., alias="roomType", description="Mã hạng phòng (STANDARD, SUPERIOR...)"),
    checkin: datetime = Query(..., description="Thời điểm nhận phòng (ISO 8601)"),
    checkout: datetime = Query(..., description="Thời điểm trả phòng (ISO 8601)"),
    conn: oracledb.Connection = Depends(get_conn)
):
    from app.repositories.booking_repo import BookingRepository
    if checkin.tzinfo is None:
        checkin = checkin.replace(tzinfo=timezone(timedelta(hours=7)))
    if checkout.tzinfo is None:
        checkout = checkout.replace(tzinfo=timezone(timedelta(hours=7)))

    if checkout <= checkin:
        raise BusinessException("VALIDATION_ERROR", "Thời điểm trả phòng phải sau thời điểm nhận phòng")

    room_type_id = BookingRepository.get_room_type_id(conn, room_type)
    if not room_type_id:
        return {"rooms": []}

    rooms = BookingRepository.get_suggested_rooms(conn, room_type_id, checkin, checkout)
    sorted_rooms = sorted(rooms, key=lambda x: (x.get("floor", 1), x.get("room_number", "")))
    return {"rooms": sorted_rooms}
