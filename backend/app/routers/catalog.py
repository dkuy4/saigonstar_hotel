import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Literal, List
from fastapi import APIRouter, Depends, Query, status
import oracledb

from app.db import get_conn
from app.errors import BusinessException
from app.repositories.catalog_repo import CatalogRepository
from app.schemas.catalog import RoomTypeOut, ExchangeRateOut, AvailabilityItem, AvailabilityResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Catalog & Availability"])

@router.get(
    "/room-types",
    response_model=List[RoomTypeOut],
    summary="Danh sách hạng phòng và bảng giá hiện hành (FR-02, FR-51)"
)
def get_room_types(
    lang: str = Query("vi", description="Mã ngôn ngữ (vi, en, zh-CN, ko, ja, es, fr)"),
    conn: oracledb.Connection = Depends(get_conn)
):
    return CatalogRepository.get_room_types(conn, lang=lang)

@router.get(
    "/exchange-rates",
    response_model=List[ExchangeRateOut],
    summary="Bảng tỷ giá ngoại tệ hiện hành (FR-10)"
)
def get_exchange_rates(
    conn: oracledb.Connection = Depends(get_conn)
):
    return CatalogRepository.get_exchange_rates(conn)

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
