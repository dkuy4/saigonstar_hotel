from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class PriceItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    bang_gia_id: int = Field(..., alias="bangGiaId")
    loai_phong_id: int = Field(..., alias="loaiPhongId")
    ma_hang: str = Field(..., alias="maHang")
    ten_hang: str = Field(..., alias="tenHang")
    loai_gia: str = Field(..., alias="loaiGia")
    don_gia: float = Field(..., alias="donGia")
    thue_suat: float = Field(..., alias="thueSuat")
    don_gia_vat: float = Field(..., alias="donGiaVat")
    hieu_luc_tu: str = Field(..., alias="hieuLucTu")
    hieu_luc_den: Optional[str] = Field(None, alias="hieuLucDen")
    is_active: bool = Field(..., alias="isActive")
    ngay_tao: Optional[str] = Field(None, alias="ngayTao")

class PriceChangeRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ma_hang: str = Field(..., alias="maHang", description="Mã hạng phòng (STANDARD, SUPERIOR, DELUXE, SUITE)")
    loai_gia: str = Field(..., alias="loaiGia", description="Loại giá: NGAY hoặc GIO")
    don_gia: float = Field(..., alias="donGia", description="Đơn giá mới (VND, bội của 1.000)")
    hieu_luc_tu: date = Field(..., alias="hieuLucTu", description="Ngày bắt đầu hiệu lực (YYYY-MM-DD)")
    ly_do: str = Field(..., alias="lyDo", description="Lý do điều chỉnh giá (ghi nhật ký)")

class PriceRuleValidationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ma_hang: str = Field(..., alias="maHang")
    loai_gia: str = Field(..., alias="loaiGia")
    don_gia: float = Field(..., alias="donGia")
    hieu_luc_tu: date = Field(..., alias="hieuLucTu")

class PriceRuleValidationResponse(BaseModel):
    valid: bool
    is_hourly_allowed: bool
    gia_gio: Optional[float] = None
    gia_gio_x5: Optional[float] = None
    gia_ngay: Optional[float] = None
    message: Optional[str] = None
