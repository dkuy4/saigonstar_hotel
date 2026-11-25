import sys
import oracledb
sys.path.insert(0, r"D:\HQT-CSDL\saigonstar_hotel\backend")
from app.db import get_pool, fetch_cursor_as_dicts
from app.config import settings

def test_procedures():
    pool = get_pool()
    with pool.acquire() as conn:
        with conn.cursor() as cur:
            cur.execute(f"ALTER SESSION SET CURRENT_SCHEMA = {settings.ORA_SCHEMA}")
            
            # Test het_han_giu_cho
            count_hold = cur.var(int)
            cur.callproc("PKG_DAT_PHONG.HET_HAN_GIU_CHO", [count_hold])
            print("HET_HAN_GIU_CHO processed:", count_hold.getvalue())
            
            # Test tu_no_show
            count_noshow = cur.var(int)
            cur.callproc("PKG_DAT_PHONG.TU_NO_SHOW", [count_noshow])
            print("TU_NO_SHOW processed:", count_noshow.getvalue())
            
            # Test doi_soat_phong_lich
            cur_out = cur.callfunc("PKG_PHONG.DOI_SOAT_PHONG_LICH", oracledb.DB_TYPE_CURSOR)
            discrepancies = fetch_cursor_as_dicts(cur_out)
            print("DOI_SOAT_PHONG_LICH discrepancies:", len(discrepancies), discrepancies)
            
    pool.close()

if __name__ == "__main__":
    test_procedures()
