from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class CurrentBooking(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    booking_code: str = Field(..., alias="bookingCode")
    booking_status: str = Field(..., alias="bookingStatus")
    checkin: datetime = Field(..., alias="from")
    checkout: datetime = Field(..., alias="to")

class NextBooking(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    booking_code: str = Field(..., alias="bookingCode")
    checkin: datetime = Field(..., alias="from")

class RoomTile(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    room_id: int = Field(..., alias="roomId")
    room_number: str = Field(..., alias="roomNumber")
    floor: int
    room_type: str = Field(..., alias="roomType")
    status: str
    is_active: bool = Field(True, alias="isActive")
    current_booking: Optional[CurrentBooking] = Field(None, alias="currentBooking")
    next_booking: Optional[NextBooking] = Field(None, alias="nextBooking")

class FloorGroup(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    floor: int
    rooms: List[RoomTile]

class RoomStats(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total: int
    available: int
    occupied: int
    cleaning: int
    maintenance: int

class RoomBoardResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    at: datetime
    floors: List[FloorGroup]
    stats: RoomStats

# --- Admin Schemas for F16.1 ---

class RoomAdminItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    room_id: int = Field(..., alias="roomId")
    room_number: str = Field(..., alias="roomNumber")
    floor: int
    room_type_id: int = Field(..., alias="roomTypeId")
    room_type: str = Field(..., alias="roomType")
    room_type_name: str = Field(..., alias="roomTypeName")
    status: str
    is_active: bool = Field(..., alias="isActive")
    notes: Optional[str] = Field(None, alias="notes")
    created_at: datetime = Field(..., alias="createdAt")

class RoomAdminListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: List[RoomAdminItem]
    total: int
    page: int
    page_size: int = Field(..., alias="pageSize")

class RoomCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    room_number: str = Field(..., alias="roomNumber", min_length=1, max_length=10)
    floor: int = Field(..., ge=1, le=50)
    room_type_id: int = Field(..., alias="roomTypeId")
    notes: Optional[str] = None

class RoomUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    room_number: Optional[str] = Field(None, alias="roomNumber", min_length=1, max_length=10)
    floor: Optional[int] = Field(None, ge=1, le=50)
    room_type_id: Optional[int] = Field(None, alias="roomTypeId")
    is_active: Optional[bool] = Field(None, alias="isActive")
    notes: Optional[str] = None

class AffectedBooking(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    booking_id: int = Field(..., alias="bookingId")
    booking_code: str = Field(..., alias="bookingCode")
    status: str
    checkin: datetime = Field(..., alias="from")
    checkout: datetime = Field(..., alias="to")
    customer_name: str = Field(..., alias="customerName")
    customer_phone: str = Field(..., alias="customerPhone")
    customer_email: str = Field(..., alias="customerEmail")

class MaintenanceRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reason: str = Field(..., min_length=1, max_length=500, alias="reason")
    ignore_affected_bookings: bool = Field(False, alias="ignoreAffectedBookings")

class MaintenanceResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    message: str
    room_id: int = Field(..., alias="roomId")
    status: str

