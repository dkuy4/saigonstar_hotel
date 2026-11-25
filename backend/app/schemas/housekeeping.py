from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class HousekeepingTaskItem(BaseModel):
    """
    Thông tin buồng phòng theo quy định bảo mật FR-25, AC-16:
    TUYỆT ĐỐI KHÔNG chứa thông tin khách hàng (họ tên, sđt, email)
    và TUYỆT ĐỐI KHÔNG chứa thông tin giá tiền.
    """
    model_config = ConfigDict(populate_by_name=True)

    room_id: int = Field(..., alias="roomId")
    room_number: str = Field(..., alias="roomNumber")
    floor: int = Field(..., alias="floor")
    room_type_id: int = Field(..., alias="roomTypeId")
    room_type: str = Field(..., alias="roomType")
    room_type_name: str = Field(..., alias="roomTypeName")
    status: str = Field(..., alias="status")
    notes: Optional[str] = Field(None, alias="notes")
    last_action_at: Optional[datetime] = Field(None, alias="lastActionAt")

class HousekeepingTaskListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: List[HousekeepingTaskItem]
    total: int

class HousekeepingActionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    message: str
    room_id: int = Field(..., alias="roomId")
    status: str
