import logging
from typing import Optional, Dict, Any
import oracledb

from app.db import fetch_cursor_as_dicts
from app.errors import parse_oracle_error

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
          FROM giao_dich_thanh_toan g
          JOIN dat_phong dp ON dp.dat_phong_id = g.dat_phong_id
          JOIN khach_hang kh ON kh.khach_hang_id = dp.khach_hang_id
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
