import logging
from typing import Optional, List, Dict, Any
import oracledb

from app.errors import parse_oracle_error

logger = logging.getLogger(__name__)

class HousekeepingRepository:
    @staticmethod
    def get_tasks(
        conn: oracledb.Connection,
        status: Optional[str] = None,
        floor: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Lấy danh sách phòng cho bộ phận buồng phòng.
        TUYỆT ĐỐI TUÂN THỦ NGUYÊN TẮC BẢO MẬT AC-16, FR-25:
        Chỉ trả về các trường kỹ thuật/vận hành phòng,
        KHÔNG ĐƯỢC CHỨA bất kỳ thông tin khách hàng hay giá phòng nào.
        """
        where_clauses = ["p.dang_hoat_dong = 1"]
        params: Dict[str, Any] = {}

        if status and status.upper() != "ALL":
            where_clauses.append("p.trang_thai = :p_status")
            params["p_status"] = status.upper()
        elif not status:
            # Mặc định chỉ lấy phòng đang dọn
            where_clauses.append("p.trang_thai = 'DANG_DON'")

        if floor is not None:
            where_clauses.append("p.so_tang = :p_floor")
            params["p_floor"] = floor

        where_sql = " AND ".join(where_clauses)

        query = f"""
            SELECT p.phong_id,
                   p.ma_phong,
                   p.so_tang,
                   p.loai_phong_id,
                   lp.ma_hang,
                   NVL(lpd.ten, lp.ma_hang) AS ten_hang,
                   p.trang_thai,
                   p.ghi_chu,
                   (
                       SELECT MAX(nk.thoi_diem)
                         FROM hotel_owner.nhat_ky_kiem_toan nk
                        WHERE nk.bang = 'PHONG'
                          AND nk.khoa_dong = TO_CHAR(p.phong_id)
                   ) AS last_action_at
              FROM hotel_owner.phong p
              JOIN hotel_owner.loai_phong lp ON p.loai_phong_id = lp.loai_phong_id
              LEFT JOIN hotel_owner.loai_phong_dich lpd
                     ON lp.loai_phong_id = lpd.loai_phong_id
                    AND lpd.ngon_ngu = 'vi'
             WHERE {where_sql}
             ORDER BY p.so_tang, p.ma_phong
        """

        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

            items = []
            for r in rows:
                items.append({
                    "roomId": r[0],
                    "roomNumber": r[1],
                    "floor": r[2],
                    "roomTypeId": r[3],
                    "roomType": r[4],
                    "roomTypeName": r[5] or r[4],
                    "status": r[6],
                    "notes": r[7],
                    "lastActionAt": r[8]
                })
            return items

    @staticmethod
    def start_cleaning(conn: oracledb.Connection, room_id: int) -> None:
        """Gọi PKG_PHONG.BAT_DAU_DON ghi nhận bắt đầu dọn phòng vào nhật ký (FR-24)."""
        with conn.cursor() as cur:
            try:
                cur.callproc("PKG_PHONG.BAT_DAU_DON", [room_id])
                conn.commit()
            except oracledb.DatabaseError as e:
                conn.rollback()
                raise parse_oracle_error(e)

    @staticmethod
    def finish_cleaning(conn: oracledb.Connection, room_id: int) -> None:
        """Gọi PKG_PHONG.DON_XONG chuyển trạng thái phòng từ DANG_DON về TRONG."""
        with conn.cursor() as cur:
            try:
                cur.callproc("PKG_PHONG.DON_XONG", [room_id])
                conn.commit()
            except oracledb.DatabaseError as e:
                conn.rollback()
                raise parse_oracle_error(e)
