from datetime import datetime, date
from typing import Optional, Literal, Dict
from pydantic import BaseModel, Field

class RoomTypeOut(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    amenities: Optional[str] = None
    capacity: Optional[int] = None
    hourly_allowed: bool
    image_url: Optional[str] = None
    daily_price: Optional[float] = None
    hourly_price: Optional[float] = None

class ExchangeRateOut(BaseModel):
    currency: str
    rate_vnd: float
    updated_at: date

class AvailabilityItem(BaseModel):
    room_type_id: int
    code: str
    name: str
    description: Optional[str] = None
    amenities: Optional[str] = None
    capacity: Optional[int] = None
    hourly_allowed: bool
    image_url: Optional[str] = None
    available_rooms: int
    unit_price: float
    daily_unit_price: float
    room_amount: float
    vat_rate: float
    vat_amount: float
    total_amount: float
    converted_prices: Dict[str, float] = Field(default_factory=dict)

class AvailabilityResponse(BaseModel):
    type: Literal["NGAY", "GIO"]
    checkin: datetime
    checkout: datetime
    guests: Optional[int] = None
    items: list[AvailabilityItem]

# --- F16.2 Room Type Admin Schemas ---

class RoomTypeTranslationItem(BaseModel):
    lang: str = Field(..., description="Mã ngôn ngữ (vi, en, zh-CN, ko, ja, es, fr)")
    name: str = Field(..., description="Tên hạng phòng")
    description: Optional[str] = None
    amenities: Optional[str] = None

class RoomTypeAdminDetail(BaseModel):
    id: int
    code: str
    capacity: int
    hourly_allowed: bool
    image_url: Optional[str] = None
    translations: Dict[str, RoomTypeTranslationItem]
    daily_price: Optional[float] = None
    hourly_price: Optional[float] = None

class RoomTypeUpdateRequest(BaseModel):
    capacity: int = Field(..., ge=1, le=20, description="Sức chứa tối đa")
    image_url: Optional[str] = None
    translations: list[RoomTypeTranslationItem] = Field(..., description="Danh sách bản dịch 7 ngôn ngữ")
