import sys
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import get_pool

pool = get_pool()
with pool.acquire() as conn:
    with conn.cursor() as cur:
        cur.execute("ALTER SESSION SET CURRENT_SCHEMA = HOTEL_OWNER")
        cur.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE 
            FROM ALL_TAB_COLUMNS 
            WHERE OWNER = 'HOTEL_OWNER' AND TABLE_NAME = 'NHAT_KY_KIEM_TOAN' 
            ORDER BY COLUMN_ID
        """)
        cols = cur.fetchall()
        print("Columns in NHAT_KY_KIEM_TOAN:")
        for c in cols:
            print(f"  {c[0]} ({c[1]}, nullable={c[3]})")
            
        cur.execute("SELECT COUNT(*) FROM NHAT_KY_KIEM_TOAN")
        print("Total rows:", cur.fetchone()[0])

        cur.execute("""
            SELECT n.NHAT_KY_ID, n.BANG, n.KHOA_DONG, n.HANH_DONG, n.NGUOI_THUC_HIEN_ID, 
                   u.TEN_DANG_NHAP, n.VAI_TRO, n.KENH, n.THOI_DIEM, n.LY_DO,
                   SUBSTR(n.GIA_TRI_CU, 1, 80), SUBSTR(n.GIA_TRI_MOI, 1, 80)
            FROM NHAT_KY_KIEM_TOAN n
            LEFT JOIN NGUOI_DUNG u ON n.NGUOI_THUC_HIEN_ID = u.NGUOI_DUNG_ID
            ORDER BY n.NHAT_KY_ID DESC
            FETCH FIRST 5 ROWS ONLY
        """)
        rows = cur.fetchall()
        print("\nSample 5 rows:")
        for r in rows:
            print("Row:", r)

        cur.execute("""
            SELECT NHAT_KY_ID, TO_CHAR(THOI_DIEM, 'YYYY-MM-DD HH24:MI:SS TZH:TZM')
            FROM NHAT_KY_KIEM_TOAN
            WHERE BANG = 'PHONG' AND KHOA_DONG = '222'
        """)
        for r in cur.fetchall():
            print("Formatted THOI_DIEM:", r)

        try:
            cur.execute("UPDATE NHAT_KY_KIEM_TOAN SET LY_DO = 'hack' WHERE ROWNUM = 1")
            print("UPDATE succeeded?! Rows affected:", cur.rowcount)
        except oracledb.DatabaseError as ex:
            print("UPDATE caught exception:", ex)
