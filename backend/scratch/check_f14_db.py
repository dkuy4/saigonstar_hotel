import sys
sys.path.insert(0, r"D:\HQT-CSDL\saigonstar_hotel\backend")
from app.db import get_pool
from app.config import settings

def main():
    pool = get_pool()
    with pool.acquire() as conn:
        with conn.cursor() as cur:
            cur.execute(f"ALTER SESSION SET CURRENT_SCHEMA = {settings.ORA_SCHEMA}")
            
            print("=== CAU_HINH_HE_THONG ===")
            cur.execute("SELECT DISTINCT ma_tham_so, gia_tri_so, gia_tri_chu FROM cau_hinh_he_thong ORDER BY ma_tham_so")
            for r in cur.fetchall():
                print(r)
                
            print("\n=== NOI_DUNG_DICH (EMAIL) ===")
            cur.execute("SELECT ma_khoa, ngon_ngu, tieu_de, SUBSTR(noi_dung, 1, 60) FROM noi_dung_dich WHERE ma_khoa LIKE 'EMAIL%' ORDER BY ma_khoa, ngon_ngu")
            rows = cur.fetchall()
            print(f"Total email templates in DB: {len(rows)}")
            for r in rows[:15]:
                print(r)
                
            print("\n=== HANG_DOI_EMAIL ===")
            cur.execute("SELECT trang_thai, COUNT(*) FROM hang_doi_email GROUP BY trang_thai")
            print("Counts:", cur.fetchall())
            
            cur.execute("""
                SELECT privilege, table_name 
                FROM all_tab_privs 
                WHERE grantee = 'HOTEL_APP' AND table_name IN ('HANG_DOI_EMAIL', 'NOI_DUNG_DICH', 'PKG_EMAIL')
            """)
            print("\n=== PRIVILEGES FOR HOTEL_APP ===")
            for r in cur.fetchall():
                print(r)
    pool.close()

if __name__ == "__main__":
    main()
