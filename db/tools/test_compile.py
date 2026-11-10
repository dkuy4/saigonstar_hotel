import oracledb

conn = oracledb.connect(user='hotel_owner', password='HotelOwner123#', dsn='localhost:1521/FREEPDB1')
cur = conn.cursor()

cur.execute("SELECT ma_tham_so, gia_tri_so FROM cau_hinh_he_thong WHERE ma_tham_so IN ('SO_LAN_DANG_NHAP_SAI_TOI_DA', 'PHUT_KHOA_TAM')")
for r in cur.fetchall():
    print(r)

conn.close()
