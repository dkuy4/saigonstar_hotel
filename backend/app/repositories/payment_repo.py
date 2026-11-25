import logging
from datetime import datetime, date
from typing import Optional, Dict, Any, List
import oracledb

from app.db import fetch_cursor_as_dicts
from app.errors import parse_oracle_error, BusinessException

logger = logging.getLogger(__name__)

class PaymentRepository:
    @staticmethod
    def create_gateway_transaction(
        conn: oracledb.Connection,
        booking_id: int,
        reference_code: str
    ) -> int:
        with conn.cursor() as cur:
            p_giao_dich_id = cur.var(oracledb.NUMBER)
            try:
                cur.callproc(
                    "PKG_THANH_TOAN.TAO_GIAO_DICH_CONG",
                    [booking_id, reference_code, p_giao_dich_id]
                )
                return int(p_giao_dich_id.getvalue())
            except oracledb.DatabaseError as e:
                raise parse_oracle_error(e)

    @staticmethod
    def process_gateway_callback(
        conn: oracledb.Connection,
        reference_code: str,
        is_success: bool
    ) -> str:
        with conn.cursor() as cur:
            p_ket_qua = cur.var(oracledb.STRING)
            try:
                cur.callproc(
                    "PKG_THANH_TOAN.XU_LY_KET_QUA_CONG",
                    [reference_code, 1 if is_success else 0, p_ket_qua]
                )
                return str(p_ket_qua.getvalue())
            except oracledb.DatabaseError as e:
                raise parse_oracle_error(e)

    @staticmethod
    def get_payment_info_by_ref(
        conn: oracledb.Connection,
        reference_code: str
    ) -> Optional[Dict[str, Any]]:
        sql = """
        SELECT g.giao_dich_id, g.ma_tham_chieu_cong, g.so_tien, g.trang_thai AS trang_thai_giao_dich,
               dp.dat_phong_id, dp.ma_tra_cuu, dp.trang_thai AS trang_thai_don, dp.han_giu_cho,
               kh.ho_ten, kh.email
          FROM hotel_owner.giao_dich_thanh_toan g
          JOIN hotel_owner.dat_phong dp ON dp.dat_phong_id = g.dat_phong_id
          JOIN hotel_owner.khach_hang kh ON kh.khach_hang_id = dp.khach_hang_id
         WHERE g.ma_tham_chieu_cong = :ref
        """
        with conn.cursor() as cur:
            cur.execute(sql, {"ref": reference_code})
            rows = fetch_cursor_as_dicts(cur)
            if not rows:
                return None
            r = rows[0]
            return {
                "transaction_id": r["giao_dich_id"],
                "reference_code": r["ma_tham_chieu_cong"],
                "amount": float(r["so_tien"]),
                "status": r["trang_thai_giao_dich"],
                "booking_id": r["dat_phong_id"],
                "booking_code": r["ma_tra_cuu"],
                "booking_status": r["trang_thai_don"],
                "hold_expires_at": r["han_giu_cho"],
                "customer_name": r["ho_ten"],
                "customer_email": r["email"]
            }

    # --- F12: Thu tiền quầy, hoàn tiền, đối soát ---

    @staticmethod
    def record_desk_payment(
        conn: oracledb.Connection,
        booking_id: int,
        method: str,
        amount: float,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Thu tiền tại quầy (tiền mặt, chuyển khoản, thẻ) qua PKG_THANH_TOAN.GHI_NHAN_QUAY (FR-34, BR-45)."""
        method_norm = method.strip().upper()
        if method_norm not in ('TIEN_MAT', 'CHUYEN_KHOAN', 'THE'):
            raise BusinessException("VALIDATION_ERROR", f"Phương thức thanh toán không hợp lệ: {method}")

        with conn.cursor() as cur:
            try:
                if notes and notes.strip():
                    cur.callproc("PKG_NGU_CANH.DAT_LY_DO", [notes.strip()[:500]])

                out_id = cur.var(oracledb.NUMBER)
                cur.callproc(
                    "PKG_THANH_TOAN.GHI_NHAN_QUAY",
                    [booking_id, method_norm, amount, out_id]
                )
                tx_id = int(out_id.getvalue())
                conn.commit()

                cur.execute(
                    """
                    SELECT giao_dich_id, dat_phong_id, phuong_thuc, so_tien, trang_thai, ngay_giao_dich
                      FROM hotel_owner.giao_dich_thanh_toan
                     WHERE giao_dich_id = :p_id
                    """,
                    {"p_id": tx_id}
                )
                row = cur.fetchone()
                return {
                    "transaction_id": row[0],
                    "booking_id": row[1],
                    "method": row[2],
                    "amount": float(row[3]),
                    "status": row[4],
                    "created_at": row[5]
                }
            except oracledb.DatabaseError as e:
                conn.rollback()
                raise parse_oracle_error(e)

    @staticmethod
    def create_refund(
        conn: oracledb.Connection,
        booking_id: int,
        amount: float,
        reason: str,
        requester_id: Optional[int] = None,
        approver_id: Optional[int] = None
    ) -> None:
        """Tạo yêu cầu hoàn tiền qua PKG_THANH_TOAN.TAO_HOAN (BR-25)."""
        with conn.cursor() as cur:
            try:
                cur.callproc(
                    "PKG_THANH_TOAN.TAO_HOAN",
                    [booking_id, amount, reason.strip(), requester_id, approver_id]
                )
                conn.commit()
            except oracledb.DatabaseError as e:
                conn.rollback()
                raise parse_oracle_error(e)

    @staticmethod
    def approve_refund(
        conn: oracledb.Connection,
        refund_id: int,
        approver_id: int,
        approved: bool
    ) -> None:
        """Duyệt hoặc từ chối hoàn tiền qua PKG_THANH_TOAN.DUYET_HOAN_TIEN (BR-25, BR-26)."""
        with conn.cursor() as cur:
            try:
                cur.callproc(
                    "PKG_THANH_TOAN.DUYET_HOAN_TIEN",
                    [refund_id, approver_id, 1 if approved else 0]
                )
                conn.commit()
            except oracledb.DatabaseError as e:
                conn.rollback()
                raise parse_oracle_error(e)

    @staticmethod
    def complete_refund(
        conn: oracledb.Connection,
        refund_id: int
    ) -> None:
        """Xác nhận đã chi tiền hoàn qua PKG_THANH_TOAN.XAC_NHAN_DA_HOAN (FR-37)."""
        with conn.cursor() as cur:
            try:
                cur.callproc("PKG_THANH_TOAN.XAC_NHAN_DA_HOAN", [refund_id])
                conn.commit()
            except oracledb.DatabaseError as e:
                conn.rollback()
                raise parse_oracle_error(e)

    @staticmethod
    def override_refund(
        conn: oracledb.Connection,
        booking_id: int,
        amount: float,
        reason: str,
        manager_id: int
    ) -> None:
        """Hoàn ngoại lệ do quản lý thực hiện qua PKG_THANH_TOAN.HOAN_NGOAI_LE (BR-26)."""
        with conn.cursor() as cur:
            try:
                cur.callproc(
                    "PKG_THANH_TOAN.HOAN_NGOAI_LE",
                    [booking_id, amount, reason.strip(), manager_id]
                )
                conn.commit()
            except oracledb.DatabaseError as e:
                conn.rollback()
                raise parse_oracle_error(e)

    @staticmethod
    def get_refunds(
        conn: oracledb.Connection,
        status: Optional[str] = None,
        booking_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Truy vấn danh sách yêu cầu hoàn tiền."""
        where_clauses = ["1 = 1"]
        params: Dict[str, Any] = {}

        if status and status.upper() != "ALL":
            where_clauses.append("h.trang_thai = :p_status")
            params["p_status"] = status.upper()

        if booking_id is not None:
            where_clauses.append("g.dat_phong_id = :p_booking_id")
            params["p_booking_id"] = booking_id

        where_sql = " AND ".join(where_clauses)

        with conn.cursor() as cur:
            # Count
            count_sql = f"""
                SELECT COUNT(*)
                  FROM hotel_owner.hoan_tien h
                  JOIN hotel_owner.giao_dich_thanh_toan g ON g.giao_dich_id = h.giao_dich_id
                 WHERE {where_sql}
            """
            cur.execute(count_sql, params)
            total = cur.fetchone()[0]

            offset = (page - 1) * page_size
            data_sql = f"""
                SELECT h.hoan_tien_id, h.giao_dich_id, g.dat_phong_id, dp.ma_tra_cuu,
                       kh.ho_ten, kh.sdt, g.phuong_thuc, g.kenh, h.so_tien, h.ly_do,
                       h.trang_thai, nd_req.ho_ten AS requester_name, nd_app.ho_ten AS approver_name,
                       h.ngay_tao
                  FROM hotel_owner.hoan_tien h
                  JOIN hotel_owner.giao_dich_thanh_toan g ON g.giao_dich_id = h.giao_dich_id
                  JOIN hotel_owner.dat_phong dp ON dp.dat_phong_id = g.dat_phong_id
                  JOIN hotel_owner.khach_hang kh ON kh.khach_hang_id = dp.khach_hang_id
                  LEFT JOIN hotel_owner.nguoi_dung nd_req ON nd_req.nguoi_dung_id = h.nguoi_de_nghi_id
                  LEFT JOIN hotel_owner.nguoi_dung nd_app ON nd_app.nguoi_dung_id = h.nguoi_duyet_id
                 WHERE {where_sql}
                 ORDER BY h.hoan_tien_id DESC
                 OFFSET :p_offset ROWS FETCH NEXT :p_page_size ROWS ONLY
            """
            params_query = dict(params)
            params_query["p_offset"] = offset
            params_query["p_page_size"] = page_size

            cur.execute(data_sql, params_query)
            rows = cur.fetchall()

            items = []
            for r in rows:
                items.append({
                    "refundId": r[0],
                    "transactionId": r[1],
                    "bookingId": r[2],
                    "bookingCode": r[3],
                    "customerName": r[4],
                    "customerPhone": r[5],
                    "method": r[6],
                    "channel": r[7],
                    "amount": float(r[8]),
                    "reason": r[9],
                    "status": r[10],
                    "requesterName": r[11],
                    "approverName": r[12],
                    "createdAt": r[13]
                })

            return {
                "items": items,
                "total": total,
                "page": page,
                "pageSize": page_size
            }

    @staticmethod
    def get_daily_reconciliation(
        conn: oracledb.Connection,
        target_date: date
    ) -> Dict[str, Any]:
        """Báo cáo đối soát doanh thu theo phương thức trong một ngày (FR-39)."""
        with conn.cursor() as cur:
            try:
                # Call PKG_THANH_TOAN.DOI_SOAT_NGAY
                res_cursor = cur.callfunc(
                    "PKG_THANH_TOAN.DOI_SOAT_NGAY",
                    oracledb.CURSOR,
                    [target_date]
                )
                rows = fetch_cursor_as_dicts(res_cursor)
                res_cursor.close()

                items = []
                grand_total_collected = 0.0
                grand_total_refunded = 0.0
                grand_net_revenue = 0.0

                for r in rows:
                    collected = float(r["tong_thu"] or 0)
                    refunded = float(r["tong_hoan"] or 0)
                    net = float(r["thuc_thu"] or 0)

                    grand_total_collected += collected
                    grand_total_refunded += refunded
                    grand_net_revenue += net

                    items.append({
                        "paymentMethod": r["phuong_thuc"],
                        "channel": r["kenh"],
                        "totalCollected": collected,
                        "totalRefunded": refunded,
                        "netRevenue": net
                    })

                return {
                    "date": target_date.strftime("%Y-%m-%d"),
                    "items": items,
                    "grandTotalCollected": grand_total_collected,
                    "grandTotalRefunded": grand_total_refunded,
                    "grandNetRevenue": grand_net_revenue
                }
            except oracledb.DatabaseError as e:
                raise parse_oracle_error(e)
