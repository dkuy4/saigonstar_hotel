"""
Repository cho Quản lý Bản dịch chính sách và Mẫu email (F16.5, FR-33, BR-55).
"""
import logging
from typing import List, Dict, Optional, Any
import oracledb
from app.errors import BusinessException
from app.core.translation_meta import (
    SUPPORTED_LANGUAGES,
    TRANSLATION_DEFINITIONS,
)
from app.schemas.translation import (
    TranslationItem,
    TranslationMatrixItem,
    TranslationUpdateResponse,
)

logger = logging.getLogger(__name__)

class TranslationRepository:
    @staticmethod
    def get_translations(
        conn: oracledb.Connection,
        ma_noi_dung: Optional[str] = None,
        ngon_ngu: Optional[str] = None,
    ) -> List[TranslationMatrixItem]:
        """
        Lấy danh sách ma trận bản dịch 7 ngôn ngữ cho từng nội dung.
        """
        with conn.cursor() as cur:
            sql = "SELECT ma_noi_dung, ngon_ngu, noi_dung, TO_CHAR(ngay_tao, 'YYYY-MM-DD HH24:MI:SS') FROM noi_dung_dich WHERE 1=1"
            params: Dict[str, Any] = {}
            if ma_noi_dung and ma_noi_dung.strip():
                sql += " AND ma_noi_dung = :ma"
                params["ma"] = ma_noi_dung.strip()
            if ngon_ngu and ngon_ngu.strip():
                sql += " AND ngon_ngu = :lang"
                params["lang"] = ngon_ngu.strip()

            cur.execute(sql, params)
            rows = cur.fetchall()

            # Map raw data by (ma_noi_dung, ngon_ngu)
            raw_map: Dict[str, Dict[str, str]] = {}
            for r in rows:
                c_ma = r[0]
                c_lang = r[1]
                val = r[2].read() if hasattr(r[2], "read") else str(r[2]) if r[2] else ""
                if c_ma not in raw_map:
                    raw_map[c_ma] = {}
                raw_map[c_ma][c_lang] = val

            matrix_items: List[TranslationMatrixItem] = []
            valid_codes = list(TRANSLATION_DEFINITIONS.keys())
            if ma_noi_dung:
                valid_codes = [c for c in valid_codes if c == ma_noi_dung]

            for code in valid_codes:
                meta = TRANSLATION_DEFINITIONS[code]
                code_trans = raw_map.get(code, {})

                ban_dich: Dict[str, Optional[str]] = {}
                chua_ra: Dict[str, bool] = {}

                for lang_info in SUPPORTED_LANGUAGES:
                    lang_code = lang_info["code"]
                    ban_dich[lang_code] = code_trans.get(lang_code, None)
                    # Nhãn 'chưa rà' cho ngôn ngữ ngoài Việt và Anh (F16.5)
                    chua_ra[lang_code] = not lang_info["is_primary"]

                item = TranslationMatrixItem(
                    ma_noi_dung=code,
                    loai=meta["loai"],
                    tieu_de=meta["tieu_de"],
                    mo_ta=meta["mo_ta"],
                    bien_bat_buoc=meta.get("bien_bat_buoc", []),
                    ban_dich=ban_dich,
                    chua_ra=chua_ra,
                )
                matrix_items.append(item)

            return matrix_items

    @staticmethod
    def get_single_translation(
        conn: oracledb.Connection,
        ma_noi_dung: str,
        ngon_ngu: str,
    ) -> TranslationItem:
        """
        Lấy chi tiết một bản dịch cụ thể.
        """
        if ma_noi_dung not in TRANSLATION_DEFINITIONS:
            raise BusinessException("NOT_FOUND", f"Không tìm thấy mã nội dung: {ma_noi_dung}")

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT ma_noi_dung, ngon_ngu, noi_dung, TO_CHAR(ngay_tao, 'YYYY-MM-DD HH24:MI:SS')
                FROM noi_dung_dich
                WHERE ma_noi_dung = :ma AND ngon_ngu = :lang
                """,
                {"ma": ma_noi_dung, "lang": ngon_ngu},
            )
            row = cur.fetchone()
            if not row:
                raise BusinessException("NOT_FOUND", f"Chưa có bản dịch cho mã {ma_noi_dung} ngôn ngữ {ngon_ngu}")

            val = row[2].read() if hasattr(row[2], "read") else str(row[2]) if row[2] else ""
            return TranslationItem(
                ma_noi_dung=row[0],
                ngon_ngu=row[1],
                noi_dung=val,
                ngay_tao=row[3],
            )

    @staticmethod
    def upsert_translation(
        conn: oracledb.Connection,
        ma_noi_dung: str,
        ngon_ngu: str,
        noi_dung: str,
        current_user: Any,
    ) -> TranslationUpdateResponse:
        """
        Cập nhật hoặc thêm mới bản dịch nội dung theo ngôn ngữ (F16.5, FR-33, BR-55).
        """
        if ma_noi_dung not in TRANSLATION_DEFINITIONS:
            raise BusinessException("VALIDATION_ERROR", f"Mã nội dung không hợp lệ: {ma_noi_dung}")

        valid_lang_codes = [l["code"] for l in SUPPORTED_LANGUAGES]
        if ngon_ngu not in valid_lang_codes:
            raise BusinessException(
                "VALIDATION_ERROR",
                f"Mã ngôn ngữ không hợp lệ: {ngon_ngu}. Các ngôn ngữ được hỗ trợ: {', '.join(valid_lang_codes)}",
            )

        # Ràng buộc BR-55: Bản tiếng Việt có giá trị pháp lý khi tranh chấp, không được để trống
        if ngon_ngu == "vi" and not noi_dung.strip():
            raise BusinessException(
                "VALIDATION_ERROR",
                "Bản dịch tiếng Việt có giá trị pháp lý khi tranh chấp (BR-55), không được để trống.",
            )

        # Ràng buộc biến thay thế đối với mẫu email (F16.5 bước 1)
        meta = TRANSLATION_DEFINITIONS[ma_noi_dung]
        required_vars = meta.get("bien_bat_buoc", [])
        if required_vars:
            missing = [var for var in required_vars if var not in noi_dung]
            if missing:
                raise BusinessException(
                    "VALIDATION_ERROR",
                    f"Mẫu email thiếu các biến thay thế bắt buộc: {', '.join(missing)}",
                )

        # Thiết lập ngữ cảnh Oracle
        user_id = getattr(current_user, "user_id", None) or 1
        role = getattr(current_user, "role", "QUAN_LY")
        ly_do = f"Cập nhật bản dịch {ma_noi_dung} [{ngon_ngu}]"

        with conn.cursor() as cur:
            try:
                cur.execute(
                    "BEGIN pkg_ngu_canh.dat(:1, :2, :3); END;",
                    [user_id, role, ly_do],
                )
            except Exception as e:
                logger.warning(f"Could not set pkg_ngu_canh: {e}")

            # MERGE INTO noi_dung_dich
            merge_sql = """
            MERGE INTO noi_dung_dich t
            USING (SELECT :ma AS ma_noi_dung, :lang AS ngon_ngu FROM dual) s
            ON (t.ma_noi_dung = s.ma_noi_dung AND t.ngon_ngu = s.ngon_ngu)
            WHEN MATCHED THEN
              UPDATE SET t.noi_dung = :noi_dung, t.ngay_tao = SYSTIMESTAMP
            WHEN NOT MATCHED THEN
              INSERT (ma_noi_dung, ngon_ngu, noi_dung, ngay_tao)
              VALUES (:ma, :lang, :noi_dung, SYSTIMESTAMP)
            """
            cur.execute(merge_sql, {"ma": ma_noi_dung, "lang": ngon_ngu, "noi_dung": noi_dung})
            conn.commit()

        canh_bao = (
            "Bản dịch này chưa qua chuyên viên hiệu đính, cần rà soát kỹ thuật ngữ trước khi áp dụng."
            if ngon_ngu not in ("vi", "en")
            else None
        )

        return TranslationUpdateResponse(
            success=True,
            ma_noi_dung=ma_noi_dung,
            ngon_ngu=ngon_ngu,
            noi_dung=noi_dung,
            canh_bao=canh_bao,
        )
