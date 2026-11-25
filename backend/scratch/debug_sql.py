import traceback
import oracledb

conn = oracledb.connect(user="hotel_app", password="HotelApp123#", dsn="localhost:1521/FREEPDB1")
cur = conn.cursor()
try:
    sql = """
    SELECT 
        dp.dat_phong_id,
        dp.ma_tra_cuu,
        dp.loai_dat,
        dp.kenh_dat,
        dp.trang_thai,
        TO_CHAR(dp.tu_luc, 'YYYY-MM-DD"T"HH24:MI:SS') AS tu_luc,
        TO_CHAR(dp.den_luc, 'YYYY-MM-DD"T"HH24:MI:SS') AS den_luc,
        dp.so_khach,
        dp.tien_phong,
        dp.tien_vat,
        dp.tong_tien,
        (SELECT lp.ma_hang FROM hotel_owner.dat_phong_doan dpd
           JOIN hotel_owner.phong p ON p.phong_id = dpd.phong_id
           JOIN hotel_owner.loai_phong lp ON lp.loai_phong_id = p.loai_phong_id
          WHERE dpd.dat_phong_id = dp.dat_phong_id AND ROWNUM = 1) AS ma_hang,
        (SELECT lpd.ten FROM hotel_owner.dat_phong_doan dpd
           JOIN hotel_owner.phong p ON p.phong_id = dpd.phong_id
           JOIN hotel_owner.loai_phong lp ON lp.loai_phong_id = p.loai_phong_id
           LEFT JOIN hotel_owner.loai_phong_dich lpd ON (lpd.loai_phong_id = lp.loai_phong_id AND lpd.ngon_ngu = 'vi')
          WHERE dpd.dat_phong_id = dp.dat_phong_id AND ROWNUM = 1) AS ten_hang,
        (SELECT p.ma_phong FROM hotel_owner.dat_phong_doan dpd
           JOIN hotel_owner.phong p ON p.phong_id = dpd.phong_id
          WHERE dpd.dat_phong_id = dp.dat_phong_id AND ROWNUM = 1) AS so_phong,
        TO_CHAR(dp.ngay_tao, 'YYYY-MM-DD"T"HH24:MI:SS') AS ngay_tao
    FROM hotel_owner.dat_phong dp
    LEFT JOIN hotel_owner.khach_hang kh ON dp.khach_hang_id = kh.khach_hang_id
    WHERE dp.khach_hang_id = :kid OR (kh.email IS NOT NULL AND LOWER(kh.email) = :email)
    ORDER BY dp.ngay_tao DESC
    """
    cur.execute(sql, {"kid": 1671, "email": "test@test.com"})
    print("Query success! Rows:", cur.fetchall())
except Exception as e:
    traceback.print_exc()
finally:
    conn.close()
