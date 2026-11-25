from datetime import datetime, timezone, timedelta
import logging
from typing import Optional, Dict, Any, List
import oracledb

from app.db import fetch_cursor_as_dicts
from app.errors import BusinessException, parse_oracle_error
from app.schemas.booking import CustomerInfo
from app.config import settings
from app.services.crypto import encrypt_id_document, decrypt_id_document, mask_id_document

logger = logging.getLogger(__name__)

class BookingRepository:
    @staticmethod
    def get_suggested_rooms(
        conn: oracledb.Connection,
        room_type_id: int,
        checkin: datetime,
        checkout: datetime
    ) -> List[Dict[str, Any]]:
        try:
            with conn.cursor() as cur:
                res_cur = cur.callfunc(
                    "PKG_DAT_PHONG.GOI_Y_PHONG",
                    oracledb.CURSOR,
                    [room_type_id, checkin, checkout]
                )
                rows = fetch_cursor_as_dicts(res_cur)
                res_cur.close()
                return [
                    {
                        "room_id": r["phong_id"],
                        "room_number": r["ma_phong"],
                        "floor": r["so_tang"]
                    }
                    for r in rows
                ]
        except Exception as e:
            logger.warning(f"Failed to fetch suggested rooms: {e}")
            return []

    @staticmethod
    def get_room_type_id(conn: oracledb.Connection, room_type_code: str) -> Optional[int]:
        with conn.cursor() as cur:
            cur.execute("SELECT loai_phong_id FROM loai_phong WHERE ma_hang = :code", {"code": room_type_code.upper()})
            row = cur.fetchone()
            return row[0] if row else None

    @staticmethod
    def create_booking(
        conn: oracledb.Connection,
        type_: str,
        room_type: str,
        room_id: Optional[int],
        checkin: datetime,
        checkout: datetime,
        guests: int,
        payment_method: str,
        channel: str,
        customer: CustomerInfo,
        lang: str,
        agree_time: datetime
    ) -> Dict[str, Any]:
        with conn.cursor() as cur:
            p_id = cur.var(oracledb.NUMBER)
            p_code = cur.var(oracledb.STRING)
            p_st = cur.var(oracledb.STRING)
            p_room = cur.var(oracledb.NUMBER)
            p_room_amt = cur.var(oracledb.NUMBER)
            p_vat = cur.var(oracledb.NUMBER)
            p_tot = cur.var(oracledb.NUMBER)
            p_hold = cur.var(oracledb.DB_TYPE_TIMESTAMP_TZ)

            try:
                cur.callproc(
                    "PKG_DAT_PHONG.TAO_DON",
                    [
                        customer.full_name,
                        customer.phone,
                        customer.email,
                        customer.nationality,
                        lang,
                        type_,
                        channel,
                        room_type.upper(),
                        room_id,
                        checkin,
                        checkout,
                        guests,
                        payment_method,
                        agree_time,
                        p_id,
                        p_code,
                        p_st,
                        p_room,
                        p_room_amt,
                        p_vat,
                        p_tot,
                        p_hold
                    ]
                )
            except oracledb.DatabaseError as e:
                biz_exc = parse_oracle_error(e)
                # If ROOM_CONFLICT (-20001) occurs (e.g. receptionist chose a specific room),
                # attach suggested rooms to error data (BR-11)
                if biz_exc.code == "ROOM_CONFLICT":
                    type_id = BookingRepository.get_room_type_id(conn, room_type)
                    if type_id:
                        suggestions = BookingRepository.get_suggested_rooms(conn, type_id, checkin, checkout)
                        biz_exc.data = {"suggested_rooms": suggestions}
                raise biz_exc

            return {
                "id": p_id.getvalue(),
                "booking_code": p_code.getvalue(),
                "status": p_st.getvalue(),
                "room_type": room_type.upper(),
                "room_id": p_room.getvalue(),
                "checkin": checkin,
                "checkout": checkout,
                "guests": guests,
                "room_amount": float(p_room_amt.getvalue() or 0),
                "vat_rate": 0.08, # standard VAT rate from config
                "vat_amount": float(p_vat.getvalue() or 0),
                "total_amount": float(p_tot.getvalue() or 0),
                "hold_expires_at": p_hold.getvalue(),
                "payment_method": payment_method,
                "channel": channel,
                "customer": customer
            }

    @staticmethod
    def _map_booking_row(r: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": r["dat_phong_id"],
            "booking_code": r["ma_tra_cuu"],
            "status": r["trang_thai"],
            "room_type": r["ma_hang"] or "STANDARD",
            "room_id": r["phong_id"],
            "checkin": r["tu_luc"],
            "checkout": r["den_luc"],
            "guests": r["so_khach"],
            "room_amount": float(r["tien_phong"]),
            "vat_rate": float(r["thue_suat"]),
            "vat_amount": float(r["tien_vat"]),
            "total_amount": float(r["tong_tien"]),
            "hold_expires_at": r["han_giu_cho"],
            "payment_method": "TRUC_TUYEN" if r["trang_thai"] == "HOLD" else "KHI_NHAN_PHONG",
            "channel": r["kenh_dat"],
            "customer": CustomerInfo(
                fullName=r["ho_ten"],
                phone=r["sdt"],
                email=r["email"],
                nationality=r["quoc_tich"] or "VN"
            )
        }

    @staticmethod
    def get_booking_by_code(conn: oracledb.Connection, code: str) -> Optional[Dict[str, Any]]:
        sql = """
        SELECT dp.dat_phong_id, dp.ma_tra_cuu, dp.trang_thai, dp.loai_dat, dp.kenh_dat,
               dp.tu_luc, dp.den_luc, dp.han_giu_cho, dp.so_khach,
               dp.tien_phong, dp.thue_suat, dp.tien_vat, dp.tong_tien,
               kh.ho_ten, kh.sdt, kh.email, kh.quoc_tich,
               (SELECT lp.ma_hang FROM dat_phong_doan dpd
                  JOIN phong p ON p.phong_id = dpd.phong_id
                  JOIN loai_phong lp ON lp.loai_phong_id = p.loai_phong_id
                 WHERE dpd.dat_phong_id = dp.dat_phong_id AND ROWNUM = 1) AS ma_hang,
               (SELECT dpd.phong_id FROM dat_phong_doan dpd
                 WHERE dpd.dat_phong_id = dp.dat_phong_id AND ROWNUM = 1) AS phong_id
          FROM dat_phong dp
          JOIN khach_hang kh ON kh.khach_hang_id = dp.khach_hang_id
         WHERE UPPER(dp.ma_tra_cuu) = UPPER(:code)
        """
        with conn.cursor() as cur:
            cur.execute(sql, {"code": code})
            rows = fetch_cursor_as_dicts(cur)
            if not rows:
                return None
            return BookingRepository._map_booking_row(rows[0])

    @staticmethod
    def get_booking_by_code_and_email(conn: oracledb.Connection, code: str, email: str) -> Optional[Dict[str, Any]]:
        sql = """
        SELECT dp.dat_phong_id, dp.ma_tra_cuu, dp.trang_thai, dp.loai_dat, dp.kenh_dat,
               dp.tu_luc, dp.den_luc, dp.han_giu_cho, dp.so_khach,
               dp.tien_phong, dp.thue_suat, dp.tien_vat, dp.tong_tien,
               kh.ho_ten, kh.sdt, kh.email, kh.quoc_tich,
               (SELECT lp.ma_hang FROM dat_phong_doan dpd
                  JOIN phong p ON p.phong_id = dpd.phong_id
                  JOIN loai_phong lp ON lp.loai_phong_id = p.loai_phong_id
                 WHERE dpd.dat_phong_id = dp.dat_phong_id AND ROWNUM = 1) AS ma_hang,
               (SELECT dpd.phong_id FROM dat_phong_doan dpd
                 WHERE dpd.dat_phong_id = dp.dat_phong_id AND ROWNUM = 1) AS phong_id
          FROM dat_phong dp
          JOIN khach_hang kh ON kh.khach_hang_id = dp.khach_hang_id
         WHERE UPPER(dp.ma_tra_cuu) = UPPER(:code)
           AND LOWER(kh.email) = LOWER(:email)
        """
        with conn.cursor() as cur:
            cur.execute(sql, {"code": code.strip(), "email": email.strip().lower()})
            rows = fetch_cursor_as_dicts(cur)
            if not rows:
                return None
            return BookingRepository._map_booking_row(rows[0])

    @staticmethod
    def get_booking_by_id_or_code(conn: oracledb.Connection, id_or_code: Any) -> Optional[Dict[str, Any]]:
        try:
            val_int = int(id_or_code)
            is_id = True
        except (ValueError, TypeError):
            is_id = False

        sql = f"""
        SELECT dp.dat_phong_id, dp.ma_tra_cuu, dp.trang_thai, dp.loai_dat, dp.kenh_dat,
               dp.tu_luc, dp.den_luc, dp.han_giu_cho, dp.so_khach,
               dp.tien_phong, dp.thue_suat, dp.tien_vat, dp.tong_tien,
               kh.ho_ten, kh.sdt, kh.email, kh.quoc_tich,
               (SELECT lp.ma_hang FROM dat_phong_doan dpd
                  JOIN phong p ON p.phong_id = dpd.phong_id
                  JOIN loai_phong lp ON lp.loai_phong_id = p.loai_phong_id
                 WHERE dpd.dat_phong_id = dp.dat_phong_id AND ROWNUM = 1) AS ma_hang,
               (SELECT dpd.phong_id FROM dat_phong_doan dpd
                 WHERE dpd.dat_phong_id = dp.dat_phong_id AND ROWNUM = 1) AS phong_id
          FROM dat_phong dp
          JOIN khach_hang kh ON kh.khach_hang_id = dp.khach_hang_id
         WHERE {"dp.dat_phong_id = :val" if is_id else "UPPER(dp.ma_tra_cuu) = UPPER(:val)"}
        """
        with conn.cursor() as cur:
            cur.execute(sql, {"val": val_int if is_id else str(id_or_code).strip()})
            rows = fetch_cursor_as_dicts(cur)
            if not rows:
                return None
            return BookingRepository._map_booking_row(rows[0])

    @staticmethod
    def get_refund_preview(conn: oracledb.Connection, booking_id: int) -> Dict[str, Any]:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT dp.dat_phong_id, dp.ma_tra_cuu, dp.tu_luc, dp.tong_tien, dp.trang_thai,
                       pkg_thanh_toan.tinh_da_thanh_toan(dp.dat_phong_id) AS da_thanh_toan,
                       pkg_gia.so_phut(SYSTIMESTAMP, dp.tu_luc) / 60 AS so_gio_truoc_nhan,
                       pkg_cau_hinh.lay_so('GIO_HUY_MIEN_PHI') AS gio_mien_phi
                  FROM dat_phong dp
                 WHERE dp.dat_phong_id = :id
            """, {"id": booking_id})
            rows = fetch_cursor_as_dicts(cur)
            if not rows:
                raise BusinessException("BOOKING_NOT_FOUND", f"Không tìm thấy đơn đặt phòng ID {booking_id}")
            r = rows[0]

            try:
                expected_refund = float(cur.callfunc("PKG_DAT_PHONG.HOAN_DU_KIEN", oracledb.NUMBER, [booking_id]) or 0)
            except oracledb.DatabaseError as e:
                raise parse_oracle_error(e)

            paid_amount = float(r["da_thanh_toan"] or 0)
            hours_left = float(r["so_gio_truoc_nhan"] or 0)
            free_hours = float(r["gio_mien_phi"] or 24)
            is_eligible = hours_left >= free_hours and r["trang_thai"] == "CONFIRMED"

            if r["trang_thai"] != "CONFIRMED":
                reason = f"Đơn đang ở trạng thái {r['trang_thai']}, không áp dụng hoàn tiền tự động khi hủy."
            elif is_eligible:
                reason = f"Hủy trước {int(free_hours)} giờ so với thời điểm nhận phòng: hoàn 100% số tiền đã thanh toán ({paid_amount:,.0f} đ)."
            else:
                reason = f"Hủy dưới {int(free_hours)} giờ so với thời điểm nhận phòng ({hours_left:.1f} giờ còn lại): không được hoàn tiền theo chính sách (BR-24)."

            return {
                "booking_id": r["dat_phong_id"],
                "booking_code": r["ma_tra_cuu"],
                "checkin": r["tu_luc"],
                "paid_amount": paid_amount,
                "expected_refund": expected_refund,
                "reason": reason,
                "is_eligible": is_eligible
            }

    @staticmethod
    def cancel_booking(conn: oracledb.Connection, booking_id: int, reason: str) -> Dict[str, Any]:
        with conn.cursor() as cur:
            p_refund = cur.var(oracledb.NUMBER)
            try:
                cur.callproc("PKG_DAT_PHONG.HUY_DON", [booking_id, reason, p_refund])
            except oracledb.DatabaseError as e:
                raise parse_oracle_error(e)

            cur.execute("SELECT ma_tra_cuu, trang_thai FROM dat_phong WHERE dat_phong_id = :id", {"id": booking_id})
            row = cur.fetchone()
            b_code = row[0] if row else ""
            new_st = row[1] if row else "CANCELLED"
            refund_val = float(p_refund.getvalue() or 0)

            msg = "Hủy đơn thành công."
            if refund_val > 0:
                msg += f" Hệ thống đã tạo lệnh hoàn tiền {refund_val:,.0f} đ theo chính sách (BR-24)."

            return {
                "status": "success",
                "booking_code": b_code,
                "new_status": new_st,
                "refund_amount": refund_val,
                "message": msg
            }

    @staticmethod
    def mark_no_show(conn: oracledb.Connection, booking_id: int) -> Dict[str, Any]:
        with conn.cursor() as cur:
            try:
                cur.callproc("PKG_DAT_PHONG.NO_SHOW_THU_CONG", [booking_id])
            except oracledb.DatabaseError as e:
                raise parse_oracle_error(e)

            cur.execute("SELECT ma_tra_cuu, trang_thai FROM dat_phong WHERE dat_phong_id = :id", {"id": booking_id})
            row = cur.fetchone()
            b_code = row[0] if row else ""
            new_st = row[1] if row else "NO_SHOW"
            return {
                "status": "success",
                "booking_id": booking_id,
                "booking_code": b_code,
                "new_status": new_st,
                "message": "Đã chuyển đơn sang trạng thái NO_SHOW (khách không đến) thành công."
            }

    @staticmethod
    def resend_email(conn: oracledb.Connection, booking_id: int) -> Dict[str, Any]:
        with conn.cursor() as cur:
            cur.execute("SELECT ma_tra_cuu FROM dat_phong WHERE dat_phong_id = :id", {"id": booking_id})
            row = cur.fetchone()
            if not row:
                raise BusinessException("BOOKING_NOT_FOUND", f"Không tìm thấy đơn đặt phòng ID {booking_id}")
            b_code = row[0]
            try:
                cur.callproc("PKG_EMAIL.XEP", [booking_id, "XAC_NHAN"])
            except oracledb.DatabaseError as e:
                raise parse_oracle_error(e)

            return {
                "status": "success",
                "booking_id": booking_id,
                "booking_code": b_code,
                "message": "Đã xếp email xác nhận vào hàng đợi gửi thành công (FR-23)."
            }

    @staticmethod
    def reschedule_booking(
        conn: oracledb.Connection,
        booking_id: int,
        checkin: datetime,
        checkout: datetime,
        room_type: Optional[str] = None,
        room_id: Optional[int] = None
    ) -> Dict[str, Any]:
        with conn.cursor() as cur:
            # 1. Fetch current booking info
            cur.execute("""
                SELECT dp.dat_phong_id, dp.ma_tra_cuu, dp.tong_tien, dp.trang_thai,
                       (SELECT lp.loai_phong_id FROM dat_phong_doan dpd
                          JOIN phong p ON p.phong_id = dpd.phong_id
                          JOIN loai_phong lp ON lp.loai_phong_id = p.loai_phong_id
                         WHERE dpd.dat_phong_id = dp.dat_phong_id AND ROWNUM = 1) AS loai_phong_id,
                       (SELECT dpd.phong_id FROM dat_phong_doan dpd
                         WHERE dpd.dat_phong_id = dp.dat_phong_id AND ROWNUM = 1) AS phong_id
                  FROM dat_phong dp
                 WHERE dp.dat_phong_id = :id
            """, {"id": booking_id})
            row = cur.fetchone()
            if not row:
                raise BusinessException("BOOKING_NOT_FOUND", f"Không tìm thấy đơn đặt phòng ID {booking_id}")
            
            b_id, b_code, old_total, status, curr_type_id, curr_room_id = row
            old_total = float(old_total or 0)

            target_room_id = room_id
            target_type_id = curr_type_id
            if room_type:
                new_type_id = BookingRepository.get_room_type_id(conn, room_type)
                if new_type_id:
                    target_type_id = new_type_id

            # If user wants a new room type or specific room was not provided:
            if target_room_id is None:
                if room_type and (target_type_id != curr_type_id):
                    # Category changed
                    suggestions = BookingRepository.get_suggested_rooms(conn, target_type_id, checkin, checkout)
                    if not suggestions:
                        raise BusinessException("NO_AVAILABILITY", f"Hạng phòng {room_type} đã hết phòng trống trong khoảng thời gian này")
                    target_room_id = suggestions[0]["room_id"]
                else:
                    # Same category: check if current room is free during new timeframe
                    with conn.cursor() as chk_cur:
                        chk_cur.execute(
                            "SELECT pkg_kiem_tra_trung.dem_xung_dot(:room_id, :tu, :den) FROM dual",
                            {"room_id": curr_room_id, "tu": checkin, "den": checkout}
                        )
                        has_conflict = chk_cur.fetchone()[0] > 0
                    if has_conflict:
                        suggestions = BookingRepository.get_suggested_rooms(conn, target_type_id, checkin, checkout)
                        if not suggestions:
                            raise BusinessException("NO_AVAILABILITY", "Không còn phòng trống trong hạng này ở khung thời gian mới")
                        target_room_id = suggestions[0]["room_id"]
                    else:
                        target_room_id = curr_room_id

            p_diff = cur.var(oracledb.NUMBER)
            p_refund = cur.var(oracledb.NUMBER)

            try:
                cur.callproc(
                    "PKG_DAT_PHONG.DOI_LICH",
                    [booking_id, checkin, checkout, target_room_id, p_diff, p_refund]
                )
            except oracledb.DatabaseError as e:
                biz_exc = parse_oracle_error(e)
                if biz_exc.code in ("ROOM_CONFLICT", "EXTEND_CONFLICT"):
                    # Attach available rooms to response so guest can pick another room
                    suggestions = BookingRepository.get_suggested_rooms(conn, target_type_id, checkin, checkout)
                    biz_exc.data = {"suggested_rooms": suggestions}
                raise biz_exc

            # Query new total amount and status
            cur.execute("SELECT tong_tien, trang_thai FROM dat_phong WHERE dat_phong_id = :id", {"id": booking_id})
            new_r = cur.fetchone()
            new_total = float(new_r[0]) if new_r else old_total
            new_status = new_r[1] if new_r else status

            diff_val = float(p_diff.getvalue() or 0)
            refund_val = float(p_refund.getvalue() or 0)

            msg = "Đổi lịch đặt phòng thành công."
            if diff_val > 0:
                msg += f" Quý khách vui lòng thanh toán thêm chênh lệch: {diff_val:,.0f} đ."
            elif refund_val > 0:
                msg += f" Hệ thống đã tạo lệnh hoàn lại phần tiền thừa: {refund_val:,.0f} đ."

            return {
                "status": "success",
                "booking_code": b_code,
                "new_status": new_status,
                "old_total": old_total,
                "new_total": new_total,
                "difference": diff_val,
                "refund_amount": refund_val,
                "message": msg
            }

    @staticmethod
    def search_bookings(
        conn: oracledb.Connection,
        q: Optional[str] = None,
        status: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        where_clauses = ["1=1"]
        binds: Dict[str, Any] = {}

        if q:
            kw = f"%{q.strip().upper()}%"
            binds["kw"] = kw
            where_clauses.append("""(
                UPPER(dp.ma_tra_cuu) LIKE :kw
                OR UPPER(kh.ho_ten) LIKE :kw
                OR kh.sdt LIKE :kw
                OR UPPER(kh.email) LIKE :kw
                OR EXISTS (
                    SELECT 1 FROM dat_phong_doan dpd
                    JOIN phong p ON p.phong_id = dpd.phong_id
                    WHERE dpd.dat_phong_id = dp.dat_phong_id AND UPPER(p.ma_phong) LIKE :kw
                )
            )""")

        if status and status.upper() != "ALL":
            binds["status"] = status.upper()
            where_clauses.append("dp.trang_thai = :status")

        if from_date:
            binds["from_date"] = from_date
            where_clauses.append("dp.tu_luc >= :from_date")

        if to_date:
            binds["to_date"] = to_date
            where_clauses.append("dp.den_luc <= :to_date")

        where_sql = " AND ".join(where_clauses)

        with conn.cursor() as cur:
            count_sql = f"""
                SELECT COUNT(*)
                  FROM dat_phong dp
                  JOIN khach_hang kh ON kh.khach_hang_id = dp.khach_hang_id
                 WHERE {where_sql}
            """
            cur.execute(count_sql, binds)
            total = cur.fetchone()[0]

            offset = (page - 1) * page_size
            binds["offset"] = offset
            binds["limit"] = page_size

            data_sql = f"""
                SELECT dp.dat_phong_id, dp.ma_tra_cuu, dp.trang_thai, dp.loai_dat, dp.kenh_dat,
                       dp.tu_luc, dp.den_luc, dp.so_khach, dp.tong_tien, dp.ngay_tao,
                       kh.ho_ten, kh.sdt, kh.email,
                       (SELECT p.ma_phong FROM dat_phong_doan dpd
                          JOIN phong p ON p.phong_id = dpd.phong_id
                         WHERE dpd.dat_phong_id = dp.dat_phong_id AND ROWNUM = 1) AS ma_phong,
                       (SELECT lp.ma_hang FROM dat_phong_doan dpd
                          JOIN phong p ON p.phong_id = dpd.phong_id
                          JOIN loai_phong lp ON lp.loai_phong_id = p.loai_phong_id
                         WHERE dpd.dat_phong_id = dp.dat_phong_id AND ROWNUM = 1) AS ma_hang,
                       pkg_thanh_toan.tinh_da_thanh_toan(dp.dat_phong_id) AS da_thanh_toan
                  FROM dat_phong dp
                  JOIN khach_hang kh ON kh.khach_hang_id = dp.khach_hang_id
                 WHERE {where_sql}
                 ORDER BY dp.dat_phong_id DESC
                OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY
            """
            cur.execute(data_sql, binds)
            rows = fetch_cursor_as_dicts(cur)

            items = []
            for r in rows:
                items.append({
                    "id": r["dat_phong_id"],
                    "bookingCode": r["ma_tra_cuu"],
                    "status": r["trang_thai"],
                    "bookingType": r["loai_dat"],
                    "channel": r["kenh_dat"],
                    "checkin": r["tu_luc"],
                    "checkout": r["den_luc"],
                    "guests": r["so_khach"],
                    "totalAmount": float(r["tong_tien"] or 0),
                    "paidAmount": float(r["da_thanh_toan"] or 0),
                    "createdAt": r["ngay_tao"],
                    "customerName": r["ho_ten"],
                    "customerPhone": r["sdt"],
                    "customerEmail": r["email"],
                    "roomNumber": r["ma_phong"],
                    "roomType": r["ma_hang"]
                })

            total_pages = (total + page_size - 1) // page_size if total > 0 else 1

            return {
                "items": items,
                "total": total,
                "page": page,
                "pageSize": page_size,
                "totalPages": total_pages
            }

    @staticmethod
    def get_staff_booking_detail(conn: oracledb.Connection, id_or_code: Any) -> Optional[Dict[str, Any]]:
        try:
            val_int = int(id_or_code)
            is_id = True
        except (ValueError, TypeError):
            is_id = False

        sql = f"""
        SELECT dp.dat_phong_id, dp.ma_tra_cuu, dp.trang_thai, dp.loai_dat, dp.kenh_dat,
               dp.tu_luc, dp.den_luc, dp.nhan_thuc_te, dp.tra_thuc_te, dp.han_giu_cho,
               dp.so_khach, dp.tien_phong, dp.thue_suat, dp.tien_vat, dp.tong_tien,
               dp.ly_do_huy,
               pkg_thanh_toan.tinh_da_thanh_toan(dp.dat_phong_id) AS da_thanh_toan,
               kh.khach_hang_id, kh.ho_ten, kh.sdt, kh.email, kh.quoc_tich
          FROM dat_phong dp
          JOIN khach_hang kh ON kh.khach_hang_id = dp.khach_hang_id
         WHERE {"dp.dat_phong_id = :val" if is_id else "UPPER(dp.ma_tra_cuu) = UPPER(:val)"}
        """
        with conn.cursor() as cur:
            cur.execute(sql, {"val": val_int if is_id else str(id_or_code).strip()})
            rows = fetch_cursor_as_dicts(cur)
            if not rows:
                return None
            dp = rows[0]
            dp_id = dp["dat_phong_id"]
            tot = float(dp["tong_tien"] or 0)
            paid = float(dp["da_thanh_toan"] or 0)
            rem = max(0.0, tot - paid)

            # Segments
            cur.execute("""
                SELECT dpd.doan_id, dpd.phong_id, p.ma_phong, p.so_tang, lp.ma_hang,
                       dpd.tu_luc, dpd.den_luc
                  FROM dat_phong_doan dpd
                  JOIN phong p ON p.phong_id = dpd.phong_id
                  JOIN loai_phong lp ON lp.loai_phong_id = p.loai_phong_id
                 WHERE dpd.dat_phong_id = :id
                 ORDER BY dpd.tu_luc
            """, {"id": dp_id})
            seg_rows = fetch_cursor_as_dicts(cur)
            segments = [
                {
                    "segmentId": s["doan_id"],
                    "roomId": s["phong_id"],
                    "roomNumber": s["ma_phong"],
                    "floor": s["so_tang"],
                    "roomType": s["ma_hang"],
                    "from": s["tu_luc"],
                    "to": s["den_luc"]
                }
                for s in seg_rows
            ]

            # Transactions
            cur.execute("""
                SELECT g.giao_dich_id, g.kenh, g.phuong_thuc, g.so_tien, g.trang_thai,
                       g.ma_tham_chieu_cong, g.ngay_giao_dich
                  FROM giao_dich_thanh_toan g
                 WHERE g.dat_phong_id = :id
                 ORDER BY g.giao_dich_id DESC
            """, {"id": dp_id})
            tx_rows = fetch_cursor_as_dicts(cur)
            transactions = [
                {
                    "transactionId": t["giao_dich_id"],
                    "channel": t["kenh"],
                    "method": t["phuong_thuc"],
                    "amount": float(t["so_tien"] or 0),
                    "status": t["trang_thai"],
                    "referenceCode": t["ma_tham_chieu_cong"],
                    "transactionDate": t["ngay_giao_dich"]
                }
                for t in tx_rows
            ]

            # Refunds
            cur.execute("""
                SELECT h.hoan_tien_id, h.giao_dich_id, h.so_tien, h.ly_do, h.trang_thai, h.ngay_tao
                  FROM hoan_tien h
                  JOIN giao_dich_thanh_toan g ON g.giao_dich_id = h.giao_dich_id
                 WHERE g.dat_phong_id = :id
                 ORDER BY h.hoan_tien_id DESC
            """, {"id": dp_id})
            rf_rows = fetch_cursor_as_dicts(cur)
            refunds = [
                {
                    "refundId": r["hoan_tien_id"],
                    "transactionId": r["giao_dich_id"],
                    "amount": float(r["so_tien"] or 0),
                    "reason": r["ly_do"],
                    "status": r["trang_thai"],
                    "createdAt": r["ngay_tao"]
                }
                for r in rf_rows
            ]

            # Invoices
            cur.execute("""
                SELECT hd.hoa_don_id, hd.so_hoa_don, hd.tong_tien, hd.ngay_lap, u.ho_ten AS nguoi_lap
                  FROM hoa_don hd
                  LEFT JOIN nguoi_dung u ON u.nguoi_dung_id = hd.nguoi_lap_id
                 WHERE hd.dat_phong_id = :id
                 ORDER BY hd.hoa_don_id DESC
                 FETCH FIRST 1 ROW ONLY
            """, {"id": dp_id})
            inv_rows = fetch_cursor_as_dicts(cur)
            invoice = None
            if inv_rows:
                inv = inv_rows[0]
                invoice = {
                    "invoiceId": inv["hoa_don_id"],
                    "invoiceNumber": inv["so_hoa_don"],
                    "totalAmount": float(inv["tong_tien"] or 0),
                    "issuedAt": inv["ngay_lap"],
                    "createdBy": inv["nguoi_lap"]
                }

            # Email queue logs (F14, FR-23, FR-53)
            cur.execute("""
                SELECT email_id, loai_email, ngon_ngu, trang_thai, so_lan_thu, lan_gui_cuoi, loi, ngay_tao
                  FROM hang_doi_email
                 WHERE dat_phong_id = :id
                 ORDER BY email_id DESC
            """, {"id": dp_id})
            email_rows = fetch_cursor_as_dicts(cur)
            emails = [
                {
                    "emailId": e["email_id"],
                    "emailType": e["loai_email"],
                    "language": e["ngon_ngu"],
                    "status": e["trang_thai"],
                    "attempts": int(e["so_lan_thu"] or 0),
                    "lastSentAt": e["lan_gui_cuoi"],
                    "error": e["loi"],
                    "createdAt": e["ngay_tao"]
                }
                for e in email_rows
            ]

            # Guest identification document (NFR-13)
            doc_id = None
            id_type = None
            id_number_masked = None
            photo_url = None
            cur.execute("""
                SELECT giay_to_id, loai_giay_to, so_giay_to, anh_url
                  FROM giay_to_khach
                 WHERE khach_hang_id = :kh_id
                 ORDER BY giay_to_id DESC
                 FETCH FIRST 1 ROW ONLY
            """, {"kh_id": dp["khach_hang_id"]})
            doc_row = cur.fetchone()
            if doc_row:
                doc_id, id_type, enc_so_giay_to, photo_url = doc_row
                try:
                    decrypted = decrypt_id_document(enc_so_giay_to)
                    id_number_masked = mask_id_document(decrypted)
                    # Audit logging for decryption of guest ID document (NFR-13)
                    cur.callproc(
                        f"{settings.ORA_SCHEMA}.PKG_NHAT_KY.GHI",
                        ["GIAY_TO_KHACH", str(doc_id), "XEM_GIAY_TO", None, None]
                    )
                    conn.commit()
                except Exception:
                    logger.warning("Could not decrypt ID document for customer %s", dp["khach_hang_id"])

            # State-machine actions (SRS 12.2)
            st = dp["trang_thai"]
            actions = {
                "can_cancel": st in ("HOLD", "CONFIRMED"),
                "can_reschedule": st == "CONFIRMED",
                "can_check_in": st == "CONFIRMED",
                "can_extend": st == "CHECKED_IN",
                "can_change_room": st == "CHECKED_IN",
                "can_check_out": st == "CHECKED_IN",
                "can_pay": st in ("HOLD", "CONFIRMED", "CHECKED_IN") and rem > 0
            }

            room_type = segments[0]["roomType"] if segments else None
            hold_exp = dp["han_giu_cho"]
            if hold_exp is not None and hasattr(hold_exp, "tzinfo") and hold_exp.tzinfo is None:
                hold_exp = hold_exp.replace(tzinfo=timezone.utc)

            return {
                "id": dp_id,
                "booking_code": dp["ma_tra_cuu"],
                "status": st,
                "room_type": room_type,
                "booking_type": dp["loai_dat"],
                "channel": dp["kenh_dat"],
                "checkin": dp["tu_luc"],
                "checkout": dp["den_luc"],
                "actual_checkin": dp["nhan_thuc_te"],
                "actual_checkout": dp["tra_thuc_te"],
                "guests": dp["so_khach"],
                "hold_expires_at": hold_exp,
                "room_amount": float(dp["tien_phong"] or 0),
                "vat_rate": float(dp["thue_suat"] or 0),
                "vat_amount": float(dp["tien_vat"] or 0),
                "total_amount": tot,
                "paid_amount": paid,
                "remaining_amount": rem,
                "cancellation_reason": dp["ly_do_huy"],
                "customer": {
                    "fullName": dp["ho_ten"],
                    "phone": dp["sdt"],
                    "email": dp["email"],
                    "nationality": dp["quoc_tich"] or "VN",
                    "identificationId": id_number_masked,
                    "idType": id_type,
                    "photoUrl": photo_url
                },
                "segments": segments,
                "transactions": transactions,
                "refunds": refunds,
                "invoice": invoice,
                "emails": emails,
                "actions": actions
            }

    @staticmethod
    def check_in(
        conn: oracledb.Connection,
        booking_id: int,
        id_type: str,
        id_number: str,
        nationality: str,
        photo_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes check-in via PKG_DAT_PHONG.CHECK_IN (F08, BR-30 to BR-32, AC-21).
        Encrypts guest identification number before storage (NFR-13).
        """
        encrypted_id = encrypt_id_document(id_number)
        with conn.cursor() as cur:
            p_phong_id = cur.var(oracledb.NUMBER)
            try:
                cur.callproc(
                    f"{settings.ORA_SCHEMA}.PKG_DAT_PHONG.CHECK_IN",
                    [
                        booking_id,
                        id_type,
                        encrypted_id,
                        nationality,
                        photo_url,
                        p_phong_id
                    ]
                )
                assigned_room_id = int(p_phong_id.getvalue())
                conn.commit()
            except oracledb.DatabaseError as e:
                conn.rollback()
                raise parse_oracle_error(e)

            # Retrieve updated booking status and assigned room details
            cur.execute("""
                SELECT dp.ma_tra_cuu, dp.trang_thai, dp.nhan_thuc_te, p.ma_phong
                  FROM dat_phong dp
                  JOIN phong p ON p.phong_id = :phong_id
                 WHERE dp.dat_phong_id = :dp_id
            """, {"phong_id": assigned_room_id, "dp_id": booking_id})
            row = cur.fetchone()
            if not row:
                raise BusinessException(code="BOOKING_NOT_FOUND", detail="Đơn đặt phòng không tồn tại")

            return {
                "booking_id": booking_id,
                "booking_code": row[0],
                "room_id": assigned_room_id,
                "room_number": row[3],
                "status": row[1],
                "checked_in_at": row[2],
                "message": f"Nhận phòng thành công (Phòng {row[3]})"
            }

    @staticmethod
    def preview_extend(conn: oracledb.Connection, booking_id: int, units: int) -> Dict[str, Any]:
        """
        Calculates preview price and conflict status for extending a CHECKED_IN stay
        using Oracle pricing functions (BR-33, BR-34, AC-12) without mutating DB.
        """
        if units < 1:
            raise BusinessException(code="VALIDATION_ERROR", detail="Số đơn vị gia hạn phải lớn hơn 0")

        with conn.cursor() as cur:
            cur.execute("""
                SELECT dp.ma_tra_cuu, dp.loai_dat, dp.trang_thai, dp.tu_luc, dp.den_luc,
                       dp.tien_phong, dp.tien_vat, dp.tong_tien,
                       dp.don_gia_ap_dung, dp.don_gia_ngay_ap_dung, dp.thue_suat,
                       d.doan_id, d.phong_id, d.tu_luc AS doan_tu_luc, p.loai_phong_id
                  FROM dat_phong dp
                  JOIN (SELECT dat_phong_id, doan_id, phong_id, tu_luc
                          FROM dat_phong_doan
                         WHERE dat_phong_id = :id
                         ORDER BY doan_id DESC
                         FETCH FIRST 1 ROW ONLY) d ON d.dat_phong_id = dp.dat_phong_id
                  JOIN phong p ON p.phong_id = d.phong_id
                 WHERE dp.dat_phong_id = :id
            """, {"id": booking_id})
            rows = fetch_cursor_as_dicts(cur)
            if not rows:
                raise BusinessException(code="BOOKING_NOT_FOUND", detail="Đơn đặt phòng không tồn tại")

            dp = rows[0]
            if dp["trang_thai"] != "CHECKED_IN":
                raise BusinessException(code="BOOKING_STATE_INVALID", detail=dp["trang_thai"])

            loai_dat = dp["loai_dat"]
            if loai_dat == "NGAY":
                cur.execute("""
                    SELECT dp.den_luc + NUMTODSINTERVAL(:units, 'DAY') AS den_moi,
                           dp.tien_phong + (:units * dp.don_gia_ngay_ap_dung) AS tien_moi,
                           pkg_gia.tinh_vat(dp.tien_phong + (:units * dp.don_gia_ngay_ap_dung), dp.thue_suat) AS vat_moi,
                           0 AS switched_daily,
                           1 AS valid_hours,
                           pkg_kiem_tra_trung.dem_xung_dot(:phong_id, :doan_tu, dp.den_luc + NUMTODSINTERVAL(:units, 'DAY'), :doan_id) AS conflicts
                      FROM dat_phong dp
                     WHERE dp.dat_phong_id = :id
                """, {
                    "units": units,
                    "phong_id": dp["phong_id"],
                    "doan_tu": dp["doan_tu_luc"],
                    "doan_id": dp["doan_id"],
                    "id": booking_id
                })
            else:
                cur.execute("""
                    SELECT v.den_moi,
                           pkg_gia.tien_theo_gio(v.gio_moi, dp.don_gia_ap_dung, dp.don_gia_ngay_ap_dung) AS tien_moi,
                           pkg_gia.tinh_vat(pkg_gia.tien_theo_gio(v.gio_moi, dp.don_gia_ap_dung, dp.don_gia_ngay_ap_dung), dp.thue_suat) AS vat_moi,
                           CASE WHEN v.gio_moi > pkg_cau_hinh.lay_so('NGUONG_GIO_TINH_NGAY') THEN 1 ELSE 0 END AS switched_daily,
                           CASE WHEN v.gio_moi <= pkg_cau_hinh.lay_so('SO_GIO_TOI_DA_DON_GIO') THEN 1 ELSE 0 END AS valid_hours,
                           pkg_kiem_tra_trung.dem_xung_dot(:phong_id, :doan_tu, v.den_moi, :doan_id) AS conflicts
                      FROM dat_phong dp
                      CROSS JOIN (
                          SELECT (SELECT den_luc + NUMTODSINTERVAL(:units, 'HOUR') FROM dat_phong WHERE dat_phong_id = :id) AS den_moi,
                                 pkg_gia.so_phut(
                                     (SELECT tu_luc FROM dat_phong WHERE dat_phong_id = :id),
                                     (SELECT den_luc + NUMTODSINTERVAL(:units, 'HOUR') FROM dat_phong WHERE dat_phong_id = :id)
                                 ) / 60 AS gio_moi
                            FROM dual
                      ) v
                     WHERE dp.dat_phong_id = :id
                """, {
                    "units": units,
                    "phong_id": dp["phong_id"],
                    "doan_tu": dp["doan_tu_luc"],
                    "doan_id": dp["doan_id"],
                    "id": booking_id
                })

            calc = fetch_cursor_as_dicts(cur)[0]
            if calc["valid_hours"] == 0:
                raise BusinessException(code="VALIDATION_ERROR", detail="Vượt quá số giờ tối đa của đơn theo giờ")

            new_checkout = calc["den_moi"]
            cur_room = float(dp["tien_phong"] or 0)
            new_room = float(calc["tien_moi"] or 0)
            cur_vat = float(dp["tien_vat"] or 0)
            new_vat = float(calc["vat_moi"] or 0)
            cur_total = float(dp["tong_tien"] or 0)
            new_total = new_room + new_vat
            has_conflict = int(calc["conflicts"] or 0) > 0

            suggestions = []
            if has_conflict:
                suggestions = BookingRepository.get_suggested_rooms(
                    conn, dp["loai_phong_id"], dp["den_luc"], new_checkout
                )

            return {
                "booking_id": booking_id,
                "booking_code": dp["ma_tra_cuu"],
                "booking_type": loai_dat,
                "units": units,
                "current_checkout": dp["den_luc"],
                "new_checkout": new_checkout,
                "current_room_amount": cur_room,
                "new_room_amount": new_room,
                "added_room_amount": new_room - cur_room,
                "current_vat_amount": cur_vat,
                "new_vat_amount": new_vat,
                "added_vat_amount": new_vat - cur_vat,
                "current_total_amount": cur_total,
                "new_total_amount": new_total,
                "added_amount": new_total - cur_total,
                "switched_to_daily_rate": bool(calc["switched_daily"]),
                "has_conflict": has_conflict,
                "suggested_rooms": suggestions
            }

    @staticmethod
    def extend_booking(conn: oracledb.Connection, booking_id: int, units: int) -> Dict[str, Any]:
        """
        Extends a CHECKED_IN booking via PKG_DAT_PHONG.GIA_HAN (F09, FR-17, BR-33, BR-34, AC-12).
        On EXTEND_CONFLICT, attaches suggested rooms from PKG_DAT_PHONG.GOI_Y_PHONG for the extended period.
        """
        with conn.cursor() as cur:
            cur.execute("""
                SELECT dp.loai_dat, dp.den_luc, p.loai_phong_id
                  FROM dat_phong dp
                  JOIN (SELECT dat_phong_id, phong_id
                          FROM dat_phong_doan
                         WHERE dat_phong_id = :id
                         ORDER BY doan_id DESC
                         FETCH FIRST 1 ROW ONLY) d ON d.dat_phong_id = dp.dat_phong_id
                  JOIN phong p ON p.phong_id = d.phong_id
                 WHERE dp.dat_phong_id = :id
            """, {"id": booking_id})
            meta_rows = fetch_cursor_as_dicts(cur)
            if not meta_rows:
                raise BusinessException(code="BOOKING_NOT_FOUND", detail="Đơn đặt phòng không tồn tại")
            meta = meta_rows[0]

            p_tien_them = cur.var(oracledb.NUMBER)
            try:
                cur.callproc(
                    f"{settings.ORA_SCHEMA}.PKG_DAT_PHONG.GIA_HAN",
                    [booking_id, units, p_tien_them]
                )
                added_amount = float(p_tien_them.getvalue() or 0)
                conn.commit()
            except oracledb.DatabaseError as e:
                conn.rollback()
                biz_exc = parse_oracle_error(e)
                if biz_exc.code == "EXTEND_CONFLICT":
                    new_checkout = (
                        meta["den_luc"] + timedelta(days=units)
                        if meta["loai_dat"] == "NGAY"
                        else meta["den_luc"] + timedelta(hours=units)
                    )
                    suggestions = BookingRepository.get_suggested_rooms(
                        conn, meta["loai_phong_id"], meta["den_luc"], new_checkout
                    )
                    biz_exc.data = {
                        "suggested_rooms": suggestions,
                        "extend_from": meta["den_luc"].isoformat(),
                        "extend_to": new_checkout.isoformat()
                    }
                raise biz_exc

            cur.execute("""
                SELECT dp.ma_tra_cuu, dp.loai_dat, dp.den_luc, dp.tien_phong, dp.tien_vat, dp.tong_tien,
                       pkg_thanh_toan.tinh_da_thanh_toan(dp.dat_phong_id) AS da_thanh_toan
                  FROM dat_phong dp
                 WHERE dp.dat_phong_id = :id
            """, {"id": booking_id})
            dp = fetch_cursor_as_dicts(cur)[0]
            tot = float(dp["tong_tien"] or 0)
            paid = float(dp["da_thanh_toan"] or 0)

            unit_label = "đêm" if dp["loai_dat"] == "NGAY" else "giờ"
            return {
                "booking_id": booking_id,
                "booking_code": dp["ma_tra_cuu"],
                "booking_type": dp["loai_dat"],
                "units": units,
                "new_checkout": dp["den_luc"],
                "added_amount": added_amount,
                "room_amount": float(dp["tien_phong"] or 0),
                "vat_amount": float(dp["tien_vat"] or 0),
                "total_amount": tot,
                "paid_amount": paid,
                "remaining_amount": max(0.0, tot - paid),
                "message": f"Gia hạn thêm {units} {unit_label} thành công"
            }
