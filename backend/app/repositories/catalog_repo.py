from datetime import datetime, date
from typing import Optional, Dict, List, Any
import oracledb
from app.db import fetch_cursor_as_dicts

class CatalogRepository:
    @staticmethod
    def get_room_types(conn: oracledb.Connection, lang: str = "vi") -> List[Dict[str, Any]]:
        sql = """
        SELECT lp.loai_phong_id, lp.ma_hang, lp.suc_chua,
               CASE WHEN lp.cho_thue_gio = 1 OR lp.cho_thue_gio = TRUE THEN 1 ELSE 0 END AS cho_thue_gio,
               lp.anh_url,
               COALESCE(lpd.ten, lp_vi.ten, lp.ma_hang) AS ten,
               COALESCE(lpd.mo_ta, lp_vi.mo_ta) AS mo_ta,
               COALESCE(lpd.tien_nghi, lp_vi.tien_nghi) AS tien_nghi,
               (SELECT don_gia FROM bang_gia bg 
                 WHERE bg.loai_phong_id = lp.loai_phong_id AND bg.loai_gia = 'NGAY' 
                   AND bg.hieu_luc_tu <= TRUNC(SYSDATE) 
                   AND (bg.hieu_luc_den IS NULL OR bg.hieu_luc_den >= TRUNC(SYSDATE))
                   AND ROWNUM = 1) AS gia_ngay,
               (SELECT don_gia FROM bang_gia bg 
                 WHERE bg.loai_phong_id = lp.loai_phong_id AND bg.loai_gia = 'GIO' 
                   AND bg.hieu_luc_tu <= TRUNC(SYSDATE) 
                   AND (bg.hieu_luc_den IS NULL OR bg.hieu_luc_den >= TRUNC(SYSDATE))
                   AND ROWNUM = 1) AS gia_gio
          FROM loai_phong lp
          LEFT JOIN loai_phong_dich lpd ON lpd.loai_phong_id = lp.loai_phong_id AND lpd.ngon_ngu = :lang
          LEFT JOIN loai_phong_dich lp_vi ON lp_vi.loai_phong_id = lp.loai_phong_id AND lp_vi.ngon_ngu = 'vi'
         ORDER BY lp.loai_phong_id
        """
        with conn.cursor() as cur:
            cur.execute(sql, {"lang": lang})
            rows = fetch_cursor_as_dicts(cur)
            result = []
            for r in rows:
                result.append({
                    "id": r["loai_phong_id"],
                    "code": r["ma_hang"],
                    "name": r["ten"],
                    "description": r["mo_ta"],
                    "amenities": r["tien_nghi"],
                    "capacity": r["suc_chua"],
                    "hourly_allowed": bool(r["cho_thue_gio"]),
                    "image_url": r["anh_url"],
                    "daily_price": float(r["gia_ngay"]) if r.get("gia_ngay") is not None else None,
                    "hourly_price": float(r["gia_gio"]) if r.get("gia_gio") is not None else None
                })
            return result

    @staticmethod
    def get_exchange_rates(conn: oracledb.Connection) -> List[Dict[str, Any]]:
        sql = """
        SELECT ngoai_te, ty_gia_vnd, ngay_cap_nhat
          FROM ty_gia t1
         WHERE ngay_cap_nhat = (
           SELECT MAX(ngay_cap_nhat) FROM ty_gia t2 WHERE t2.ngoai_te = t1.ngoai_te
         )
         ORDER BY ngoai_te
        """
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = fetch_cursor_as_dicts(cur)
            return [
                {
                    "currency": r["ngoai_te"],
                    "rate_vnd": float(r["ty_gia_vnd"]),
                    "updated_at": r["ngay_cap_nhat"].date() if isinstance(r["ngay_cap_nhat"], datetime) else r["ngay_cap_nhat"]
                }
                for r in rows
            ]

    @staticmethod
    def get_availability(
        conn: oracledb.Connection,
        loai_dat: str,
        checkin: datetime,
        checkout: datetime,
        guests: Optional[int] = None,
        lang: str = "vi"
    ) -> List[Dict[str, Any]]:
        # 1. Fetch exchange rates for currency conversion
        rates = CatalogRepository.get_exchange_rates(conn)
        rate_map = {r["currency"]: r["rate_vnd"] for r in rates}

        # 2. Fetch room type translations
        room_types = CatalogRepository.get_room_types(conn, lang=lang)
        type_meta = {rt["code"]: rt for rt in room_types}

        # 3. Call Oracle PKG_DAT_PHONG.TIM_HANG_CON_PHONG
        with conn.cursor() as cur:
            res_cur = cur.callfunc(
                "PKG_DAT_PHONG.TIM_HANG_CON_PHONG",
                oracledb.CURSOR,
                [loai_dat, checkin, checkout, guests]
            )
            raw_items = fetch_cursor_as_dicts(res_cur)
            res_cur.close()

        items = []
        for r in raw_items:
            code = r["ma_hang"]
            meta = type_meta.get(code, {})
            total_vnd = float(r["tong_tien"])
            
            # Compute converted prices for display (FR-10)
            converted = {}
            for cur_code, rate in rate_map.items():
                if rate > 0:
                    converted[cur_code] = round(total_vnd / rate, 2)

            items.append({
                "room_type_id": r["loai_phong_id"],
                "code": code,
                "name": meta.get("name") or code,
                "description": meta.get("description"),
                "amenities": meta.get("amenities"),
                "capacity": r["suc_chua"],
                "hourly_allowed": str(r.get("cho_thue_gio", "")).upper() in ("TRUE", "1"),
                "image_url": r["anh_url"] or meta.get("image_url"),
                "available_rooms": int(r["so_phong_con"]),
                "unit_price": float(r["don_gia"]),
                "daily_unit_price": float(r["don_gia_ngay"]),
                "room_amount": float(r["tien_phong"]),
                "vat_rate": float(r["thue_suat"]),
                "vat_amount": float(r["tien_vat"]),
                "total_amount": total_vnd,
                "converted_prices": converted
            })

        return items
