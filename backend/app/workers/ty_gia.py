import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import oracledb
import urllib.request
import json

from app.db import fetch_cursor_as_dicts

logger = logging.getLogger(__name__)

SUPPORTED_CURRENCIES = ["USD", "EUR", "CNY", "KRW", "JPY"]

class ExchangeRateService:
    """Service for managing and synchronizing daily foreign exchange rates (F13, FR-10, D-37)."""

    @staticmethod
    def get_latest_rates(conn: oracledb.Connection) -> List[Dict[str, Any]]:
        """Fetch latest exchange rates for all supported currencies."""
        sql = """
        SELECT t1.ngoai_te, t1.ty_gia_vnd, t1.ngay_cap_nhat
          FROM ty_gia t1
         WHERE t1.ngay_cap_nhat = (
           SELECT MAX(t2.ngay_cap_nhat) FROM ty_gia t2 WHERE t2.ngoai_te = t1.ngoai_te
         )
         ORDER BY t1.ngoai_te
        """
        with conn.cursor() as cur:
            cur.execute(sql)
            rows = fetch_cursor_as_dicts(cur)
            return [
                {
                    "currency": r["ngoai_te"],
                    "rate_vnd": float(r["ty_gia_vnd"]),
                    "updated_at": r["ngay_cap_nhat"].strftime("%Y-%m-%d") if isinstance(r["ngay_cap_nhat"], (datetime, date)) else str(r["ngay_cap_nhat"])
                }
                for r in rows
            ]

    @staticmethod
    def save_manual_rates(conn: oracledb.Connection, rates: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Save manual exchange rates entered by Manager (POST /exchange-rates/manual).
        Upserts into TY_GIA with today's date (TRUNC(SYSDATE)).
        """
        today_date = date.today()
        sql = """
        MERGE INTO ty_gia t
        USING (SELECT :ngoai_te AS ngoai_te, TRUNC(SYSDATE) AS ngay_cap_nhat, :ty_gia_vnd AS ty_gia_vnd FROM dual) s
        ON (t.ngoai_te = s.ngoai_te AND t.ngay_cap_nhat = s.ngay_cap_nhat)
        WHEN MATCHED THEN
          UPDATE SET t.ty_gia_vnd = s.ty_gia_vnd
        WHEN NOT MATCHED THEN
          INSERT (ngoai_te, ngay_cap_nhat, ty_gia_vnd)
          VALUES (s.ngoai_te, s.ngay_cap_nhat, s.ty_gia_vnd)
        """
        with conn.cursor() as cur:
            for curr, rate in rates.items():
                curr_upper = curr.strip().upper()
                if curr_upper in SUPPORTED_CURRENCIES and rate > 0:
                    cur.execute(sql, {"ngoai_te": curr_upper, "ty_gia_vnd": float(rate)})
            conn.commit()

        return ExchangeRateService.get_latest_rates(conn)

    @staticmethod
    def sync_exchange_rates(conn: oracledb.Connection) -> Dict[str, Any]:
        """
        Fetch exchange rates from external banking/exchange API and save to TY_GIA.
        Includes graceful fallback if external network is unavailable.
        """
        updated = {}
        error_msg = None
        
        # Try fetching from free open exchange API (using USD base)
        try:
            req = urllib.request.Request(
                "https://open.er-api.com/v6/latest/USD",
                headers={"User-Agent": "SaigonStarHotel/1.0"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    rates = data.get("rates", {})
                    vnd_per_usd = rates.get("VND", 25450.0)
                    
                    # Convert target currencies against VND
                    for curr in SUPPORTED_CURRENCIES:
                        if curr == "USD":
                            updated[curr] = round(vnd_per_usd, 2)
                        elif curr in rates and rates[curr] > 0:
                            # 1 Unit of CURR = (vnd_per_usd / rates[curr]) VND
                            updated[curr] = round(vnd_per_usd / rates[curr], 2)
        except Exception as e:
            logger.warning(f"External exchange rate API fetch failed: {e}. Using fallback defaults.")
            error_msg = str(e)
            # Default reference rates if API unavailable
            updated = {
                "USD": 25450.0,
                "EUR": 27200.0,
                "CNY": 3520.0,
                "KRW": 18.5,
                "JPY": 168.0
            }

        ExchangeRateService.save_manual_rates(conn, updated)
        
        return {
            "status": "success",
            "synced_rates": updated,
            "source": "api" if error_msg is None else "fallback_defaults",
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }
