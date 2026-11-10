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
