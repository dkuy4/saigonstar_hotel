"""
F11: Check-out và hóa đơn nội bộ
Schemas cho checkout, invoice, adjust
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# Check-out preview (tính tạm không ghi – màn hình tổng kết)
# ---------------------------------------------------------------------------

class CheckOutPreviewRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    surcharge_amount: float = Field(0.0, ge=0, alias="phuThuTien",
                                    description="Phụ thu (tiền minibar, dịch vụ...)")
    discount_amount: float = Field(0.0, ge=0, alias="giamGia",
                                   description="Giảm giá (chỉ quản lý)")


class CheckOutPreviewResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    booking_id: int
    booking_code: str
    room_amount: float = Field(..., alias="tienPhong")
    overtime_amount: float = Field(..., alias="tienQuaGio",
                                    description="Tiền ở quá giờ trả phòng (BR-39)")
    surcharge_amount: float = Field(..., alias="phuThu")
    discount_amount: float = Field(..., alias="giamGia")
    vat_amount: float = Field(..., alias="tienVat")
    total_invoice: float = Field(..., alias="tongHoaDon")
    paid_amount: float = Field(..., alias="daThanhToan")
    remaining_amount: float = Field(..., alias="conPhaiThu")


# ---------------------------------------------------------------------------
# Check-out request / response
# ---------------------------------------------------------------------------

class CheckOutRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    surcharge_amount: float = Field(0.0, ge=0, alias="phuThuTien")
    surcharge_description: Optional[str] = Field(None, max_length=500, alias="phuThuMoTa",
                                                  description="Mô tả phụ thu (bắt buộc nếu phuThuTien > 0, BR-38)")
    discount_amount: float = Field(0.0, ge=0, alias="giamGia",
                                   description="Giảm giá – chỉ quản lý mới có thể dùng (BR-26)")
    discount_reason: Optional[str] = Field(None, max_length=500, alias="giamGiaLyDo",
                                           description="Lý do giảm giá (bắt buộc nếu giamGia > 0)")


class InvoiceLineItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    line_type: str = Field(..., alias="loaiDong")
    description: str = Field(..., alias="moTa")
    amount: float = Field(..., alias="soTien")
    vat_rate: Optional[float] = Field(None, alias="thueSuat")


class InvoiceDetail(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    invoice_id: int = Field(..., alias="hoaDonId")
    invoice_number: int = Field(..., alias="soHoaDon")
    booking_id: int = Field(..., alias="datPhongId")
    booking_code: str = Field(..., alias="maTraCuu")
    total_amount: float = Field(..., alias="tongTien")
    issued_at: datetime = Field(..., alias="ngayLap")
    created_by: Optional[str] = Field(None, alias="nguoiLap")
    is_adjustment: bool = Field(False, alias="laDieuChinh")
    original_invoice_id: Optional[int] = Field(None, alias="hoaDonGocId")
    lines: List[InvoiceLineItem] = Field(default_factory=list, alias="chiTiet")

    # Guest & booking summary (for printing)
    customer_name: Optional[str] = Field(None, alias="hoTen")
    customer_phone: Optional[str] = Field(None, alias="sdt")
    room_number: Optional[str] = Field(None, alias="maPhong")
    room_type: Optional[str] = Field(None, alias="maHang")
    checkin: Optional[datetime] = None
    checkout: Optional[datetime] = None
    actual_checkin: Optional[datetime] = Field(None, alias="nhanThucTe")
    actual_checkout: Optional[datetime] = Field(None, alias="traThucTe")


class CheckOutResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    booking_id: int
    booking_code: str
    new_status: str = Field(..., alias="newStatus")
    invoice_id: int = Field(..., alias="invoiceId")
    invoice_number: int = Field(..., alias="invoiceNumber")
    total_invoice: float = Field(..., alias="totalInvoice")
    remaining_amount: float = Field(..., alias="remainingAmount")
    message: str


# ---------------------------------------------------------------------------
# Adjust invoice (hóa đơn điều chỉnh)
# ---------------------------------------------------------------------------

class InvoiceAdjustRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    amount: float = Field(..., alias="soTien",
                          description="Dương: phụ thu thêm; Âm: giảm trừ. Khác 0.")
    description: str = Field(..., min_length=3, max_length=500, alias="moTa",
                              description="Mô tả lý do điều chỉnh (bắt buộc, BR-45)")


class InvoiceAdjustResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    original_invoice_id: int = Field(..., alias="hoaDonGocId")
    adjustment_invoice_id: int = Field(..., alias="hoaDonDieuChinhId")
    adjustment_invoice_number: int = Field(..., alias="soHoaDonDieuChinh")
    amount: float = Field(..., alias="soTien")
    description: str = Field(..., alias="moTa")
    message: str
