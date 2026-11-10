from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class OnlinePaymentInitRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    booking_code: str = Field(..., alias="bookingCode")
    email: str
    return_url: Optional[str] = Field(None, alias="returnUrl")

class OnlinePaymentInitResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    payment_url: str = Field(..., alias="paymentUrl")
    reference_code: str = Field(..., alias="referenceCode")
    amount: float
    expires_at: Optional[datetime] = Field(None, alias="expiresAt")
    booking_code: str = Field(..., alias="bookingCode")

class PaymentCallbackRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reference_code: str = Field(..., alias="referenceCode")
    is_success: bool = Field(..., alias="isSuccess")
    signature: str

class PaymentCallbackResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    status: str = "success"
    result: str # XAC_NHAN | XAC_NHAN_MUON | HOAN_TIEN | THAT_BAI | DA_XU_LY
    reference_code: str = Field(..., alias="referenceCode")
    message: str
