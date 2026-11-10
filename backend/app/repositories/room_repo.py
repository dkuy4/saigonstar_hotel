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
