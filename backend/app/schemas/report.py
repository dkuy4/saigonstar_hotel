from typing import Optional
from pydantic import BaseModel


class RevenueItem(BaseModel):
    ky: str
    thu: float
    hoan: float
    thucThu: float


class RevenueReportResponse(BaseModel):
    success: bool = True
    tuNgay: str
    denNgay: str
    donVi: str
    tongThu: float
    tongHoan: float
    tongThucThu: float
    data: list[RevenueItem]


class OccupancyItem(BaseModel):
    maHang: str
    soPhong: int
    gioPhongKhaDung: float
    gioPhongBan: float
    congSuatPhanTram: float


class OccupancyReportResponse(BaseModel):
    success: bool = True
    tuNgay: str
    denNgay: str
    tongGioKhaDung: float
    tongGioBan: float
    congSuatTrungBinh: float
    data: list[OccupancyItem]


class CancellationReportResponse(BaseModel):
    success: bool = True
    tuNgay: str
    denNgay: str
    tongDon: int
    huy: int
    noShow: int
    hetHanGiuCho: int
    tyLeHuy: float
    tyLeNoShow: float
    tyLeHetHan: float


class KpiItem(BaseModel):
    maHang: str
    doanhThuPhong: float
    phongDemBan: float
    phongDemKhaDung: float
    adr: Optional[float] = None
    revpar: float


class KpiReportResponse(BaseModel):
    success: bool = True
    tuNgay: str
    denNgay: str
    tongDoanhThuPhong: float
    tongPhongDemBan: float
    tongPhongDemKhaDung: float
    adrChung: Optional[float] = None
    revparChung: float
    data: list[KpiItem]
