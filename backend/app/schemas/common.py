from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field

T = TypeVar("T")

class BaseResponse(BaseModel):
    success: bool

class SuccessResponse(BaseResponse, Generic[T]):
    success: bool = True
    data: Optional[T] = None

class ErrorResponse(BaseResponse):
    success: bool = False
    code: str
    detail: Optional[str] = ""
    data: Optional[Any] = None

class PaginatedData(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int = Field(alias="pageSize")
    total: int

    model_config = {"populate_by_name": True}

class PaginatedResponse(BaseResponse, Generic[T]):
    success: bool = True
    data: PaginatedData[T]

class HealthResponse(BaseModel):
    status: str  # "healthy" or "unhealthy"
    database: str  # "connected" or "disconnected"
    timestamp: str
