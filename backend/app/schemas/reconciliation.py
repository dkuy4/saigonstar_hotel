from typing import List
from pydantic import BaseModel, Field, ConfigDict

class DailyReconciliationItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    payment_method: str = Field(..., alias="paymentMethod")
    channel: str = Field(..., alias="channel")
    total_collected: float = Field(..., alias="totalCollected")
    total_refunded: float = Field(..., alias="totalRefunded")
    net_revenue: float = Field(..., alias="netRevenue")

class DailyReconciliationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    date: str
    items: List[DailyReconciliationItem]
    grand_total_collected: float = Field(..., alias="grandTotalCollected")
    grand_total_refunded: float = Field(..., alias="grandTotalRefunded")
    grand_net_revenue: float = Field(..., alias="grandNetRevenue")
