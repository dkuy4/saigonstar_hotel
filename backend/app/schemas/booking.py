from datetime import datetime
from typing import Optional, Literal, List
from pydantic import BaseModel, Field, ConfigDict

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
PHONE_REGEX = r"^[0-9+\s\-()]{8,20}$"

class CustomerInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    full_name: str = Field(..., min_length=2, max_length=100, alias="fullName")
    phone: str = Field(..., min_length=8, max_length=20, pattern=PHONE_REGEX)
    email: str = Field(..., pattern=EMAIL_REGEX)
    nationality: str = Field("VN", min_length=2, max_length=50)
    identification_id: Optional[str] = Field(None, alias="identificationId")
    id_type: Optional[str] = Field(None, alias="idType")
    photo_url: Optional[str] = Field(None, alias="photoUrl")

class BookingCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: Literal["NGAY", "GIO"] = Field(..., alias="loaiDat")
    room_type: str = Field(..., alias="maHang")
    room_id: Optional[int] = Field(None, alias="phongId")
    checkin: datetime = Field(..., alias="nhanLuc")
    checkout: datetime = Field(..., alias="traLuc")
    guests: int = Field(..., ge=1, le=10, alias="soKhach")
    payment_method: Literal["TRUC_TUYEN", "KHI_NHAN_PHONG"] = Field(..., alias="thanhToan")
    agree_terms: bool = Field(True, alias="dongYChinhSach")
    customer: CustomerInfo
    lang: str = Field("vi", alias="ngonNgu")
    captcha_token: Optional[str] = Field(None, alias="captchaToken")

class SuggestedRoom(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    room_id: int
    room_number: str
    floor: int

class BookingOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    booking_code: str
    status: str
    room_type: str
    room_id: Optional[int] = None
    checkin: datetime
    checkout: datetime
    guests: int
    room_amount: float
    vat_rate: float
    vat_amount: float
    total_amount: float
    hold_expires_at: Optional[datetime] = None
    payment_method: str
    channel: str
    customer: CustomerInfo

class BookingLookupRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    booking_code: str = Field(..., min_length=3, max_length=50, alias="bookingCode")
    email: str = Field(..., pattern=EMAIL_REGEX)

class BookingLookupResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    token: str
    booking: BookingOut

class RefundPreviewResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    booking_id: int = Field(..., alias="bookingId")
    booking_code: str = Field(..., alias="bookingCode")
    checkin: datetime
    paid_amount: float = Field(..., alias="paidAmount")
    expected_refund: float = Field(..., alias="expectedRefund")
    reason: str
    is_eligible: bool = Field(..., alias="isEligible")

class BookingCancelRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    reason: Optional[str] = Field("Khách hủy trên website", max_length=500)

class BookingCancelResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    status: str
    booking_code: str = Field(..., alias="bookingCode")
    new_status: str = Field(..., alias="newStatus")
    refund_amount: float = Field(0.0, alias="refundAmount")
    message: str

class BookingRescheduleRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    checkin: datetime = Field(..., alias="nhanLuc")
    checkout: datetime = Field(..., alias="traLuc")
    room_type: Optional[str] = Field(None, alias="maHang")
    room_id: Optional[int] = Field(None, alias="phongId")

class BookingRescheduleResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    status: str
    booking_code: str = Field(..., alias="bookingCode")
    new_status: str = Field(..., alias="newStatus")
    old_total: float = Field(..., alias="oldTotal")
    new_total: float = Field(..., alias="newTotal")
    difference: float
    refund_amount: float = Field(0.0, alias="refundAmount")
    message: str

class BookingListItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    booking_code: str = Field(..., alias="bookingCode")
    status: str
    booking_type: str = Field(..., alias="bookingType")
    channel: str
    checkin: datetime
    checkout: datetime
    guests: int
    total_amount: float = Field(..., alias="totalAmount")
    paid_amount: float = Field(..., alias="paidAmount")
    created_at: datetime = Field(..., alias="createdAt")
    customer_name: str = Field(..., alias="customerName")
    customer_phone: str = Field(..., alias="customerPhone")
    customer_email: str = Field(..., alias="customerEmail")
    room_number: Optional[str] = Field(None, alias="roomNumber")
    room_type: Optional[str] = Field(None, alias="roomType")

class BookingListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: List[BookingListItem]
    total: int
    page: int
    page_size: int = Field(..., alias="pageSize")
    total_pages: int = Field(..., alias="totalPages")

class BookingSegment(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    segment_id: int = Field(..., alias="segmentId")
    room_id: int = Field(..., alias="roomId")
    room_number: str = Field(..., alias="roomNumber")
    floor: int
    room_type: str = Field(..., alias="roomType")
    checkin: datetime = Field(..., alias="from")
    checkout: datetime = Field(..., alias="to")

class PaymentTransaction(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    transaction_id: int = Field(..., alias="transactionId")
    channel: str
    method: str
    amount: float
    status: str
    reference_code: Optional[str] = Field(None, alias="referenceCode")
    transaction_date: datetime = Field(..., alias="transactionDate")

class RefundRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    refund_id: int = Field(..., alias="refundId")
    transaction_id: int = Field(..., alias="transactionId")
    amount: float
    reason: str
    status: str
    created_at: datetime = Field(..., alias="createdAt")

class InvoiceSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    invoice_id: int = Field(..., alias="invoiceId")
    invoice_number: int = Field(..., alias="invoiceNumber")
    total_amount: float = Field(..., alias="totalAmount")
    issued_at: datetime = Field(..., alias="issuedAt")
    created_by: Optional[str] = Field(None, alias="createdBy")

class AllowedActions(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    can_cancel: bool = False
    can_reschedule: bool = False
    can_check_in: bool = False
    can_extend: bool = False
    can_change_room: bool = False
    can_check_out: bool = False
    can_pay: bool = False

class BookingStaffDetailResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    booking_code: str
    status: str
    booking_type: str
    channel: str
    checkin: datetime
    checkout: datetime
    actual_checkin: Optional[datetime] = None
    actual_checkout: Optional[datetime] = None
    guests: int
    hold_expires_at: Optional[datetime] = None
    room_amount: float
    vat_rate: float
    vat_amount: float
    total_amount: float
    paid_amount: float
    remaining_amount: float
    cancellation_reason: Optional[str] = None
    customer: CustomerInfo
    segments: List[BookingSegment] = []
    transactions: List[PaymentTransaction] = []
    refunds: List[RefundRecord] = []
    invoice: Optional[InvoiceSummary] = None
    actions: AllowedActions

class CheckInRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_type: str = Field(..., alias="loaiGiayTo")
    id_number: str = Field(..., alias="soGiayTo")
    nationality: str = Field(default="VN", alias="quocTich")
    photo_url: Optional[str] = Field(default=None, alias="anhUrl")

class CheckInResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    booking_id: int
    booking_code: str
    room_id: int
    room_number: str
    status: str
    checked_in_at: datetime
    message: str = "Nhận phòng thành công"

class BookingExtendRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    units: int = Field(..., ge=1, alias="soDonVi", description="Số đêm (NGAY) hoặc số giờ (GIO) muốn gia hạn thêm")

class BookingExtendPreviewResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    booking_id: int
    booking_code: str
    booking_type: str
    units: int
    current_checkout: datetime
    new_checkout: datetime
    current_room_amount: float
    new_room_amount: float
    added_room_amount: float
    current_vat_amount: float
    new_vat_amount: float
    added_vat_amount: float
    current_total_amount: float
    new_total_amount: float
    added_amount: float
    switched_to_daily_rate: bool = False
    has_conflict: bool = False
    suggested_rooms: List[SuggestedRoom] = []

class BookingExtendResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    booking_id: int
    booking_code: str
    booking_type: str
    units: int
    new_checkout: datetime
    added_amount: float
    room_amount: float
    vat_amount: float
    total_amount: float
    paid_amount: float
    remaining_amount: float
    message: str


# ---------------------------------------------------------------------------
# F10 – Change room on incident
# ---------------------------------------------------------------------------

class ChangeRoomRequest(BaseModel):
    """Request body for POST /bookings/{id}/change-room (F10, FR-18, BR-35, BR-36)."""
    model_config = ConfigDict(populate_by_name=True)

    new_room_id: int = Field(..., alias="newRoomId", description="ID of the new room to move the guest into")
    reason: str = Field(..., min_length=3, max_length=500, alias="reason",
                        description="Mandatory incident reason recorded in audit log")


class ChangeRoomResponse(BaseModel):
    """Response for a successful room change on incident."""
    model_config = ConfigDict(populate_by_name=True)

    booking_id: int
    booking_code: str
    old_room_id: int = Field(..., alias="oldRoomId")
    new_room_id: int = Field(..., alias="newRoomId")
    new_room_number: str = Field(..., alias="newRoomNumber")
    new_room_floor: int = Field(..., alias="newRoomFloor")
    total_amount: float = Field(..., alias="totalAmount",
                                description="Booking total amount – unchanged per BR-36")
    suggested_rooms: List[SuggestedRoom] = Field(
        default_factory=list, alias="suggestedRooms",
        description="Rooms still available in same type, for pre-selection in UI"
    )
