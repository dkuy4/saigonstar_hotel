"""
Pydantic Schemas cho Quản lý Bản dịch chính sách và Mẫu email (F16.5).
"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, ConfigDict

class TranslationItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ma_noi_dung: str = Field(..., alias="maNoiDung")
    ngon_ngu: str = Field(..., alias="ngonNgu")
    noi_dung: str = Field(..., alias="noiDung")
    ngay_tao: Optional[str] = Field(None, alias="ngayTao")

class TranslationMatrixItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    ma_noi_dung: str = Field(..., alias="maNoiDung")
    loai: str = Field(..., alias="loai")  # CHINH_SACH | EMAIL
    tieu_de: str = Field(..., alias="tieuDe")
    mo_ta: str = Field(..., alias="moTa")
    bien_bat_buoc: List[str] = Field(default_factory=list, alias="bienBatBuoc")
    ban_dich: Dict[str, Optional[str]] = Field(default_factory=dict, alias="banDich")
    chua_ra: Dict[str, bool] = Field(default_factory=dict, alias="chuaRa")

class TranslationUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    noi_dung: str = Field(..., alias="noiDung")

class TranslationUpdateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool = True
    ma_noi_dung: str = Field(..., alias="maNoiDung")
    ngon_ngu: str = Field(..., alias="ngonNgu")
    noi_dung: str = Field(..., alias="noiDung")
    canh_bao: Optional[str] = Field(None, alias="canhBao")
