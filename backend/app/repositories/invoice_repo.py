"""
F11: Invoice repository – gọi PKG_DAT_PHONG.CHECK_OUT, PKG_HOA_DON.LAP_DIEU_CHINH,
     PKG_DAT_PHONG.TINH_TRUOC_CHECK_OUT và truy vấn chi tiết hóa đơn.
"""
import logging
from typing import Dict, Any, Optional
import oracledb

from app.db import fetch_cursor_as_dicts
from app.errors import BusinessException, parse_oracle_error
from app.config import settings

logger = logging.getLogger(__name__)


class InvoiceRepository:

    # ------------------------------------------------------------------
    # Preview check-out (không ghi DB) – màn hình tổng kết trước khi xác nhận
    # ------------------------------------------------------------------
    @staticmethod
    def preview_checkout(
        conn: oracledb.Connection,
        booking_id: int,
        surcharge: float = 0.0,
        discount: float = 0.0
    ) -> Dict[str, Any]:
        with conn.cursor() as cur:
            p_tp   = cur.var(oracledb.NUMBER)
            p_qg   = cur.var(oracledb.NUMBER)
            p_pt   = cur.var(oracledb.NUMBER)
            p_gg   = cur.var(oracledb.NUMBER)
            p_vat  = cur.var(oracledb.NUMBER)
            p_tong = cur.var(oracledb.NUMBER)
            p_paid = cur.var(oracledb.NUMBER)
            p_con  = cur.var(oracledb.NUMBER)
            try:
                cur.callproc(
                    f"{settings.ORA_SCHEMA}.PKG_DAT_PHONG.TINH_TRUOC_CHECK_OUT",
                    [
                        booking_id,
                        surcharge,
                        discount,
                        p_tp, p_qg, p_pt, p_gg, p_vat, p_tong, p_paid, p_con
                    ]
                )
            except oracledb.DatabaseError as e:
                raise parse_oracle_error(e)

            # Fetch booking code
            cur.execute(
                "SELECT ma_tra_cuu FROM dat_phong WHERE dat_phong_id = :id",
                {"id": booking_id}
            )
            row = cur.fetchone()
            code = row[0] if row else ""

            return {
                "booking_id": booking_id,
                "booking_code": code,
                "tienPhong":    float(p_tp.getvalue() or 0),
                "tienQuaGio":   float(p_qg.getvalue() or 0),
                "phuThu":       float(p_pt.getvalue() or 0),
                "giamGia":      float(p_gg.getvalue() or 0),
                "tienVat":      float(p_vat.getvalue() or 0),
                "tongHoaDon":   float(p_tong.getvalue() or 0),
                "daThanhToan":  float(p_paid.getvalue() or 0),
                "conPhaiThu":   float(p_con.getvalue() or 0),
            }

    # ------------------------------------------------------------------
    # Thực hiện check-out – gọi PKG_DAT_PHONG.CHECK_OUT
    # ------------------------------------------------------------------
    @staticmethod
    def checkout(
        conn: oracledb.Connection,
        booking_id: int,
        issuer_user_id: int,
        surcharge: float = 0.0,
        surcharge_desc: Optional[str] = None,
        discount: float = 0.0,
        discount_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        with conn.cursor() as cur:
            p_hoa_don_id  = cur.var(oracledb.NUMBER)
            p_tong_hd     = cur.var(oracledb.NUMBER)
            p_con_phai_thu = cur.var(oracledb.NUMBER)
            try:
                cur.callproc(
                    f"{settings.ORA_SCHEMA}.PKG_DAT_PHONG.CHECK_OUT",
                    [
                        booking_id,
                        issuer_user_id,
                        surcharge,
                        surcharge_desc,
                        discount,
                        discount_reason,
                        p_hoa_don_id,
                        p_tong_hd,
                        p_con_phai_thu
                    ]
                )
            except oracledb.DatabaseError as e:
                raise parse_oracle_error(e)

            # Lấy trạng thái mới và mã đơn, số hóa đơn
            cur.execute("""
                SELECT dp.ma_tra_cuu, dp.trang_thai, hd.so_hoa_don
                  FROM dat_phong dp
                  JOIN hoa_don hd ON hd.hoa_don_id = :hd_id
                 WHERE dp.dat_phong_id = :dp_id
            """, {"hd_id": int(p_hoa_don_id.getvalue()), "dp_id": booking_id})
            row = cur.fetchone()
            code = row[0] if row else ""
            new_status = row[1] if row else "CHECKED_OUT"
            inv_number = int(row[2]) if row else 0
            hd_id = int(p_hoa_don_id.getvalue())
            tong = float(p_tong_hd.getvalue() or 0)
            con = float(p_con_phai_thu.getvalue() or 0)

            msg = f"Trả phòng thành công. Hóa đơn #{inv_number} đã được lập."
            if con > 0:
                msg += f" Còn phải thu: {con:,.0f} đ."
            elif con < 0:
                msg += f" Thừa: {abs(con):,.0f} đ cần hoàn."

            return {
                "booking_id": booking_id,
                "booking_code": code,
                "new_status": new_status,
                "invoice_id": hd_id,
                "invoice_number": inv_number,
                "total_invoice": tong,
                "remaining_amount": con,
                "message": msg
            }

    # ------------------------------------------------------------------
    # Lấy chi tiết hóa đơn (kèm chi tiết dòng và thông tin đơn / khách)
    # ------------------------------------------------------------------
    @staticmethod
    def get_invoice(conn: oracledb.Connection, invoice_id: int) -> Optional[Dict[str, Any]]:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT hd.hoa_don_id, hd.so_hoa_don, hd.dat_phong_id, dp.ma_tra_cuu,
                       hd.tong_tien, hd.ngay_lap,
                       u.ho_ten AS nguoi_lap,
                       NVL(hd.la_dieu_chinh, FALSE) AS la_dieu_chinh,
                       hd.hoa_don_goc_id,
                       kh.ho_ten AS khach_ho_ten, kh.sdt,
                       (SELECT p.ma_phong FROM dat_phong_doan dpd
                          JOIN phong p ON p.phong_id = dpd.phong_id
                         WHERE dpd.dat_phong_id = dp.dat_phong_id AND ROWNUM = 1) AS ma_phong,
                       (SELECT lp.ma_hang FROM dat_phong_doan dpd
                          JOIN phong p ON p.phong_id = dpd.phong_id
                          JOIN loai_phong lp ON lp.loai_phong_id = p.loai_phong_id
                         WHERE dpd.dat_phong_id = dp.dat_phong_id AND ROWNUM = 1) AS ma_hang,
                       dp.tu_luc, dp.den_luc, dp.nhan_thuc_te, dp.tra_thuc_te
                  FROM hoa_don hd
                  JOIN dat_phong dp ON dp.dat_phong_id = hd.dat_phong_id
                  JOIN khach_hang kh ON kh.khach_hang_id = dp.khach_hang_id
                  LEFT JOIN nguoi_dung u ON u.nguoi_dung_id = hd.nguoi_lap_id
                 WHERE hd.hoa_don_id = :id
            """, {"id": invoice_id})
            rows = fetch_cursor_as_dicts(cur)
            if not rows:
                return None
            hd = rows[0]

            # Chi tiết dòng
            cur.execute("""
                SELECT loai_dong, mo_ta, so_tien, thue_suat
                  FROM chi_tiet_hoa_don
                 WHERE hoa_don_id = :id
                 ORDER BY chi_tiet_id
            """, {"id": invoice_id})
            line_rows = fetch_cursor_as_dicts(cur)
            lines = [
                {
                    "loaiDong": r["loai_dong"],
                    "moTa": r["mo_ta"],
                    "soTien": float(r["so_tien"] or 0),
                    "thueSuat": float(r["thue_suat"]) if r["thue_suat"] else None
                }
                for r in line_rows
            ]

            return {
                "hoaDonId": hd["hoa_don_id"],
                "soHoaDon": hd["so_hoa_don"],
                "datPhongId": hd["dat_phong_id"],
                "maTraCuu": hd["ma_tra_cuu"],
                "tongTien": float(hd["tong_tien"] or 0),
                "ngayLap": hd["ngay_lap"],
                "nguoiLap": hd["nguoi_lap"],
                "laDieuChinh": bool(hd["la_dieu_chinh"]),
                "hoaDonGocId": hd["hoa_don_goc_id"],
                "hoTen": hd["khach_ho_ten"],
                "sdt": hd["sdt"],
                "maPhong": hd["ma_phong"],
                "maHang": hd["ma_hang"],
                "checkin": hd["tu_luc"],
                "checkout": hd["den_luc"],
                "nhanThucTe": hd["nhan_thuc_te"],
                "traThucTe": hd["tra_thuc_te"],
                "chiTiet": lines,
            }

    # ------------------------------------------------------------------
    # Lập hóa đơn điều chỉnh – gọi PKG_HOA_DON.LAP_DIEU_CHINH
    # ------------------------------------------------------------------
    @staticmethod
    def adjust_invoice(
        conn: oracledb.Connection,
        invoice_id: int,
        issuer_user_id: int,
        amount: float,
        description: str
    ) -> Dict[str, Any]:
        with conn.cursor() as cur:
            p_dieu_id  = cur.var(oracledb.NUMBER)
            p_dieu_so  = cur.var(oracledb.NUMBER)
            try:
                cur.callproc(
                    f"{settings.ORA_SCHEMA}.PKG_HOA_DON.LAP_DIEU_CHINH",
                    [invoice_id, issuer_user_id, description, amount, p_dieu_id, p_dieu_so]
                )
            except oracledb.DatabaseError as e:
                raise parse_oracle_error(e)

            dieu_id = int(p_dieu_id.getvalue())
            dieu_so = int(p_dieu_so.getvalue())

            msg = f"Hóa đơn điều chỉnh #{dieu_so} đã được lập."
            if amount > 0:
                msg += f" Phụ thu thêm: {amount:,.0f} đ."
            else:
                msg += f" Giảm trừ: {abs(amount):,.0f} đ."

            return {
                "hoaDonGocId": invoice_id,
                "hoaDonDieuChinhId": dieu_id,
                "soHoaDonDieuChinh": dieu_so,
                "soTien": amount,
                "moTa": description,
                "message": msg
            }
