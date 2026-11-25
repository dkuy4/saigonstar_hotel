import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
import oracledb

from app.schemas.audit import AuditLogItem, AuditLogsResponse, StateAtResponse

logger = logging.getLogger(__name__)


def _parse_audit_json(val: Any) -> Optional[dict[str, Any]]:
    """Parse JSON/CLOB/dict from audit log column safely."""
    if val is None:
        return None
    if isinstance(val, dict):
        return val
    if hasattr(val, "read"):
        val = val.read()
    if not isinstance(val, str):
        return None
    val_str = val.strip()
    if not val_str:
        return None
    try:
        return json.loads(val_str)
    except Exception:
        pass
    try:
        import ast
        res = ast.literal_eval(val_str)
        if isinstance(res, dict):
            return res
    except Exception:
        pass
    return {"raw": val_str}


def get_filter_metadata(conn: oracledb.Connection) -> tuple[list[str], list[str]]:
    """Get distinct tables and actions for filter dropdowns."""
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT BANG FROM NHAT_KY_KIEM_TOAN ORDER BY BANG")
        tables = [row[0] for row in cur.fetchall() if row[0]]

        cur.execute("SELECT DISTINCT HANH_DONG FROM NHAT_KY_KIEM_TOAN ORDER BY HANH_DONG")
        actions = [row[0] for row in cur.fetchall() if row[0]]

    return tables, actions


def list_audit_logs(
    conn: oracledb.Connection,
    page: int = 1,
    page_size: int = 20,
    bang: Optional[str] = None,
    khoa_dong: Optional[str] = None,
    vai_tro: Optional[str] = None,
    kenh: Optional[str] = None,
    hanh_dong: Optional[str] = None,
    nguoi_dung: Optional[str] = None,
    tu_ngay: Optional[datetime] = None,
    den_ngay: Optional[datetime] = None,
) -> AuditLogsResponse:
    """Query audit logs with filtering, sorting and pagination."""
    page = max(1, page)
    page_size = min(max(5, page_size), 100)
    offset = (page - 1) * page_size

    where_clauses = ["1 = 1"]
    params: dict[str, Any] = {}

    if bang:
        where_clauses.append("n.BANG = :bang")
        params["bang"] = bang.strip().upper()

    if khoa_dong:
        where_clauses.append("n.KHOA_DONG = :khoa_dong")
        params["khoa_dong"] = khoa_dong.strip()

    if vai_tro:
        where_clauses.append("n.VAI_TRO = :vai_tro")
        params["vai_tro"] = vai_tro.strip().upper()

    if kenh:
        where_clauses.append("n.KENH = :kenh")
        params["kenh"] = kenh.strip().upper()

    if hanh_dong:
        where_clauses.append("n.HANH_DONG = :hanh_dong")
        params["hanh_dong"] = hanh_dong.strip().upper()

    if nguoi_dung:
        where_clauses.append("(LOWER(u.TEN_DANG_NHAP) LIKE :nguoi_dung OR LOWER(u.HO_TEN) LIKE :nguoi_dung)")
        params["nguoi_dung"] = f"%{nguoi_dung.strip().lower()}%"

    if tu_ngay:
        naive_tu = tu_ngay.astimezone(timezone.utc).replace(tzinfo=None) if tu_ngay.tzinfo else tu_ngay
        where_clauses.append("n.THOI_DIEM >= FROM_TZ(CAST(:tu_ngay AS TIMESTAMP), '+00:00')")
        params["tu_ngay"] = naive_tu

    if den_ngay:
        naive_den = den_ngay.astimezone(timezone.utc).replace(tzinfo=None) if den_ngay.tzinfo else den_ngay
        where_clauses.append("n.THOI_DIEM <= FROM_TZ(CAST(:den_ngay AS TIMESTAMP), '+00:00')")
        params["den_ngay"] = naive_den

    where_sql = " AND ".join(where_clauses)

    with conn.cursor() as cur:
        # Total count
        count_sql = f"""
            SELECT COUNT(*)
            FROM NHAT_KY_KIEM_TOAN n
            LEFT JOIN NGUOI_DUNG u ON n.NGUOI_THUC_HIEN_ID = u.NGUOI_DUNG_ID
            WHERE {where_sql}
        """
        cur.execute(count_sql, params)
        total = cur.fetchone()[0]

        # Items page
        query_sql = f"""
            SELECT n.NHAT_KY_ID, n.BANG, n.KHOA_DONG, n.HANH_DONG, n.THOI_DIEM,
                   n.NGUOI_THUC_HIEN_ID, u.TEN_DANG_NHAP, n.VAI_TRO, n.KENH,
                   n.DIA_CHI_IP, n.LY_DO, n.GIA_TRI_CU, n.GIA_TRI_MOI
            FROM NHAT_KY_KIEM_TOAN n
            LEFT JOIN NGUOI_DUNG u ON n.NGUOI_THUC_HIEN_ID = u.NGUOI_DUNG_ID
            WHERE {where_sql}
            ORDER BY n.THOI_DIEM DESC, n.NHAT_KY_ID DESC
            OFFSET :offset ROWS FETCH NEXT :page_size ROWS ONLY
        """
        query_params = {**params, "offset": offset, "page_size": page_size}
        cur.execute(query_sql, query_params)
        rows = cur.fetchall()

    items: list[AuditLogItem] = []
    for r in rows:
        items.append(
            AuditLogItem(
                nhatKyId=r[0],
                bang=r[1],
                khoaDong=r[2],
                hanhDong=r[3],
                thoiDiem=r[4],
                nguoiThucHienId=r[5],
                tenDangNhap=r[6],
                vaiTro=r[7],
                kenh=r[8],
                diaChiIp=r[9],
                lyDo=r[10],
                giaTriCu=_parse_audit_json(r[11]),
                giaTriMoi=_parse_audit_json(r[12]),
            )
        )

    tables, actions = get_filter_metadata(conn)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return AuditLogsResponse(
        total=total,
        page=page,
        pageSize=page_size,
        totalPages=total_pages,
        items=items,
        tables=tables,
        actions=actions,
    )


def get_state_at(
    conn: oracledb.Connection,
    bang: str,
    khoa_dong: str,
    target_time: datetime,
) -> StateAtResponse:
    """
    Retrieve the state of a record at a specific point in time (BR-46, AC-14).
    Finds the latest audit record with THOI_DIEM <= target_time.
    """
    cleaned_bang = bang.strip().upper()
    cleaned_khoa = khoa_dong.strip()
    naive_target = target_time.astimezone(timezone.utc).replace(tzinfo=None) if target_time.tzinfo else target_time

    sql = """
        SELECT n.NHAT_KY_ID, n.THOI_DIEM, n.HANH_DONG, u.TEN_DANG_NHAP, n.VAI_TRO, n.GIA_TRI_MOI
        FROM NHAT_KY_KIEM_TOAN n
        LEFT JOIN NGUOI_DUNG u ON n.NGUOI_THUC_HIEN_ID = u.NGUOI_DUNG_ID
        WHERE n.BANG = :bang
          AND n.KHOA_DONG = :khoa_dong
          AND n.THOI_DIEM <= FROM_TZ(CAST(:target_time AS TIMESTAMP), '+00:00')
        ORDER BY n.THOI_DIEM DESC, n.NHAT_KY_ID DESC
        FETCH FIRST 1 ROWS ONLY
    """

    with conn.cursor() as cur:
        cur.execute(
            sql,
            {
                "bang": cleaned_bang,
                "khoa_dong": cleaned_khoa,
                "target_time": naive_target,
            },
        )
        row = cur.fetchone()

    if not row:
        return StateAtResponse(
            found=False,
            bang=cleaned_bang,
            khoaDong=cleaned_khoa,
            targetTime=target_time,
            message="Không tìm thấy bản ghi nào tại thời điểm này (có thể đối tượng chưa được tạo trước mốc thời gian đã chọn).",
        )

    action = row[2]
    parsed_state = _parse_audit_json(row[5])

    if action == "XOA":
        return StateAtResponse(
            found=True,
            bang=cleaned_bang,
            khoaDong=cleaned_khoa,
            targetTime=target_time,
            auditTime=row[1],
            action=action,
            performedBy=row[3],
            role=row[4],
            state=None,
            message="Đối tượng đã bị xóa tại hoặc trước thời điểm này.",
        )

    return StateAtResponse(
        found=True,
        bang=cleaned_bang,
        khoaDong=cleaned_khoa,
        targetTime=target_time,
        auditTime=row[1],
        action=action,
        performedBy=row[3],
        role=row[4],
        state=parsed_state,
        message="Trạng thái đối tượng được tái hiện thành công từ nhật ký kiểm toán.",
    )
