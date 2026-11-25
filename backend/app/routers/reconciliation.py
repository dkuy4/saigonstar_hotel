import csv
import io
import logging
from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
import oracledb

from app.db import get_conn
from app.context import set_db_context
from app.security import require_role, AuthUser
from app.schemas.reconciliation import DailyReconciliationResponse
from app.repositories.payment_repo import PaymentRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])

@router.get(
    "/daily",
    response_model=DailyReconciliationResponse,
    summary="Báo cáo đối soát doanh thu theo phương thức trong một ngày (F12, FR-39)"
)
def get_daily_reconciliation(
    target_date: Optional[str] = Query(None, alias="date", description="Ngày đối soát theo định dạng YYYY-MM-DD. Mặc định là hôm nay."),
    user: AuthUser = Depends(require_role("LE_TAN", "QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="QUAY")
    if target_date:
        try:
            d = datetime.strptime(target_date.strip(), "%Y-%m-%d").date()
        except ValueError:
            d = date.today()
    else:
        d = date.today()

    res = PaymentRepository.get_daily_reconciliation(conn=conn, target_date=d)
    return DailyReconciliationResponse(**res)

@router.get(
    "/daily/export",
    summary="Xuất báo cáo đối soát ngày dưới dạng tệp CSV (F12, FR-39)"
)
def export_daily_reconciliation_csv(
    target_date: Optional[str] = Query(None, alias="date", description="Ngày đối soát YYYY-MM-DD"),
    user: AuthUser = Depends(require_role("LE_TAN", "QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="QUAY")
    if target_date:
        try:
            d = datetime.strptime(target_date.strip(), "%Y-%m-%d").date()
        except ValueError:
            d = date.today()
    else:
        d = date.today()

    res = PaymentRepository.get_daily_reconciliation(conn=conn, target_date=d)

    output = io.StringIO()
    writer = csv.writer(output)
    # Ghi BOM UTF-8 để Excel đọc tiếng Việt chuẩn
    output.write('\ufeff')
    writer.writerow(["BÁO CÁO ĐỐI SOÁT DOANH THU THEO PHƯƠNG THỨC"])
    writer.writerow([f"Ngày đối soát: {res['date']}"])
    writer.writerow([])
    writer.writerow(["Phương thức", "Kênh", "Tổng thu (VND)", "Tổng hoàn (VND)", "Thực thu ròng (VND)"])

    for item in res["items"]:
        writer.writerow([
            item["paymentMethod"],
            item["channel"],
            int(item["totalCollected"]),
            int(item["totalRefunded"]),
            int(item["netRevenue"])
        ])

    writer.writerow([])
    writer.writerow([
        "TỔNG CỘNG",
        "",
        int(res["grandTotalCollected"]),
        int(res["grandTotalRefunded"]),
        int(res["grandNetRevenue"])
    ])

    csv_content = output.getvalue()
    filename = f"doi_soat_{res['date']}.csv"

    return Response(
        content=csv_content.encode('utf-8-sig'),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
