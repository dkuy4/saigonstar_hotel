from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import oracledb

from app.db import fetch_cursor_as_dicts
from app.errors import parse_oracle_error

class RoomRepository:
    @staticmethod
    def get_room_board(conn: oracledb.Connection, at_time: Optional[datetime] = None) -> Dict[str, Any]:
        target_time = at_time or datetime.now(timezone.utc)
        if target_time.tzinfo is None:
            target_time = target_time.replace(tzinfo=timezone.utc)

        with conn.cursor() as cur:
            try:
                res_cursor = cur.callfunc(
                    "PKG_PHONG.SO_DO",
                    oracledb.CURSOR,
                    [target_time]
                )
                rows = fetch_cursor_as_dicts(res_cursor)
                res_cursor.close()
            except oracledb.DatabaseError as e:
                raise parse_oracle_error(e)

        floors_dict: Dict[int, List[Dict[str, Any]]] = {}
        stats = {
            "total": len(rows),
            "available": 0,
            "occupied": 0,
            "cleaning": 0,
            "maintenance": 0
        }

        for r in rows:
            st = r["trang_thai"]
            if st == "TRONG":
                stats["available"] += 1
            elif st == "DANG_O":
                stats["occupied"] += 1
            elif st == "DANG_DON":
                stats["cleaning"] += 1
            elif st == "BAO_TRI":
                stats["maintenance"] += 1

            current_b = None
            if r["ma_don_hien_tai"]:
                current_b = {
                    "bookingCode": r["ma_don_hien_tai"],
                    "bookingStatus": r["trang_thai_don"],
                    "from": r["luot_tu"],
                    "to": r["luot_den"]
                }

            next_b = None
            if r["ma_don_ke_tiep"]:
                next_b = {
                    "bookingCode": r["ma_don_ke_tiep"],
                    "from": r["ke_tiep_tu"]
                }

            tile = {
                "roomId": r["phong_id"],
                "roomNumber": r["ma_phong"],
                "floor": r["so_tang"],
                "roomType": r["ma_hang"],
                "status": st,
                "isActive": bool(r["dang_hoat_dong"]),
                "currentBooking": current_b,
                "nextBooking": next_b
            }

            floor_num = r["so_tang"]
            if floor_num not in floors_dict:
                floors_dict[floor_num] = []
            floors_dict[floor_num].append(tile)

        floors = [
            {"floor": f_num, "rooms": floors_dict[f_num]}
            for f_num in sorted(floors_dict.keys())
        ]

        return {
            "at": target_time,
            "floors": floors,
            "stats": stats
        }

    @staticmethod
    def get_rooms_admin(
        conn: oracledb.Connection,
        floor: Optional[int] = None,
        room_type: Optional[str] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
        query: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        conditions = ["1=1"]
        params: Dict[str, Any] = {}

        if floor is not None:
            conditions.append("p.so_tang = :p_floor")
            params["p_floor"] = floor

        if room_type:
            conditions.append("lp.ma_hang = :p_room_type")
            params["p_room_type"] = room_type.upper()

        if status:
            conditions.append("p.trang_thai = :p_status")
            params["p_status"] = status.upper()

        if is_active is not None:
            conditions.append("p.dang_hoat_dong = :p_is_active")
            params["p_is_active"] = is_active

        if query:
            conditions.append("(LOWER(p.ma_phong) LIKE :p_query OR LOWER(p.ghi_chu) LIKE :p_query)")
            params["p_query"] = f"%{query.strip().lower()}%"

        where_clause = " AND ".join(conditions)

        with conn.cursor() as cur:
            count_sql = f"""
                SELECT COUNT(*)
                  FROM hotel_owner.phong p
                  JOIN hotel_owner.loai_phong lp ON p.loai_phong_id = lp.loai_phong_id
                 WHERE {where_clause}
            """
            cur.execute(count_sql, params)
            total = cur.fetchone()[0]

            offset = (page - 1) * page_size
            data_sql = f"""
                SELECT p.phong_id, p.ma_phong, p.so_tang, p.loai_phong_id,
                       lp.ma_hang, lpd.ten, p.trang_thai, p.dang_hoat_dong,
                       p.ghi_chu, p.ngay_tao
                  FROM hotel_owner.phong p
                  JOIN hotel_owner.loai_phong lp ON p.loai_phong_id = lp.loai_phong_id
                  LEFT JOIN hotel_owner.loai_phong_dich lpd ON lp.loai_phong_id = lpd.loai_phong_id AND lpd.ngon_ngu = 'vi'
                 WHERE {where_clause}
                 ORDER BY p.so_tang, p.ma_phong
                OFFSET :p_offset ROWS FETCH NEXT :p_page_size ROWS ONLY
            """
            params["p_offset"] = offset
            params["p_page_size"] = page_size

            cur.execute(data_sql, params)
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
                "isActive": bool(r[7]),
                "notes": r[8],
                "createdAt": r[9]
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "pageSize": page_size
        }

    @staticmethod
    def get_room_by_id(conn: oracledb.Connection, room_id: int) -> Optional[Dict[str, Any]]:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT p.phong_id, p.ma_phong, p.so_tang, p.loai_phong_id,
                       lp.ma_hang, lpd.ten, p.trang_thai, p.dang_hoat_dong,
                       p.ghi_chu, p.ngay_tao
                  FROM hotel_owner.phong p
                  JOIN hotel_owner.loai_phong lp ON p.loai_phong_id = lp.loai_phong_id
                  LEFT JOIN hotel_owner.loai_phong_dich lpd ON lp.loai_phong_id = lpd.loai_phong_id AND lpd.ngon_ngu = 'vi'
                 WHERE p.phong_id = :p_room_id
                """,
                p_room_id=room_id
            )
            r = cur.fetchone()
            if not r:
                return None
            return {
                "roomId": r[0],
                "roomNumber": r[1],
                "floor": r[2],
                "roomTypeId": r[3],
                "roomType": r[4],
                "roomTypeName": r[5] or r[4],
                "status": r[6],
                "isActive": bool(r[7]),
                "notes": r[8],
                "createdAt": r[9]
            }

    @staticmethod
    def get_affected_bookings(conn: oracledb.Connection, room_id: int) -> List[Dict[str, Any]]:
        with conn.cursor() as cur:
            try:
                res_cursor = cur.callfunc("PKG_PHONG.DON_BI_ANH_HUONG", oracledb.CURSOR, [room_id])
                rows = fetch_cursor_as_dicts(res_cursor)
                res_cursor.close()
                return [
                    {
                        "bookingId": r["dat_phong_id"],
                        "bookingCode": r["ma_tra_cuu"],
                        "status": r["trang_thai"],
                        "from": r["tu_luc"],
                        "to": r["den_luc"],
                        "customerName": r["ho_ten"],
                        "customerPhone": r["sdt"],
                        "customerEmail": r["email"]
                    }
                    for r in rows
                ]
            except oracledb.DatabaseError as e:
                raise parse_oracle_error(e)

    @staticmethod
    def create_room(
        conn: oracledb.Connection,
        room_number: str,
        floor: int,
        room_type_id: int,
        notes: Optional[str] = None
    ) -> int:
        with conn.cursor() as cur:
            try:
                out_id = cur.var(int)
                cur.execute(
                    """
                    INSERT INTO hotel_owner.phong (
                        ma_phong, so_tang, loai_phong_id, trang_thai, dang_hoat_dong, ghi_chu, ngay_tao
                    ) VALUES (
                        :p_ma, :p_tang, :p_loai, 'TRONG', 1, :p_ghi_chu, SYSTIMESTAMP
                    ) RETURNING phong_id INTO :p_out_id
                    """,
                    p_ma=room_number.strip().upper(),
                    p_tang=floor,
                    p_loai=room_type_id,
                    p_ghi_chu=notes.strip() if notes else None,
                    p_out_id=out_id
                )
                conn.commit()
                return out_id.getvalue()[0]
            except oracledb.DatabaseError as e:
                conn.rollback()
                raise parse_oracle_error(e)

    @staticmethod
    def update_room(
        conn: oracledb.Connection,
        room_id: int,
        room_number: Optional[str] = None,
        floor: Optional[int] = None,
        room_type_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        notes: Optional[str] = None
    ) -> None:
        updates = []
        params: Dict[str, Any] = {"p_room_id": room_id}

        if room_number is not None:
            updates.append("ma_phong = :p_ma")
            params["p_ma"] = room_number.strip().upper()

        if floor is not None:
            updates.append("so_tang = :p_tang")
            params["p_tang"] = floor

        if room_type_id is not None:
            updates.append("loai_phong_id = :p_loai")
            params["p_loai"] = room_type_id

        if is_active is not None:
            updates.append("dang_hoat_dong = :p_is_active")
            params["p_is_active"] = 1 if is_active else 0

        if notes is not None:
            updates.append("ghi_chu = :p_ghi_chu")
            params["p_ghi_chu"] = notes.strip() if notes else None

        if not updates:
            return

        with conn.cursor() as cur:
            try:
                set_clause = ", ".join(updates)
                cur.execute(
                    f"UPDATE hotel_owner.phong SET {set_clause} WHERE phong_id = :p_room_id",
                    params
                )
                conn.commit()
            except oracledb.DatabaseError as e:
                conn.rollback()
                raise parse_oracle_error(e)

    @staticmethod
    def start_maintenance(
        conn: oracledb.Connection,
        room_id: int,
        reason: str,
        ignore_affected_bookings: bool = False
    ) -> None:
        with conn.cursor() as cur:
            try:
                cur.callproc(
                    "PKG_PHONG.BAT_BAO_TRI",
                    [room_id, reason.strip(), 1 if ignore_affected_bookings else 0]
                )
                conn.commit()
            except oracledb.DatabaseError as e:
                conn.rollback()
                raise parse_oracle_error(e)

    @staticmethod
    def end_maintenance(conn: oracledb.Connection, room_id: int) -> None:
        with conn.cursor() as cur:
            try:
                cur.callproc("PKG_PHONG.KET_THUC_BAO_TRI", [room_id])
                conn.commit()
            except oracledb.DatabaseError as e:
                conn.rollback()
                raise parse_oracle_error(e)

