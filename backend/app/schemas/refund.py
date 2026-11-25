from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class RefundCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    booking_id: int = Field(..., alias="bookingId")
    amount: float = Field(..., gt=0)
    reason: str = Field(..., min_length=1, max_length=500)

class RefundOverrideRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    booking_id: int = Field(..., alias="bookingId")
    amount: float = Field(..., gt=0)
    reason: str = Field(..., min_length=1, max_length=500)

class RefundApproveRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    approved: bool
    reason: Optional[str] = Field(None, max_length=500)

class RefundItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    refund_id: int = Field(..., alias="refundId")
    transaction_id: int = Field(..., alias="transactionId")
    booking_id: int = Field(..., alias="bookingId")
    booking_code: str = Field(..., alias="bookingCode")
    customer_name: Optional[str] = Field(None, alias="customerName")
    customer_phone: Optional[str] = Field(None, alias="customerPhone")
    method: str = Field(..., alias="method")
    channel: str = Field(..., alias="channel")
    amount: float = Field(..., alias="amount")
    reason: Optional[str] = Field(None, alias="reason")
    status: str = Field(..., alias="status")
    requester_name: Optional[str] = Field(None, alias="requesterName")
    approver_name: Optional[str] = Field(None, alias="approverName")
    created_at: datetime = Field(..., alias="createdAt")

class RefundListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    items: List[RefundItem]
    total: int
    page: int
    page_size: int = Field(..., alias="pageSize")

class RefundActionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    message: str
    refund_id: int = Field(..., alias="refundId")
    status: str
