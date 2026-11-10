import sys
from datetime import datetime, timezone, timedelta
import oracledb

VN_TZ = timezone(timedelta(hours=7))

conn = oracledb.connect(user='hotel_app', password='HotelApp123#', dsn='localhost:1521/FREEPDB1')
with conn.cursor() as cur:
    cur.execute("ALTER SESSION SET CURRENT_SCHEMA = HOTEL_OWNER")
    
    # Test 1: Hourly search for Standard (3 hours)
    # 2026-11-20 10:00:00 to 2026-11-20 13:00:00
    t_in = datetime(2026, 11, 20, 10, 0, 0, tzinfo=VN_TZ)
    t_out = datetime(2026, 11, 20, 13, 0, 0, tzinfo=VN_TZ)
    
    res_cur = cur.callfunc("PKG_DAT_PHONG.TIM_HANG_CON_PHONG", oracledb.CURSOR, ["GIO", t_in, t_out, None])
    cols = [col[0].lower() for col in res_cur.description]
    rows = [dict(zip(cols, r)) for r in res_cur.fetchall()]
    print("Test 1 (Hourly 3h):", rows)
    assert len(rows) == 1
    assert rows[0]['ma_hang'] == 'STANDARD'
    assert rows[0]['tien_phong'] == 240000  # 3 * 80.000 = 240.000
    assert rows[0]['thue_suat'] == 0.08
    assert rows[0]['tien_vat'] == 19200
    assert rows[0]['tong_tien'] == 259200

    # Test 2: Hourly 5 hours (10:00 to 15:00)
    t_out_5h = datetime(2026, 11, 20, 15, 0, 0, tzinfo=VN_TZ)
    res_cur = cur.callfunc("PKG_DAT_PHONG.TIM_HANG_CON_PHONG", oracledb.CURSOR, ["GIO", t_in, t_out_5h, None])
    cols = [col[0].lower() for col in res_cur.description]
    rows = [dict(zip(cols, r)) for r in res_cur.fetchall()]
    print("Test 2 (Hourly 5h):", rows[0]['ma_hang'], "tien_phong:", rows[0]['tien_phong'], "tong:", rows[0]['tong_tien'])
    assert rows[0]['tien_phong'] == 400000  # 5 * 80.000 = 400.000
    assert rows[0]['tong_tien'] == 432000

    # Test 3: Hourly 6 hours (10:00 to 16:00) -> capped at 1 day rate (550.000 VND)
    t_out_6h = datetime(2026, 11, 20, 16, 0, 0, tzinfo=VN_TZ)
    res_cur = cur.callfunc("PKG_DAT_PHONG.TIM_HANG_CON_PHONG", oracledb.CURSOR, ["GIO", t_in, t_out_6h, None])
    cols = [col[0].lower() for col in res_cur.description]
    rows = [dict(zip(cols, r)) for r in res_cur.fetchall()]
    print("Test 3 (Hourly 6h):", rows[0]['ma_hang'], "tien_phong:", rows[0]['tien_phong'], "tong:", rows[0]['tong_tien'])
    assert rows[0]['tien_phong'] == 550000  # BR-04: capped at 1 day rate
    assert rows[0]['tien_vat'] == 44000
    assert rows[0]['tong_tien'] == 594000

    # Test 4: Daily 2 nights (14:00 2026-11-20 to 12:00 2026-11-22)
    t_in_day = datetime(2026, 11, 20, 14, 0, 0, tzinfo=VN_TZ)
    t_out_day = datetime(2026, 11, 22, 12, 0, 0, tzinfo=VN_TZ)
    res_cur = cur.callfunc("PKG_DAT_PHONG.TIM_HANG_CON_PHONG", oracledb.CURSOR, ["NGAY", t_in_day, t_out_day, None])
    cols = [col[0].lower() for col in res_cur.description]
    rows = [dict(zip(cols, r)) for r in res_cur.fetchall()]
    print("Test 4 (Daily 2 nights): found", len(rows), "room types")
    for r in rows:
        print(" ->", r['ma_hang'], "rooms left:", r['so_phong_con'], "tien_phong:", r['tien_phong'], "VAT:", r['tien_vat'], "tong:", r['tong_tien'])
        if r['ma_hang'] == 'SUPERIOR':
            assert r['tien_phong'] == 1900000  # 2 * 950.000 = 1.900.000
            assert r['tien_vat'] == 152000
            assert r['tong_tien'] == 2052000  # Phụ lục B example!

print("\nALL ORACLE F02 TESTS PASSED PERFECTLY!")
conn.close()
