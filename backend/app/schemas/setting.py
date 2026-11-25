from datetime import date
from typing import Optional, List, Union, Any
from pydantic import BaseModel, Field, ConfigDict

class SettingHistoryItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    hieu_luc_tu: str = Field(..., alias="hieuLucTu")
    hieu_luc_den: Optional[str] = Field(None, alias="hieuLucDen")
    gia_tri: Union[float, str] = Field(..., alias="giaTri")
    is_active: bool = Field(..., alias="isActive")
    ngay_tao: Optional[str] = Field(None, alias="ngayTao")

class SettingItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ma: str = Field(..., alias="ma")
    ten: str = Field(..., alias="ten")
    mo_ta: str = Field(..., alias="moTa")
    kieu: str = Field(..., alias="kieu")
    don_vi: str = Field(..., alias="donVi")
    min_val: Optional[float] = Field(None, alias="minVal")
    max_val: Optional[float] = Field(None, alias="maxVal")
    canh_bao: Optional[str] = Field(None, alias="canhBao")
    gia_tri_hien_hanh: Union[float, str] = Field(..., alias="giaTriHienHanh")
    hieu_luc_tu: str = Field(..., alias="hieuLucTu")
    hieu_luc_den: Optional[str] = Field(None, alias="hieuLucDen")
    history: List[SettingHistoryItem] = Field(default_factory=list, alias="history")

class SettingUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    gia_tri: Union[float, str] = Field(..., alias="giaTri", description="Giá trị tham số mới")
    hieu_luc_tu: date = Field(..., alias="hieuLucTu", description="Ngày bắt đầu hiệu lực (YYYY-MM-DD)")
    ly_do: str = Field(..., alias="lyDo", description="Lý do điều chỉnh tham số (lưu vào nhật ký kiểm toán)")

class SettingUpdateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    message: str
    canh_bao: Optional[str] = Field(None, alias="canhBao")
