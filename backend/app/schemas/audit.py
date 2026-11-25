from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class AuditLogItem(BaseModel):
    nhatKyId: int
    bang: str
    khoaDong: str
    hanhDong: str
    thoiDiem: datetime
    nguoiThucHienId: Optional[int] = None
    tenDangNhap: Optional[str] = None
    vaiTro: str
    kenh: str
    diaChiIp: Optional[str] = None
    lyDo: Optional[str] = None
    giaTriCu: Optional[dict[str, Any]] = None
    giaTriMoi: Optional[dict[str, Any]] = None


class AuditLogsResponse(BaseModel):
    success: bool = True
    total: int
    page: int
    pageSize: int
    totalPages: int
    items: list[AuditLogItem]
    tables: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)


class StateAtResponse(BaseModel):
    success: bool = True
    found: bool
    bang: str
    khoaDong: str
    targetTime: datetime
    auditTime: Optional[datetime] = None
    action: Optional[str] = None
    performedBy: Optional[str] = None
    role: Optional[str] = None
    state: Optional[dict[str, Any]] = None
    message: Optional[str] = None
