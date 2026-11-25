import io
import logging
from datetime import date, datetime
from typing import Optional
import oracledb
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from app.schemas.report import (
    RevenueItem,
    RevenueReportResponse,
    OccupancyItem,
    OccupancyReportResponse,
    CancellationReportResponse,
    KpiItem,
    KpiReportResponse,
)

logger = logging.getLogger(__name__)


def get_revenue_report(
    conn: oracledb.Connection,
    tu_ngay: date,
    den_ngay: date,
    don_vi: str = "NGAY",
    ma_hang: Optional[str] = None,
    phuong_thuc: Optional[str] = None,
) -> RevenueReportResponse:
    """Queries pkg_bao_cao.doanh_thu (FR-40)."""
    unit_param = don_vi.upper().strip() if don_vi else "NGAY"
    hang_param = ma_hang.upper().strip() if (ma_hang and ma_hang.strip()) else None
    pt_param = phuong_thuc.upper().strip() if (phuong_thuc and phuong_thuc.strip()) else None

    with conn.cursor() as cur:
        rc = cur.callfunc(
            "pkg_bao_cao.doanh_thu",
            oracledb.DB_TYPE_CURSOR,
            [tu_ngay, den_ngay, unit_param, hang_param, pt_param]
        )
        rows = rc.fetchall()

    items: list[RevenueItem] = []
    tot_thu = 0.0
    tot_hoan = 0.0
    tot_thuc_thu = 0.0

    for r in rows:
        ky_val = r[0]
        if isinstance(ky_val, (datetime, date)):
            ky_str = ky_val.strftime("%Y-%m-%d") if unit_param == "NGAY" else ky_val.strftime("%Y-%m")
        else:
            ky_str = str(ky_val)

        thu = float(r[1] or 0)
        hoan = float(r[2] or 0)
        thuc_thu = float(r[3] or 0)

        tot_thu += thu
        tot_hoan += hoan
        tot_thuc_thu += thuc_thu

        items.append(
            RevenueItem(
                ky=ky_str,
                thu=thu,
                hoan=hoan,
                thucThu=thuc_thu
            )
        )

    return RevenueReportResponse(
        success=True,
        tuNgay=tu_ngay.isoformat(),
        denNgay=den_ngay.isoformat(),
        donVi=unit_param,
        tongThu=tot_thu,
        tongHoan=tot_hoan,
        tongThucThu=tot_thuc_thu,
        data=items
    )


def get_occupancy_report(
    conn: oracledb.Connection,
    tu_ngay: date,
    den_ngay: date
) -> OccupancyReportResponse:
    """Queries pkg_bao_cao.cong_suat (FR-41)."""
    with conn.cursor() as cur:
        rc = cur.callfunc(
            "pkg_bao_cao.cong_suat",
            oracledb.DB_TYPE_CURSOR,
            [tu_ngay, den_ngay]
        )
        rows = rc.fetchall()

    items: list[OccupancyItem] = []
    tot_kha_dung = 0.0
    tot_ban = 0.0

    for r in rows:
        ma_hang = str(r[0])
        so_phong = int(r[1] or 0)
        gio_kd = float(r[2] or 0)
        gio_ban = float(r[3] or 0)
        cs_pt = float(r[4] or 0)

        tot_kha_dung += gio_kd
        tot_ban += gio_ban

        items.append(
            OccupancyItem(
                maHang=ma_hang,
                soPhong=so_phong,
                gioPhongKhaDung=gio_kd,
                gioPhongBan=gio_ban,
                congSuatPhanTram=cs_pt
            )
        )

    cong_suat_tb = round((tot_ban / tot_kha_dung) * 100, 2) if tot_kha_dung > 0 else 0.0

    return OccupancyReportResponse(
        success=True,
        tuNgay=tu_ngay.isoformat(),
        denNgay=den_ngay.isoformat(),
        tongGioKhaDung=tot_kha_dung,
        tongGioBan=tot_ban,
        congSuatTrungBinh=cong_suat_tb,
        data=items
    )


def get_cancellation_report(
    conn: oracledb.Connection,
    tu_ngay: date,
    den_ngay: date
) -> CancellationReportResponse:
    """Queries pkg_bao_cao.ty_le_huy (FR-42)."""
    with conn.cursor() as cur:
        rc = cur.callfunc(
            "pkg_bao_cao.ty_le_huy",
            oracledb.DB_TYPE_CURSOR,
            [tu_ngay, den_ngay]
        )
        row = rc.fetchone()

    if not row:
        return CancellationReportResponse(
            success=True,
            tuNgay=tu_ngay.isoformat(),
            denNgay=den_ngay.isoformat(),
            tongDon=0,
            huy=0,
            noShow=0,
            hetHanGiuCho=0,
            tyLeHuy=0.0,
            tyLeNoShow=0.0,
            tyLeHetHan=0.0
        )

    return CancellationReportResponse(
        success=True,
        tuNgay=tu_ngay.isoformat(),
        denNgay=den_ngay.isoformat(),
        tongDon=int(row[0] or 0),
        huy=int(row[1] or 0),
        noShow=int(row[2] or 0),
        hetHanGiuCho=int(row[3] or 0),
        tyLeHuy=float(row[4] or 0),
        tyLeNoShow=float(row[5] or 0),
        tyLeHetHan=float(row[6] or 0)
    )


def get_kpi_report(
    conn: oracledb.Connection,
    tu_ngay: date,
    den_ngay: date
) -> KpiReportResponse:
    """Queries pkg_bao_cao.adr_revpar (FR-44)."""
    with conn.cursor() as cur:
        rc = cur.callfunc(
            "pkg_bao_cao.adr_revpar",
            oracledb.DB_TYPE_CURSOR,
            [tu_ngay, den_ngay]
        )
        rows = rc.fetchall()

    items: list[KpiItem] = []
    tot_dt = 0.0
    tot_dem_ban = 0.0
    tot_dem_kd = 0.0

    for r in rows:
        ma_hang = str(r[0])
        dt = float(r[1] or 0)
        dem_ban = float(r[2] or 0)
        dem_kd = float(r[3] or 0)
        adr = float(r[4]) if r[4] is not None else None
        revpar = float(r[5] or 0)

        tot_dt += dt
        tot_dem_ban += dem_ban
        tot_dem_kd += dem_kd

        items.append(
            KpiItem(
                maHang=ma_hang,
                doanhThuPhong=dt,
                phongDemBan=dem_ban,
                phongDemKhaDung=dem_kd,
                adr=adr,
                revpar=revpar
            )
        )

    adr_chung = round(tot_dt / tot_dem_ban, 0) if tot_dem_ban > 0 else None
    revpar_chung = round(tot_dt / tot_dem_kd, 0) if tot_dem_kd > 0 else 0.0

    return KpiReportResponse(
        success=True,
        tuNgay=tu_ngay.isoformat(),
        denNgay=den_ngay.isoformat(),
        tongDoanhThuPhong=tot_dt,
        tongPhongDemBan=tot_dem_ban,
        tongPhongDemKhaDung=tot_dem_kd,
        adrChung=adr_chung,
        revparChung=revpar_chung,
        data=items
    )


# ---------- Excel Export Helpers (openpyxl) ----------

def _apply_excel_styling(ws, header_row_idx: int, title: str, subtitle: str):
    """Applies clean enterprise styling to openpyxl worksheet."""
    # Title
    ws["A1"] = title
    ws["A1"].font = Font(name="Arial", size=15, bold=True, color="0F172A")
    ws["A2"] = subtitle
    ws["A2"].font = Font(name="Arial", size=10, italic=True, color="64748B")

    # Header row formatting
    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="0284C7", end_color="0284C7", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1")
    )

    for cell in ws[header_row_idx]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            max_len = max(max_len, len(val_str))
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)


def export_revenue_excel(report: RevenueReportResponse) -> io.BytesIO:
    """Exports revenue report to formatted Excel workbook."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Báo cáo doanh thu"

    _apply_excel_styling(
        ws,
        header_row_idx=4,
        title="KHÁCH SẠN SÀI GÒN STAR - BÁO CÁO DOANH THU",
        subtitle=f"Thời gian: {report.tuNgay} đến {report.denNgay} | Đơn vị tính: {report.donVi} (FR-40, FR-43)"
    )

    headers = ["Kỳ", "Tiền thu (VND)", "Tiền hoàn (VND)", "Thực thu (VND)"]
    for col_idx, h in enumerate(headers, 1):
        ws.cell(row=4, column=col_idx, value=h)

    thin_border = Border(
        left=Side(style="thin", color="E2E8F0"),
        right=Side(style="thin", color="E2E8F0"),
        top=Side(style="thin", color="E2E8F0"),
        bottom=Side(style="thin", color="E2E8F0")
    )

    curr_row = 5
    for item in report.data:
        c1 = ws.cell(row=curr_row, column=1, value=item.ky)
        c2 = ws.cell(row=curr_row, column=2, value=item.thu)
        c3 = ws.cell(row=curr_row, column=3, value=item.hoan)
        c4 = ws.cell(row=curr_row, column=4, value=item.thucThu)

        c1.alignment = Alignment(horizontal="center")
        c2.number_format = "#,##0"
        c3.number_format = "#,##0"
        c4.number_format = "#,##0"

        for c in (c1, c2, c3, c4):
            c.border = thin_border
            c.font = Font(name="Arial", size=10)
        curr_row += 1

    # Total row
    tot_label = ws.cell(row=curr_row, column=1, value="TỔNG CỘNG")
    tot_thu = ws.cell(row=curr_row, column=2, value=report.tongThu)
    tot_hoan = ws.cell(row=curr_row, column=3, value=report.tongHoan)
    tot_thuc = ws.cell(row=curr_row, column=4, value=report.tongThucThu)

    tot_font = Font(name="Arial", size=11, bold=True, color="0F172A")
    tot_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

    for c in (tot_label, tot_thu, tot_hoan, tot_thuc):
        c.font = tot_font
        c.fill = tot_fill
        c.border = thin_border
        if c != tot_label:
            c.number_format = "#,##0"
        else:
            c.alignment = Alignment(horizontal="center")

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def export_occupancy_excel(report: OccupancyReportResponse) -> io.BytesIO:
    """Exports occupancy report to formatted Excel workbook."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Báo cáo công suất"

    _apply_excel_styling(
        ws,
        header_row_idx=4,
        title="KHÁCH SẠN SÀI GÒN STAR - BÁO CÁO CÔNG SUẤT PHÒNG",
        subtitle=f"Thời gian: {report.tuNgay} đến {report.denNgay} | Công suất trung bình: {report.congSuatTrungBinh}% (FR-41)"
    )

    headers = ["Hạng phòng", "Số phòng", "Giờ khả dụng", "Giờ bán", "Công suất (%)"]
    for col_idx, h in enumerate(headers, 1):
        ws.cell(row=4, column=col_idx, value=h)

    thin_border = Border(
        left=Side(style="thin", color="E2E8F0"),
        right=Side(style="thin", color="E2E8F0"),
        top=Side(style="thin", color="E2E8F0"),
        bottom=Side(style="thin", color="E2E8F0")
    )

    curr_row = 5
    for item in report.data:
        c1 = ws.cell(row=curr_row, column=1, value=item.maHang)
        c2 = ws.cell(row=curr_row, column=2, value=item.soPhong)
        c3 = ws.cell(row=curr_row, column=3, value=item.gioPhongKhaDung)
        c4 = ws.cell(row=curr_row, column=4, value=item.gioPhongBan)
        c5 = ws.cell(row=curr_row, column=5, value=item.congSuatPhanTram / 100.0)

        c1.alignment = Alignment(horizontal="center")
        c2.number_format = "#,##0"
        c3.number_format = "#,##0.0"
        c4.number_format = "#,##0.0"
        c5.number_format = "0.00%"

        for c in (c1, c2, c3, c4, c5):
            c.border = thin_border
            c.font = Font(name="Arial", size=10)
        curr_row += 1

    # Total row
    tot_label = ws.cell(row=curr_row, column=1, value="TRUNG BÌNH TOÀN KHÁCH SẠN")
    tot_sp = ws.cell(row=curr_row, column=2, value=sum(i.soPhong for i in report.data))
    tot_kd = ws.cell(row=curr_row, column=3, value=report.tongGioKhaDung)
    tot_b = ws.cell(row=curr_row, column=4, value=report.tongGioBan)
    tot_cs = ws.cell(row=curr_row, column=5, value=report.congSuatTrungBinh / 100.0)

    tot_font = Font(name="Arial", size=11, bold=True, color="0F172A")
    tot_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

    for c in (tot_label, tot_sp, tot_kd, tot_b, tot_cs):
        c.font = tot_font
        c.fill = tot_fill
        c.border = thin_border
        if c == tot_cs:
            c.number_format = "0.00%"
        elif c in (tot_kd, tot_b):
            c.number_format = "#,##0.0"
        elif c == tot_sp:
            c.number_format = "#,##0"
        else:
            c.alignment = Alignment(horizontal="center")

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def export_cancellation_excel(report: CancellationReportResponse) -> io.BytesIO:
    """Exports cancellations report to formatted Excel workbook."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Tỷ lệ hủy & No-show"

    _apply_excel_styling(
        ws,
        header_row_idx=4,
        title="KHÁCH SẠN SÀI GÒN STAR - BÁO CÁO TỶ LỆ HỦY VÀ NO-SHOW",
        subtitle=f"Thời gian: {report.tuNgay} đến {report.denNgay} (FR-42)"
    )

    headers = ["Chỉ số", "Số lượng đơn", "Tỷ lệ (%)"]
    for col_idx, h in enumerate(headers, 1):
        ws.cell(row=4, column=col_idx, value=h)

    thin_border = Border(
        left=Side(style="thin", color="E2E8F0"),
        right=Side(style="thin", color="E2E8F0"),
        top=Side(style="thin", color="E2E8F0"),
        bottom=Side(style="thin", color="E2E8F0")
    )

    metrics = [
        ("Tổng số đơn tạo trong kỳ", report.tongDon, 1.0),
        ("Đơn bị hủy (CANCELLED)", report.huy, report.tyLeHuy / 100.0),
        ("Khách không đến (NO_SHOW)", report.noShow, report.tyLeNoShow / 100.0),
        ("Hết hạn giữ chỗ (EXPIRED)", report.hetHanGiuCho, report.tyLeHetHan / 100.0),
    ]

    for idx, (label, count, rate) in enumerate(metrics, 5):
        c1 = ws.cell(row=idx, column=1, value=label)
        c2 = ws.cell(row=idx, column=2, value=count)
        c3 = ws.cell(row=idx, column=3, value=rate)

        c2.number_format = "#,##0"
        c3.number_format = "0.00%"

        for c in (c1, c2, c3):
            c.border = thin_border
            c.font = Font(name="Arial", size=10)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def export_kpi_excel(report: KpiReportResponse) -> io.BytesIO:
    """Exports ADR and RevPAR report to formatted Excel workbook."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Báo cáo ADR & RevPAR"

    _apply_excel_styling(
        ws,
        header_row_idx=4,
        title="KHÁCH SẠN SÀI GÒN STAR - BÁO CÁO ADR VÀ REVPAR",
        subtitle=f"Thời gian: {report.tuNgay} đến {report.denNgay} | ADR chung: {report.adrChung:,.0f} VND | RevPAR chung: {report.revparChung:,.0f} VND (FR-44)" if report.adrChung else f"Thời gian: {report.tuNgay} đến {report.denNgay}"
    )

    headers = ["Hạng phòng", "Doanh thu phòng (VND)", "Phòng-đêm đã bán", "Phòng-đêm khả dụng", "ADR (VND)", "RevPAR (VND)"]
    for col_idx, h in enumerate(headers, 1):
        ws.cell(row=4, column=col_idx, value=h)

    thin_border = Border(
        left=Side(style="thin", color="E2E8F0"),
        right=Side(style="thin", color="E2E8F0"),
        top=Side(style="thin", color="E2E8F0"),
        bottom=Side(style="thin", color="E2E8F0")
    )

    curr_row = 5
    for item in report.data:
        c1 = ws.cell(row=curr_row, column=1, value=item.maHang)
        c2 = ws.cell(row=curr_row, column=2, value=item.doanhThuPhong)
        c3 = ws.cell(row=curr_row, column=3, value=item.phongDemBan)
        c4 = ws.cell(row=curr_row, column=4, value=item.phongDemKhaDung)
        c5 = ws.cell(row=curr_row, column=5, value=item.adr or 0)
        c6 = ws.cell(row=curr_row, column=6, value=item.revpar)

        c1.alignment = Alignment(horizontal="center")
        c2.number_format = "#,##0"
        c3.number_format = "#,##0.00"
        c4.number_format = "#,##0.00"
        c5.number_format = "#,##0"
        c6.number_format = "#,##0"

        for c in (c1, c2, c3, c4, c5, c6):
            c.border = thin_border
            c.font = Font(name="Arial", size=10)
        curr_row += 1

    # Total row
    tot_label = ws.cell(row=curr_row, column=1, value="TOÀN KHÁCH SẠN")
    tot_dt = ws.cell(row=curr_row, column=2, value=report.tongDoanhThuPhong)
    tot_b = ws.cell(row=curr_row, column=3, value=report.tongPhongDemBan)
    tot_kd = ws.cell(row=curr_row, column=4, value=report.tongPhongDemKhaDung)
    tot_adr = ws.cell(row=curr_row, column=5, value=report.adrChung or 0)
    tot_rev = ws.cell(row=curr_row, column=6, value=report.revparChung)

    tot_font = Font(name="Arial", size=11, bold=True, color="0F172A")
    tot_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

    for c in (tot_label, tot_dt, tot_b, tot_kd, tot_adr, tot_rev):
        c.font = tot_font
        c.fill = tot_fill
        c.border = thin_border
        if c in (tot_dt, tot_adr, tot_rev):
            c.number_format = "#,##0"
        elif c in (tot_b, tot_kd):
            c.number_format = "#,##0.00"
        else:
            c.alignment = Alignment(horizontal="center")

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output
