import logging
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, status
import oracledb

from app.db import get_conn
from app.errors import BusinessException
from app.security import require_role, AuthUser
from app.schemas.report import (
    RevenueReportResponse,
    OccupancyReportResponse,
    CancellationReportResponse,
    KpiReportResponse,
)
from app.repositories import report_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Reports & KPIs (F18)"])


def _parse_dates(
    from_date_str: Optional[str],
    to_date_str: Optional[str]
) -> tuple[date, date]:
    """Helper to parse and validate date range."""
    today = date.today()
    if not from_date_str:
        # Default to first day of current month
        d_from = date(today.year, today.month, 1)
    else:
        try:
            d_from = date.fromisoformat(from_date_str.strip())
        except ValueError:
            raise BusinessException(code="VALIDATION_ERROR", detail="Định dạng ngày bắt đầu không hợp lệ (YYYY-MM-DD)")

    if not to_date_str:
        # Default to today
        d_to = today
    else:
        try:
            d_to = date.fromisoformat(to_date_str.strip())
        except ValueError:
            raise BusinessException(code="VALIDATION_ERROR", detail="Định dạng ngày kết thúc không hợp lệ (YYYY-MM-DD)")

    if d_from > d_to:
        raise BusinessException(code="VALIDATION_ERROR", detail="Ngày bắt đầu không được lớn hơn ngày kết thúc")

    return d_from, d_to


@router.get("/revenue", response_model=RevenueReportResponse)
def get_revenue_report(
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    from_date_alt: Optional[str] = Query(None, alias="from_date"),
    to_date_alt: Optional[str] = Query(None, alias="to_date"),
    tuNgay: Optional[str] = Query(None),
    denNgay: Optional[str] = Query(None),
    unit: str = Query("NGAY", alias="unit"),
    donVi: Optional[str] = Query(None),
    maHang: Optional[str] = Query(None),
    phuongThuc: Optional[str] = Query(None),
    format: str = Query("json"),
    conn: oracledb.Connection = Depends(get_conn),
    current_user: AuthUser = Depends(require_role("QUAN_LY")),
):
    """
    GET /api/v1/reports/revenue (FR-40, FR-43)
    Reports daily/monthly actual revenue: total income minus refunds.
    Supports format=xlsx for Excel download.
    Requires QUAN_LY role.
    """
    d_from, d_to = _parse_dates(from_date or from_date_alt or tuNgay, to_date or to_date_alt or denNgay)
    resolved_unit = donVi or unit or "NGAY"

    report = report_repo.get_revenue_report(
        conn=conn,
        tu_ngay=d_from,
        den_ngay=d_to,
        don_vi=resolved_unit,
        ma_hang=maHang,
        phuong_thuc=phuongThuc,
    )

    if format.lower() == "xlsx":
        excel_stream = report_repo.export_revenue_excel(report)
        filename = f"bao_cao_doanh_thu_{d_from}_{d_to}.xlsx"
        return Response(
            content=excel_stream.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    return report


@router.get("/occupancy", response_model=OccupancyReportResponse)
def get_occupancy_report(
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    from_date_alt: Optional[str] = Query(None, alias="from_date"),
    to_date_alt: Optional[str] = Query(None, alias="to_date"),
    tuNgay: Optional[str] = Query(None),
    denNgay: Optional[str] = Query(None),
    format: str = Query("json"),
    conn: oracledb.Connection = Depends(get_conn),
    current_user: AuthUser = Depends(require_role("QUAN_LY")),
):
    """
    GET /api/v1/reports/occupancy (FR-41)
    Reports room occupancy rate by room type based on room-hours excluding maintenance.
    Supports format=xlsx for Excel download.
    Requires QUAN_LY role.
    """
    d_from, d_to = _parse_dates(from_date or from_date_alt or tuNgay, to_date or to_date_alt or denNgay)

    report = report_repo.get_occupancy_report(
        conn=conn,
        tu_ngay=d_from,
        den_ngay=d_to,
    )

    if format.lower() == "xlsx":
        excel_stream = report_repo.export_occupancy_excel(report)
        filename = f"bao_cao_cong_suat_{d_from}_{d_to}.xlsx"
        return Response(
            content=excel_stream.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    return report


@router.get("/cancellations", response_model=CancellationReportResponse)
def get_cancellation_report(
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    from_date_alt: Optional[str] = Query(None, alias="from_date"),
    to_date_alt: Optional[str] = Query(None, alias="to_date"),
    tuNgay: Optional[str] = Query(None),
    denNgay: Optional[str] = Query(None),
    format: str = Query("json"),
    conn: oracledb.Connection = Depends(get_conn),
    current_user: AuthUser = Depends(require_role("QUAN_LY")),
):
    """
    GET /api/v1/reports/cancellations (FR-42)
    Reports cancellation, no-show and expired hold rates on bookings created during the period.
    Supports format=xlsx for Excel download.
    Requires QUAN_LY role.
    """
    d_from, d_to = _parse_dates(from_date or from_date_alt or tuNgay, to_date or to_date_alt or denNgay)

    report = report_repo.get_cancellation_report(
        conn=conn,
        tu_ngay=d_from,
        den_ngay=d_to,
    )

    if format.lower() == "xlsx":
        excel_stream = report_repo.export_cancellation_excel(report)
        filename = f"bao_cao_ty_le_huy_{d_from}_{d_to}.xlsx"
        return Response(
            content=excel_stream.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    return report


@router.get("/kpi", response_model=KpiReportResponse)
def get_kpi_report(
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    from_date_alt: Optional[str] = Query(None, alias="from_date"),
    to_date_alt: Optional[str] = Query(None, alias="to_date"),
    tuNgay: Optional[str] = Query(None),
    denNgay: Optional[str] = Query(None),
    format: str = Query("json"),
    conn: oracledb.Connection = Depends(get_conn),
    current_user: AuthUser = Depends(require_role("QUAN_LY")),
):
    """
    GET /api/v1/reports/kpi (FR-44)
    Reports ADR (Average Daily Rate) and RevPAR (Revenue Per Available Room) per room type.
    Supports format=xlsx for Excel download.
    Requires QUAN_LY role.
    """
    d_from, d_to = _parse_dates(from_date or from_date_alt or tuNgay, to_date or to_date_alt or denNgay)

    report = report_repo.get_kpi_report(
        conn=conn,
        tu_ngay=d_from,
        den_ngay=d_to,
    )

    if format.lower() == "xlsx":
        excel_stream = report_repo.export_kpi_excel(report)
        filename = f"bao_cao_adr_revpar_{d_from}_{d_to}.xlsx"
        return Response(
            content=excel_stream.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    return report
