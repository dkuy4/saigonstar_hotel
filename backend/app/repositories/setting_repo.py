from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
import oracledb

from app.db import fetch_cursor_as_dicts
from app.errors import BusinessException, parse_oracle_error
from app.core.settings_meta import SETTINGS_META, validate_setting_value

class SettingRepository:
    @staticmethod
    def get_settings(conn: oracledb.Connection) -> List[Dict[str, Any]]:
        """
        Retrieves all system configuration parameters grouped by code,
        including current effective value and history of revisions.
        """
        sql = """
        SELECT ma_tham_so,
               TO_CHAR(hieu_luc_tu, 'YYYY-MM-DD') AS hieu_luc_tu,
               TO_CHAR(hieu_luc_den, 'YYYY-MM-DD') AS hieu_luc_den,
               gia_tri_so,
               gia_tri_chu,
               mo_ta,
               CASE 
                 WHEN hieu_luc_tu <= TRUNC(SYSDATE) AND (hieu_luc_den IS NULL OR hieu_luc_den >= TRUNC(SYSDATE)) THEN 1
                 ELSE 0
               END AS is_active,
               TO_CHAR(ngay_tao, 'YYYY-MM-DD"T"HH24:MI:SS"+07:00"') AS ngay_tao
          FROM cau_hinh_he_thong
         ORDER BY ma_tham_so, hieu_luc_tu DESC
        """

        with conn.cursor() as cur:
            cur.execute(sql)
            rows = fetch_cursor_as_dicts(cur)

        # Group rows by ma_tham_so
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for r in rows:
            ma = r["ma_tham_so"]
            if ma not in grouped:
                grouped[ma] = []
            
            val = r["gia_tri_chu"] if r["gia_tri_chu"] is not None else float(r["gia_tri_so"]) if r["gia_tri_so"] is not None else None
            grouped[ma].append({
                "hieuLucTu": r["hieu_luc_tu"],
                "hieuLucDen": r["hieu_luc_den"],
                "giaTri": val,
                "isActive": bool(r["is_active"]),
                "ngayTao": r["ngay_tao"]
            })

        result = []
        for ma, hist in grouped.items():
            meta = SETTINGS_META.get(ma, {
                "ten": ma,
                "kieu": "CHU",
                "don_vi": "",
                "min": None,
                "max": None,
                "mo_ta": "",
                "canh_bao": None
            })

            # Pick active row or most recent
            active_row = next((h for h in hist if h["isActive"]), hist[0] if hist else None)
            curr_val = active_row["giaTri"] if active_row else None
            curr_tu = active_row["hieuLucTu"] if active_row else None
            curr_den = active_row["hieuLucDen"] if active_row else None

            result.append({
                "ma": ma,
                "ten": meta["ten"],
                "moTa": meta["mo_ta"] or (rows[0]["mo_ta"] if rows else ""),
                "kieu": meta["kieu"],
                "donVi": meta["don_vi"],
                "minVal": meta["min"],
                "maxVal": meta["max"],
                "canhBao": meta["canh_bao"],
                "giaTriHienHanh": curr_val,
                "hieuLucTu": curr_tu,
                "hieuLucDen": curr_den,
                "history": hist
            })

        # Sort so VAT and critical settings come first or alphabetical
        order_priority = ["THUE_SUAT_VAT", "KHOANG_DEM_PHUT", "PHUT_GIU_CHO", "NGUONG_GIO_TINH_NGAY", "GIO_NHAN_PHONG", "GIO_TRA_PHONG"]
        result.sort(key=lambda s: order_priority.index(s["ma"]) if s["ma"] in order_priority else 999)
        return result

    @staticmethod
    def update_setting(
        conn: oracledb.Connection,
        ma: str,
        gia_tri: Any,
        hieu_luc_tu: date,
        ly_do: str,
        user_id: int,
        user_role: str,
        ip: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Updates system configuration setting (F16.4):
        1. Validates value against settings_meta rules.
        2. Validates hieu_luc_tu >= today.
        3. Sets audit context via pkg_ngu_canh.
        4. Closes previous active record and inserts/updates active record.
        """
        ma = ma.upper().strip()
        ly_do = ly_do.strip() if ly_do else ""

        if not ly_do:
            raise BusinessException("VALIDATION_ERROR", "Vui lòng nhập lý do điều chỉnh tham số")

        today = date.today()
        if hieu_luc_tu < today:
            raise BusinessException("VALIDATION_ERROR", "Ngày hiệu lực không được ở quá khứ")

        # Step 1: Validate value
        is_valid, err_msg, num_val, str_val = validate_setting_value(ma, gia_tri)
        if not is_valid:
            raise BusinessException("INVALID_SETTING", err_msg)

        meta = SETTINGS_META.get(ma, {})
        warning_msg = meta.get("canh_bao")

        try:
            with conn.cursor() as cur:
                # Set audit context
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

                # Check if a row with exact start date already exists
                cur.execute(
                    """
                    SELECT hieu_luc_tu, hieu_luc_den
                      FROM cau_hinh_he_thong
                     WHERE ma_tham_so = :ma AND hieu_luc_tu = :tu
                     FOR UPDATE
                    """,
                    {"ma": ma, "tu": hieu_luc_tu}
                )
                same_date_row = cur.fetchone()

                if same_date_row:
                    # Same start date: update value in-place
                    cur.execute(
                        """
                        UPDATE cau_hinh_he_thong
                           SET gia_tri_so  = :gts,
                               gia_tri_chu = :gtc
                         WHERE ma_tham_so = :ma AND hieu_luc_tu = :tu
                        """,
                        {
                            "gts": num_val,
                            "gtc": str_val,
                            "ma": ma,
                            "tu": hieu_luc_tu
                        }
                    )
                else:
                    # Find active row in effect at hieu_luc_tu
                    cur.execute(
                        """
                        SELECT hieu_luc_tu, hieu_luc_den
                          FROM cau_hinh_he_thong
                         WHERE ma_tham_so = :ma
                           AND hieu_luc_tu < :tu
                           AND (hieu_luc_den IS NULL OR hieu_luc_den >= :tu)
                         FOR UPDATE
                        """,
                        {"ma": ma, "tu": hieu_luc_tu}
                    )
                    active_row = cur.fetchone()

                    # Find if there is a next future row after hieu_luc_tu
                    cur.execute(
                        """
                        SELECT MIN(hieu_luc_tu)
                          FROM cau_hinh_he_thong
                         WHERE ma_tham_so = :ma AND hieu_luc_tu > :tu
                        """,
                        {"ma": ma, "tu": hieu_luc_tu}
                    )
                    next_row = cur.fetchone()
                    next_tu = next_row[0] if next_row and next_row[0] else None

                    new_hieu_luc_den = None
                    if next_tu:
                        if hasattr(next_tu, "date"):
                            next_tu = next_tu.date()
                        new_hieu_luc_den = next_tu - timedelta(days=1)

                    if active_row:
                        curr_start = active_row[0]
                        day_before = hieu_luc_tu - timedelta(days=1)
                        cur.execute(
                            """
                            UPDATE cau_hinh_he_thong
                               SET hieu_luc_den = :den
                             WHERE ma_tham_so = :ma AND hieu_luc_tu = :tu_start
                            """,
                            {"den": day_before, "ma": ma, "tu_start": curr_start}
                        )

                    # Insert new record
                    cur.execute(
                        """
                        INSERT INTO cau_hinh_he_thong (ma_tham_so, hieu_luc_tu, hieu_luc_den, gia_tri_so, gia_tri_chu, mo_ta, ngay_tao)
                        VALUES (:ma, :tu, :den, :gts, :gtc, :mo_ta, SYSTIMESTAMP)
                        """,
                        {
                            "ma": ma,
                            "tu": hieu_luc_tu,
                            "den": new_hieu_luc_den,
                            "gts": num_val,
                            "gtc": str_val,
                            "mo_ta": meta.get("mo_ta", "")
                        }
                    )

            conn.commit()
            return {
                "success": True,
                "message": f"Cập nhật tham số {ma} thành công",
                "canh_bao": warning_msg
            }

        except oracledb.DatabaseError as e:
            conn.rollback()
            raise parse_oracle_error(e)
        except Exception:
            conn.rollback()
            raise
