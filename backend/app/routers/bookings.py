from datetime import datetime, timezone
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Header, Request, status, Query, File, UploadFile
import oracledb

from app.db import get_conn
from app.context import set_db_context
from app.errors import BusinessException
from app.security import decode_access_token, create_booking_token, require_role, AuthUser
from app.schemas.booking import (
    BookingCreate,
    BookingOut,
    BookingLookupRequest,
    BookingLookupResponse,
    RefundPreviewResponse,
    BookingCancelRequest,
    BookingCancelResponse,
    BookingRescheduleRequest,
    BookingRescheduleResponse,
    BookingListResponse,
    BookingStaffDetailResponse,
    CheckInRequest,
    CheckInResponse,
    BookingExtendRequest,
    BookingExtendPreviewResponse,
    BookingExtendResponse
)
from app.repositories.booking_repo import BookingRepository
from app.services.storage import save_document_photo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bookings", tags=["Bookings"])

def get_optional_staff_user(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ")[1]
    try:
        payload = decode_access_token(token)
        if payload.get("role") in ("LE_TAN", "QUAN_LY", "BUONG_PHONG"):
            return payload
    except Exception:
        pass
    return None

def check_booking_authorization(
    booking: dict,
    staff_user: Optional[dict] = None,
    booking_token: Optional[str] = None,
    auth_header: Optional[str] = None
):
    if staff_user and staff_user.get("role") in ("LE_TAN", "QUAN_LY"):
        return
    token = booking_token
    if not token and auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    if token:
        try:
            payload = decode_access_token(token)
            if payload.get("type") == "booking_guest" and payload.get("booking_code") == booking["booking_code"].upper():
                return
        except Exception:
            pass
    raise BusinessException("UNAUTHORIZED", "Quý khách vui lòng tra cứu đơn bằng mã và email trước khi thực hiện thao tác này")

@router.post(
    "",
    response_model=BookingOut,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo đơn đặt phòng mới (FR-04, FR-05, FR-06, FR-13, AC-01, AC-02, AC-03)"
)
def create_booking(
    payload: BookingCreate,
    staff_user: Optional[dict] = Depends(get_optional_staff_user),
    conn: oracledb.Connection = Depends(get_conn)
):
    if staff_user and staff_user.get("role") in ("LE_TAN", "QUAN_LY"):
        channel = "QUAY"
        set_db_context(conn, nguoi_id=staff_user.get("user_id"), vai_tro=staff_user.get("role"), kenh=channel)
        room_id = payload.room_id
    else:
        channel = "WEB"
        set_db_context(conn, nguoi_id=None, vai_tro="KHACH", kenh=channel)
        room_id = None
        if not payload.agree_terms:
            raise BusinessException(
                "VALIDATION_ERROR",
                "Quý khách phải đồng ý với chính sách hủy phòng và quy định vắng mặt (no-show)"
            )

    if payload.type == "GIO" and payload.room_type.upper() != "STANDARD":
        raise BusinessException(
            "HOURLY_NOT_ALLOWED",
            f"Hạng {payload.room_type} không cho thuê theo giờ (AC-05)"
        )

    checkin = payload.checkin
    checkout = payload.checkout
    if checkin.tzinfo is None:
        checkin = checkin.replace(tzinfo=timezone.utc)
    if checkout.tzinfo is None:
        checkout = checkout.replace(tzinfo=timezone.utc)

    agree_time = datetime.now(timezone.utc)

    booking = BookingRepository.create_booking(
        conn=conn,
        type_=payload.type,
        room_type=payload.room_type,
        room_id=room_id,
        checkin=checkin,
        checkout=checkout,
        guests=payload.guests,
        payment_method=payload.payment_method,
        channel=channel,
        customer=payload.customer,
        lang=payload.lang,
        agree_time=agree_time
    )

    return booking

@router.post(
    "/lookup",
    response_model=BookingLookupResponse,
    summary="Khách tra cứu đơn đặt phòng bằng mã đơn và email (FR-09, US-05)"
)
def lookup_booking(
    payload: BookingLookupRequest,
    conn: oracledb.Connection = Depends(get_conn)
):
    set_db_context(conn, nguoi_id=None, vai_tro="KHACH", kenh="WEB")
    booking = BookingRepository.get_booking_by_code_and_email(conn, payload.booking_code, payload.email)
    if not booking:
        raise BusinessException("BOOKING_NOT_FOUND", "Không tìm thấy thông tin đơn đặt phòng")

    token = create_booking_token(booking["booking_code"], payload.email)
    return BookingLookupResponse(
        token=token,
        booking=booking
    )

@router.get(
    "/{id_or_code}/refund-preview",
    response_model=RefundPreviewResponse,
    summary="Xem trước số tiền hoàn dự kiến khi hủy đơn (FR-09, BR-24, AC-09)"
)
def refund_preview(
    id_or_code: str,
    x_booking_token: Optional[str] = Header(None, alias="X-Booking-Token"),
    authorization: Optional[str] = Header(None),
    staff_user: Optional[dict] = Depends(get_optional_staff_user),
    conn: oracledb.Connection = Depends(get_conn)
):
    booking = BookingRepository.get_booking_by_id_or_code(conn, id_or_code)
    if not booking:
        raise BusinessException("BOOKING_NOT_FOUND", f"Không tìm thấy đơn đặt phòng {id_or_code}")

    check_booking_authorization(booking, staff_user, x_booking_token, authorization)
    set_db_context(
        conn,
        nguoi_id=staff_user.get("user_id") if staff_user else None,
        vai_tro=staff_user.get("role") if staff_user else "KHACH",
        kenh="QUAY" if staff_user else "WEB"
    )

    preview = BookingRepository.get_refund_preview(conn, booking["id"])
    return RefundPreviewResponse(**preview)

@router.post(
    "/{id_or_code}/cancel",
    response_model=BookingCancelResponse,
    summary="Hủy đơn đặt phòng (FR-09, BR-14, BR-24, AC-09, AC-10)"
)
def cancel_booking(
    id_or_code: str,
    payload: BookingCancelRequest = BookingCancelRequest(),
    x_booking_token: Optional[str] = Header(None, alias="X-Booking-Token"),
    authorization: Optional[str] = Header(None),
    staff_user: Optional[dict] = Depends(get_optional_staff_user),
    conn: oracledb.Connection = Depends(get_conn)
):
    booking = BookingRepository.get_booking_by_id_or_code(conn, id_or_code)
    if not booking:
        raise BusinessException("BOOKING_NOT_FOUND", f"Không tìm thấy đơn đặt phòng {id_or_code}")

    check_booking_authorization(booking, staff_user, x_booking_token, authorization)
    set_db_context(
        conn,
        nguoi_id=staff_user.get("user_id") if staff_user else None,
        vai_tro=staff_user.get("role") if staff_user else "KHACH",
        kenh="QUAY" if staff_user else "WEB"
    )

    res = BookingRepository.cancel_booking(conn, booking["id"], payload.reason or "Khách hủy trên website")
    return BookingCancelResponse(**res)

@router.put(
    "/{id_or_code}",
    response_model=BookingRescheduleResponse,
    summary="Đổi ngày giờ hoặc phòng cho đơn đã chốt (FR-09, BR-15, D-29)"
)
def reschedule_booking(
    id_or_code: str,
    payload: BookingRescheduleRequest,
    x_booking_token: Optional[str] = Header(None, alias="X-Booking-Token"),
    authorization: Optional[str] = Header(None),
    staff_user: Optional[dict] = Depends(get_optional_staff_user),
    conn: oracledb.Connection = Depends(get_conn)
):
    booking = BookingRepository.get_booking_by_id_or_code(conn, id_or_code)
    if not booking:
        raise BusinessException("BOOKING_NOT_FOUND", f"Không tìm thấy đơn đặt phòng {id_or_code}")

    check_booking_authorization(booking, staff_user, x_booking_token, authorization)
    set_db_context(
        conn,
        nguoi_id=staff_user.get("user_id") if staff_user else None,
        vai_tro=staff_user.get("role") if staff_user else "KHACH",
        kenh="QUAY" if staff_user else "WEB"
    )

    checkin = payload.checkin
    checkout = payload.checkout
    if checkin.tzinfo is None:
        checkin = checkin.replace(tzinfo=timezone.utc)
    if checkout.tzinfo is None:
        checkout = checkout.replace(tzinfo=timezone.utc)

    room_id = payload.room_id if staff_user else None

    res = BookingRepository.reschedule_booking(
        conn=conn,
        booking_id=booking["id"],
        checkin=checkin,
        checkout=checkout,
        room_type=payload.room_type,
        room_id=room_id
    )
    return BookingRescheduleResponse(**res)

@router.get(
    "",
    response_model=BookingListResponse,
    summary="Tìm kiếm, tra cứu và phân trang danh sách đơn đặt phòng cho Lễ tân & Quản lý (FR-15, US-08)"
)
def search_bookings(
    q: Optional[str] = Query(None, description="Từ khóa: mã đơn, tên, số điện thoại, email, số phòng"),
    status: Optional[str] = Query(None, description="Trạng thái đơn (HOLD, CONFIRMED, CHECKED_IN, CHECKED_OUT, CANCELLED, EXPIRED, NO_SHOW)"),
    from_date: Optional[datetime] = Query(None, alias="fromDate"),
    to_date: Optional[datetime] = Query(None, alias="toDate"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    user: AuthUser = Depends(require_role("LE_TAN", "QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="QUAY")
    result = BookingRepository.search_bookings(
        conn=conn,
        q=q,
        status=status,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size
    )
    return BookingListResponse(**result)

@router.get(
    "/{id_or_code}",
    response_model=BookingStaffDetailResponse,
    summary="Chi tiết đơn đặt phòng toàn diện (FR-09, FR-15, US-09)"
)
def get_booking(
    id_or_code: str,
    conn: oracledb.Connection = Depends(get_conn)
):
    booking = BookingRepository.get_staff_booking_detail(conn, id_or_code)
    if not booking:
        raise BusinessException("BOOKING_NOT_FOUND", f"Không tìm thấy đơn đặt phòng {id_or_code}")
    return BookingStaffDetailResponse(**booking)

@router.post(
    "/{id}/check-in",
    response_model=CheckInResponse,
    summary="Thực hiện nhận phòng / Check-in cho đơn đặt phòng (F08, FR-16, US-10)"
)
def check_in(
    id: int,
    payload: CheckInRequest,
    user: AuthUser = Depends(require_role("LE_TAN", "QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="QUAY")
    result = BookingRepository.check_in(
        conn=conn,
        booking_id=id,
        id_type=payload.id_type,
        id_number=payload.id_number,
        nationality=payload.nationality,
        photo_url=payload.photo_url
    )
    return CheckInResponse(**result)

@router.post(
    "/{id}/upload-document",
    summary="Tải ảnh giấy tờ tùy thân của khách lưu trú ngoài DB (NFR-13, F08)"
)
async def upload_document_photo(
    id: int,
    file: UploadFile = File(...),
    user: AuthUser = Depends(require_role("LE_TAN", "QUAN_LY")),
):
    photo_url = await save_document_photo(file)
    return {"photo_url": photo_url}

@router.get(
    "/{id}/extend-preview",
    response_model=BookingExtendPreviewResponse,
    summary="Xem trước chi phí và kiểm tra xung đột khi gia hạn lưu trú (F09, BR-33, BR-34)"
)
def extend_preview(
    id: int,
    units: int = Query(1, ge=1, description="Số đêm (NGAY) hoặc số giờ (GIO) muốn gia hạn thêm"),
    user: AuthUser = Depends(require_role("LE_TAN", "QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="QUAY")
    res = BookingRepository.preview_extend(conn=conn, booking_id=id, units=units)
    return BookingExtendPreviewResponse(**res)

@router.post(
    "/{id}/extend",
    response_model=BookingExtendResponse,
    summary="Gia hạn lưu trú cho đơn đang CHECKED_IN (F09, FR-17, US-11, BR-33, BR-34, AC-12)"
)
def extend_booking(
    id: int,
    payload: BookingExtendRequest,
    user: AuthUser = Depends(require_role("LE_TAN", "QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="QUAY")
    res = BookingRepository.extend_booking(conn=conn, booking_id=id, units=payload.units)
    return BookingExtendResponse(**res)
