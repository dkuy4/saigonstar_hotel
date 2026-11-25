from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class JobStatusResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    description: str
    interval_seconds: int = Field(..., alias="intervalSeconds")
    enabled: bool
    last_run: Optional[str] = Field(None, alias="lastRun")
    next_run: Optional[str] = Field(None, alias="nextRun")
    last_status: str = Field(..., alias="lastStatus")
    last_duration_ms: float = Field(..., alias="lastDurationMs")
    last_result: Optional[str] = Field(None, alias="lastResult")
    last_error: Optional[str] = Field(None, alias="lastError")
    total_runs: int = Field(..., alias="totalRuns")
    total_success: int = Field(..., alias="totalSuccess")
    total_errors: int = Field(..., alias="totalErrors")

class JobRunResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    job_id: str = Field(..., alias="jobId")
    status: str
    duration_ms: float = Field(..., alias="durationMs")
    result: Optional[str] = None
    error: Optional[str] = None
    last_run: Optional[str] = Field(None, alias="lastRun")
    next_run: Optional[str] = Field(None, alias="nextRun")

class RoomDiscrepancyItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    room_id: int = Field(..., alias="roomId")
    room_number: str = Field(..., alias="roomNumber")
    current_status: str = Field(..., alias="currentStatus")
    discrepancy_type: str = Field(..., alias="discrepancyType")
    description: str

class ManualExchangeRateItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    currency: str
    rate_vnd: float = Field(..., alias="rateVnd", gt=0)

class ManualExchangeRatesRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    rates: List[ManualExchangeRateItem]
