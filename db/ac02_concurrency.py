"""AC-01, AC-02: nhiều phiên cùng đặt một phòng và một khung giờ; đúng 1 phiên thành công.
Chạy trên Oracle thật (không chạy được trong môi trường soạn tài liệu vì không có Oracle).

  pip install oracledb
  set ORA_USER=hotel_owner  ORA_PASSWORD=...  ORA_DSN=localhost:1521/FREEPDB1
  python ac02_concurrency.py [--yeu-cau 1000] [--phien 20] [--lan 5] [--phong 210]

Mỗi yêu cầu: INSERT DAT_PHONG, INSERT DAT_PHONG_DOAN, COMMIT. Trigger TRG_DAT_PHONG_DOAN_TRUNG khóa dòng phòng và
ném ORA-20001 ROOM_CONFLICT cho phiên đến sau. Mỗi lần lặp dùng một khung giờ riêng trong năm 2032."""
import argparse, os, sys, time
from concurrent.futures import ThreadPoolExecutor
import oracledb

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ap = argparse.ArgumentParser()
ap.add_argument('--yeu-cau', type=int, default=1000)
ap.add_argument('--phien', type=int, default=20, help='số kết nối trong pool (bản Free giới hạn số phiên)')
ap.add_argument('--lan', type=int, default=5)
ap.add_argument('--phong', default='210')
a = ap.parse_args()

pool = oracledb.create_pool(user=os.environ['ORA_USER'], password=os.environ['ORA_PASSWORD'], dsn=os.environ['ORA_DSN'],
                            min=min(4, a.phien), max=a.phien, increment=2)

INS_DON = """INSERT INTO dat_phong (khach_hang_id, loai_dat, kenh_dat, trang_thai, tu_luc, den_luc, so_khach,
               don_gia_ap_dung, don_gia_ngay_ap_dung, tien_phong, thue_suat, tien_vat, tong_tien, ngon_ngu)
             VALUES (:kh, 'GIO', 'API', 'CONFIRMED', TO_TIMESTAMP_TZ(:tu, 'YYYY-MM-DD"T"HH24:MI:SSTZH:TZM'),
                     TO_TIMESTAMP_TZ(:den, 'YYYY-MM-DD"T"HH24:MI:SSTZH:TZM'), 1, 80000, 550000, 240000, 0.08, 19200, 259200, 'vi')
             RETURNING dat_phong_id INTO :id"""
INS_DOAN = """INSERT INTO dat_phong_doan (dat_phong_id, phong_id, tu_luc, den_luc)
              VALUES (:dp, :ph, TO_TIMESTAMP_TZ(:tu, 'YYYY-MM-DD"T"HH24:MI:SSTZH:TZM'),
                      TO_TIMESTAMP_TZ(:den, 'YYYY-MM-DD"T"HH24:MI:SSTZH:TZM'))"""

def mot_yeu_cau(kh, phong_id, tu, den):
    with pool.acquire() as con:
        cur = con.cursor()
        try:
            out = cur.var(int)
            cur.execute(INS_DON, kh=kh, tu=tu, den=den, id=out)
            cur.execute(INS_DOAN, dp=out.getvalue()[0], ph=phong_id, tu=tu, den=den)
            con.commit()
            return 'OK'
        except oracledb.DatabaseError as e:
            con.rollback()
            msg = str(e.args[0])
            if 'ROOM_CONFLICT' in msg: return 'CONFLICT'
            if 'ROOM_BUSY' in msg: return 'BUSY'
            return 'LOI: ' + msg.splitlines()[0]

with pool.acquire() as con:
    cur = con.cursor()
    cur.execute("SELECT phong_id FROM phong WHERE ma_phong = :m", m=a.phong)
    phong_id = cur.fetchone()[0]
    kh = cur.var(int)
    cur.execute("INSERT INTO khach_hang (ho_ten, sdt, email) VALUES ('Thử đồng thời', '0900000001', 'ac02@example.com') RETURNING khach_hang_id INTO :id", id=kh)
    kh_id = kh.getvalue()[0]
    con.commit()

that_bai = 0
try:
    for lan in range(1, a.lan + 1):
        tu, den = f'2032-01-{lan:02d}T10:00:00+07:00', f'2032-01-{lan:02d}T13:00:00+07:00'
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=a.phien) as ex:
            kq = list(ex.map(lambda _: mot_yeu_cau(kh_id, phong_id, tu, den), range(a.yeu_cau)))
        dem = {k: kq.count(k) for k in set(kq)}
        with pool.acquire() as con:
            cur = con.cursor()
            cur.execute("""SELECT COUNT(*) FROM dat_phong_doan WHERE phong_id = :p
                              AND tu_luc = TO_TIMESTAMP_TZ(:tu, 'YYYY-MM-DD"T"HH24:MI:SSTZH:TZM')""", p=phong_id, tu=tu)
            con_lai = cur.fetchone()[0]
        dat = dem.get('OK', 0) == 1 and dem.get('CONFLICT', 0) == a.yeu_cau - 1 and con_lai == 1
        that_bai += 0 if dat else 1
        print(f'Lần {lan}: {"ĐẠT" if dat else "KHÔNG ĐẠT"}  kết quả={dem}  số đoạn trong CSDL={con_lai}  ({time.time()-t0:.1f}s)')
finally:
    with pool.acquire() as con:      # dọn dữ liệu thử; nhật ký kiểm toán vẫn giữ (chỉ thêm)
        cur = con.cursor()
        cur.execute("DELETE FROM dat_phong_doan WHERE dat_phong_id IN (SELECT dat_phong_id FROM dat_phong WHERE khach_hang_id = :k)", k=kh_id)
        cur.execute("DELETE FROM dat_phong WHERE khach_hang_id = :k", k=kh_id)
        cur.execute("DELETE FROM khach_hang WHERE khach_hang_id = :k", k=kh_id)
        con.commit()
print('AC-02 ĐẠT' if that_bai == 0 else f'AC-02 KHÔNG ĐẠT ({that_bai}/{a.lan} lần)')
sys.exit(1 if that_bai else 0)
