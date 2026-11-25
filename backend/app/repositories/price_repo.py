from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
import oracledb

from app.db import fetch_cursor_as_dicts
from app.errors import BusinessException, parse_oracle_error

class PriceRepository:
    @staticmethod
    def get_prices(
        conn: oracledb.Connection,
        ma_hang: Optional[str] = None,
        loai_gia: Optional[str] = None,
        at: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves price rows with VAT calculation.
        If 'at' is provided, filters for prices active at date 'at'.
        Otherwise returns all active price rows and upcoming ones.
        """
        conditions = []
        params = {}

        if ma_hang:
            conditions.append("lp.ma_hang = :ma_hang")
            params["ma_hang"] = ma_hang.upper()
        if loai_gia:
            conditions.append("bg.loai_gia = :loai_gia")
            params["loai_gia"] = loai_gia.upper()

        if at:
            conditions.append("bg.hieu_luc_tu <= TO_DATE(:at_date, 'YYYY-MM-DD')")
            conditions.append("(bg.hieu_luc_den IS NULL OR bg.hieu_luc_den >= TO_DATE(:at_date, 'YYYY-MM-DD'))")
            params["at_date"] = at

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        sql = f"""
        SELECT bg.bang_gia_id,
               bg.loai_phong_id,
               lp.ma_hang,
               COALESCE(lpd.ten, lp.ma_hang) AS ten_hang,
               bg.loai_gia,
               bg.don_gia,
               pkg_gia.thue_suat(bg.hieu_luc_tu) AS thue_suat,
               ROUND(bg.don_gia * (1 + pkg_gia.thue_suat(bg.hieu_luc_tu))) AS don_gia_vat,
               TO_CHAR(bg.hieu_luc_tu, 'YYYY-MM-DD') AS hieu_luc_tu,
               TO_CHAR(bg.hieu_luc_den, 'YYYY-MM-DD') AS hieu_luc_den,
               CASE 
                 WHEN bg.hieu_luc_tu <= TRUNC(SYSDATE) AND (bg.hieu_luc_den IS NULL OR bg.hieu_luc_den >= TRUNC(SYSDATE)) THEN 1
                 ELSE 0
               END AS is_active,
               TO_CHAR(bg.ngay_tao, 'YYYY-MM-DD"T"HH24:MI:SS"+07:00"') AS ngay_tao
          FROM bang_gia bg
          JOIN loai_phong lp ON bg.loai_phong_id = lp.loai_phong_id
          LEFT JOIN loai_phong_dich lpd ON lp.loai_phong_id = lpd.loai_phong_id AND lpd.ngon_ngu = 'vi'
          {where_clause}
         ORDER BY lp.loai_phong_id, bg.loai_gia, bg.hieu_luc_tu DESC
        """

        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = fetch_cursor_as_dicts(cur)
            return [
                {
                    "bangGiaId": r["bang_gia_id"],
                    "loaiPhongId": r["loai_phong_id"],
                    "maHang": r["ma_hang"],
                    "tenHang": r["ten_hang"],
                    "loaiGia": r["loai_gia"],
                    "donGia": float(r["don_gia"]),
                    "thueSuat": float(r["thue_suat"]),
                    "donGiaVat": float(r["don_gia_vat"]),
                    "hieuLucTu": r["hieu_luc_tu"],
                    "hieuLucDen": r["hieu_luc_den"],
                    "isActive": bool(r["is_active"]),
                    "ngayTao": r["ngay_tao"]
                }
                for r in rows
            ]

    @staticmethod
    def get_price_history(conn: oracledb.Connection, ma_hang: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns historical price rows."""
        return PriceRepository.get_prices(conn, ma_hang=ma_hang)

    @staticmethod
    def validate_price_rule(
        conn: oracledb.Connection,
        ma_hang: str,
        loai_gia: str,
        don_gia: float,
        hieu_luc_tu: date
    ) -> Dict[str, Any]:
        """
        Validates the 5x hourly price constraint prior to submitting.
        """
        with conn.cursor() as cur:
            # 1. Check room type
            cur.execute(
                "SELECT loai_phong_id, cho_thue_gio FROM loai_phong WHERE ma_hang = :ma",
                {"ma": ma_hang.upper()}
            )
            row = cur.fetchone()
            if not row:
                raise BusinessException("NOT_FOUND", f"Không tìm thấy hạng phòng {ma_hang}")

            lp_id, cho_thue_gio = row[0], bool(row[1])

            if loai_gia.upper() == "GIO" and not cho_thue_gio:
                return {
                    "valid": False,
                    "is_hourly_allowed": False,
                    "message": "Hạng phòng này không hỗ trợ thuê theo giờ (HOURLY_NOT_ALLOWED)."
                }

            if not cho_thue_gio:
                return {
                    "valid": True,
                    "is_hourly_allowed": False,
                    "message": "Hạng phòng chỉ thuê theo ngày, không áp dụng quy tắc giá giờ."
                }

            # Threshold for calculation (default 5 from NGUONG_GIO_TINH_NGAY)
            cur.execute("SELECT pkg_cau_hinh.lay_so('NGUONG_GIO_TINH_NGAY') FROM dual")
            nguong_row = cur.fetchone()
            nguong = float(nguong_row[0]) if nguong_row and nguong_row[0] else 5.0

            if loai_gia.upper() == "GIO":
                # Find daily price active at hieu_luc_tu
                cur.execute(
                    """
                    SELECT don_gia FROM bang_gia
                     WHERE loai_phong_id = :lp_id AND loai_gia = 'NGAY'
                       AND hieu_luc_tu <= :tu
                       AND (hieu_luc_den IS NULL OR hieu_luc_den >= :tu)
                       AND ROWNUM = 1
                    """,
                    {"lp_id": lp_id, "tu": hieu_luc_tu}
                )
                daily_row = cur.fetchone()
                gia_ngay = float(daily_row[0]) if daily_row else None
                gia_gio_x5 = don_gia * nguong

                if gia_ngay is not None and gia_gio_x5 > gia_ngay:
                    return {
                        "valid": False,
                        "is_hourly_allowed": True,
                        "gia_gio": don_gia,
                        "gia_gio_x5": gia_gio_x5,
                        "gia_ngay": gia_ngay,
                        "message": f"Vi phạm quy tắc: 5 lần giá giờ ({gia_gio_x5:,.0f} đ) vượt quá giá ngày ({gia_ngay:,.0f} đ)."
                    }

                return {
                    "valid": True,
                    "is_hourly_allowed": True,
                    "gia_gio": don_gia,
                    "gia_gio_x5": gia_gio_x5,
                    "gia_ngay": gia_ngay,
                    "message": f"Hợp lệ: 5 lần giá giờ ({gia_gio_x5:,.0f} đ) ≤ giá ngày ({gia_ngay:,.0f} đ)."
                }

            else:  # loai_gia == "NGAY"
                # Find hourly price active at hieu_luc_tu
                cur.execute(
                    """
                    SELECT don_gia FROM bang_gia
                     WHERE loai_phong_id = :lp_id AND loai_gia = 'GIO'
                       AND hieu_luc_tu <= :tu
                       AND (hieu_luc_den IS NULL OR hieu_luc_den >= :tu)
                       AND ROWNUM = 1
                    """,
                    {"lp_id": lp_id, "tu": hieu_luc_tu}
                )
                hourly_row = cur.fetchone()
                gia_gio = float(hourly_row[0]) if hourly_row else None
                gia_gio_x5 = gia_gio * nguong if gia_gio is not None else None

                if gia_gio_x5 is not None and gia_gio_x5 > don_gia:
                    return {
                        "valid": False,
                        "is_hourly_allowed": True,
                        "gia_gio": gia_gio,
                        "gia_gio_x5": gia_gio_x5,
                        "gia_ngay": don_gia,
                        "message": f"Vi phạm quy tắc: 5 lần giá giờ hiện tại ({gia_gio_x5:,.0f} đ) vượt quá giá ngày mới ({don_gia:,.0f} đ)."
                    }

                return {
                    "valid": True,
                    "is_hourly_allowed": True,
                    "gia_gio": gia_gio,
                    "gia_gio_x5": gia_gio_x5,
                    "gia_ngay": don_gia,
                    "message": f"Hợp lệ: 5 lần giá giờ ({gia_gio_x5:,.0f} đ) ≤ giá ngày mới ({don_gia:,.0f} đ)." if gia_gio_x5 is not None else "Hợp lệ."
                }

    @staticmethod
    def doi_gia(
        conn: oracledb.Connection,
        ma_hang: str,
        loai_gia: str,
        don_gia: float,
        hieu_luc_tu: date,
        ly_do: str,
        user_id: int,
        user_role: str,
        ip: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Implements business logic for F16.3 / AC-04:
        1. Validates input (positive, multiple of 1,000, not in past, reason provided).
        2. Validates hourly compatibility and 5x rule.
        3. Checks for overlapping future rows.
        4. Sets audit context via pkg_ngu_canh.
        5. Closes current row (hieu_luc_den = hieu_luc_tu - 1 day) and inserts new active row.
        """
        ma_hang = ma_hang.upper().strip()
        loai_gia = loai_gia.upper().strip()
        ly_do = ly_do.strip() if ly_do else ""

        # Step 1: Input Validations
        if not ly_do:
            raise BusinessException("VALIDATION_ERROR", "Vui lòng nhập lý do điều chỉnh giá")

        if loai_gia not in ("NGAY", "GIO"):
            raise BusinessException("VALIDATION_ERROR", "Loại giá phải là 'NGAY' hoặc 'GIO'")

        if don_gia <= 0:
            raise BusinessException("VALIDATION_ERROR", "Đơn giá phải lớn hơn 0")

        if don_gia % 1000 != 0:
            raise BusinessException("VALIDATION_ERROR", "Đơn giá phải là bội số của 1.000 VND")

        today = date.today()
        if hieu_luc_tu < today:
            raise BusinessException("VALIDATION_ERROR", "Ngày hiệu lực không được ở quá khứ")

        try:
            with conn.cursor() as cur:
                # Resolve room type
                cur.execute(
                    "SELECT loai_phong_id, cho_thue_gio FROM loai_phong WHERE ma_hang = :ma",
                    {"ma": ma_hang}
                )
                rt_row = cur.fetchone()
                if not rt_row:
                    raise BusinessException("NOT_FOUND", f"Không tìm thấy hạng phòng {ma_hang}")

                lp_id, cho_thue_gio = rt_row[0], bool(rt_row[1])

                if loai_gia == "GIO" and not cho_thue_gio:
                    raise BusinessException(
                        "HOURLY_NOT_ALLOWED",
                        f"Hạng phòng {ma_hang} không áp dụng hình thức thuê theo giờ"
                    )

                # Check future overlap
                cur.execute(
                    """
                    SELECT bang_gia_id, TO_CHAR(hieu_luc_tu, 'YYYY-MM-DD')
                      FROM bang_gia
                     WHERE loai_phong_id = :lp_id AND loai_gia = :lg
                       AND hieu_luc_tu > :tu
                    """,
                    {"lp_id": lp_id, "lg": loai_gia, "tu": hieu_luc_tu}
                )
                future_row = cur.fetchone()
                if future_row:
                    raise BusinessException(
                        "PRICE_OVERLAP",
                        f"Đã có bảng giá hiệu lực từ ngày {future_row[1]}. Không thể chồng chéo thời gian."
                    )

                # Pre-check 5x rule
                rule_check = PriceRepository.validate_price_rule(
                    conn, ma_hang, loai_gia, don_gia, hieu_luc_tu
                )
                if not rule_check["valid"]:
                    raise BusinessException(
                        "PRICE_RULE_VIOLATION",
                        rule_check.get("message", "Vi phạm quy tắc 5 lần giá giờ vượt giá ngày")
                    )

                # Step 2: Set audit context
                cur.execute(
                    """
                    BEGIN
                        pkg_ngu_canh.dat(
                            p_nguoi_id => :uid,
                            p_vai_tro  => :role,
                            p_kenh     => 'WEB',
                            p_ip       => :ip,
                            p_ly_do    => :ly_do
                        );
                    END;
                    """,
                    {
                        "uid": user_id,
                        "role": user_role,
                        "ip": ip or "127.0.0.1",
                        "ly_do": ly_do
                    }
                )

                # Step 3: Find active row at hieu_luc_tu
                cur.execute(
                    """
                    SELECT bang_gia_id, hieu_luc_tu, hieu_luc_den
                      FROM bang_gia
                     WHERE loai_phong_id = :lp_id AND loai_gia = :lg
                       AND hieu_luc_tu <= :tu
                       AND (hieu_luc_den IS NULL OR hieu_luc_den >= :tu)
                     FOR UPDATE
                    """,
                    {"lp_id": lp_id, "lg": loai_gia, "tu": hieu_luc_tu}
                )
                active_row = cur.fetchone()

                if active_row:
                    curr_id = active_row[0]
                    curr_tu = active_row[1]
                    if hasattr(curr_tu, "date"):
                        curr_tu = curr_tu.date()

                    if curr_tu == hieu_luc_tu:
                        # Same start date: directly update don_gia
                        cur.execute(
                            "UPDATE bang_gia SET don_gia = :dg WHERE bang_gia_id = :id",
                            {"dg": don_gia, "id": curr_id}
                        )
                    else:
                        # Terminate current row at (hieu_luc_tu - 1 day)
                        day_before = hieu_luc_tu - timedelta(days=1)
                        cur.execute(
                            """
                            UPDATE bang_gia
                               SET hieu_luc_den = :den
                             WHERE bang_gia_id = :id
                            """,
                            {"den": day_before, "id": curr_id}
                        )

                        # Insert new price record
                        cur.execute(
                            """
                            INSERT INTO bang_gia (loai_phong_id, loai_gia, don_gia, hieu_luc_tu, hieu_luc_den, ngay_tao)
                            VALUES (:lp_id, :lg, :dg, :tu, NULL, SYSTIMESTAMP)
                            """,
                            {"lp_id": lp_id, "lg": loai_gia, "dg": don_gia, "tu": hieu_luc_tu}
                        )
                else:
                    # No active row found: direct insert
                    cur.execute(
                        """
                        INSERT INTO bang_gia (loai_phong_id, loai_gia, don_gia, hieu_luc_tu, hieu_luc_den, ngay_tao)
                        VALUES (:lp_id, :lg, :dg, :tu, NULL, SYSTIMESTAMP)
                        """,
                        {"lp_id": lp_id, "lg": loai_gia, "dg": don_gia, "tu": hieu_luc_tu}
                    )

            conn.commit()
            return {"success": True, "message": "Điều chỉnh giá thành công"}

        except oracledb.DatabaseError as e:
            conn.rollback()
            raise parse_oracle_error(e)
        except Exception:
            conn.rollback()
            raise
