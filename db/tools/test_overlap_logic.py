"""Thử logic kiểm tra trùng phòng bằng SQLite (không có Oracle trong môi trường này).
Phần được thử là phép so sánh khoảng và bộ lọc trạng thái y hệt câu SQL trong PKG_KIEM_TRA_TRUNG.DEM_XUNG_DOT.
Không thử: khóa dòng FOR UPDATE và trigger thật; hai phần đó chạy bằng 06_tests.sql và ac02_concurrency.py trên Oracle."""
import random, sqlite3, unittest

DEM = 30  # khoảng đệm, phút (BR-06)
NOW = 1000  # "bây giờ", phút

# Giống hệt điều kiện trong dem_xung_dot, đổi sang SQLite (phút thay cho TIMESTAMP, :now thay cho SYSTIMESTAMP)
SQL = """
SELECT COUNT(*) FROM doan d JOIN don dp ON dp.id = d.don_id
 WHERE d.phong_id = :phong
   AND (:bo_qua IS NULL OR d.id <> :bo_qua)
   AND (dp.trang_thai IN ('CONFIRMED','CHECKED_IN','CHECKED_OUT')
        OR (dp.trang_thai = 'HOLD' AND dp.han_giu_cho > :now))
   AND d.tu_luc  < :den + :dem
   AND d.den_luc > :tu  - :dem
"""

def h(gio, phut=0):  # đổi giờ:phút thành phút kể từ 00:00
    return gio * 60 + phut

class Co(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.executescript("CREATE TABLE don(id INTEGER PRIMARY KEY, trang_thai TEXT, han_giu_cho INTEGER);"
                              "CREATE TABLE doan(id INTEGER PRIMARY KEY, don_id INT, phong_id INT, tu_luc INT, den_luc INT);")
        self.n = 0
    def them(self, phong, tu, den, trang_thai='CONFIRMED', han=None):
        self.n += 1
        self.db.execute('INSERT INTO don VALUES (?,?,?)', (self.n, trang_thai, han))
        self.db.execute('INSERT INTO doan VALUES (?,?,?,?,?)', (self.n, self.n, phong, tu, den))
        return self.n
    def dem(self, phong, tu, den, bo_qua=None):
        return self.db.execute(SQL, dict(phong=phong, tu=tu, den=den, bo_qua=bo_qua, now=NOW, dem=DEM)).fetchone()[0]

    def test_ac03_dem_30_phut(self):
        self.them(1, h(10), h(13))                       # đơn giờ 10:00-13:00
        self.assertGreater(self.dem(1, h(13, 20), h(15)), 0, '13:20 phải bị chặn vì còn đệm')
        self.assertEqual(self.dem(1, h(13, 30), h(15)), 0, '13:30 phải được nhận (BR-08: đúng lúc hết đệm)')

    def test_phia_truoc(self):
        self.them(1, h(10), h(13))
        self.assertEqual(self.dem(1, h(8), h(9, 30)), 0, 'kết thúc 09:30, A bắt đầu 10:00: đúng lúc hết đệm, không trùng')
        self.assertGreater(self.dem(1, h(8), h(9, 40)), 0, 'kết thúc 09:40 thì A bắt đầu 10:00 còn trong đệm')

    def test_khac_phong(self):
        self.them(1, h(10), h(13))
        self.assertEqual(self.dem(2, h(10), h(13)), 0)

    def test_trang_thai_khong_chiem(self):
        for tt in ('CANCELLED', 'NO_SHOW', 'EXPIRED'):
            self.them(1, h(10), h(13), tt)
        self.assertEqual(self.dem(1, h(10), h(13)), 0, 'BR-09: CANCELLED, NO_SHOW, EXPIRED không chiếm phòng')
        for tt in ('CONFIRMED', 'CHECKED_IN', 'CHECKED_OUT'):
            self.setUp(); self.them(1, h(10), h(13), tt)
            self.assertGreater(self.dem(1, h(11), h(12)), 0, tt)

    def test_hold_het_han(self):
        self.them(1, h(10), h(13), 'HOLD', han=NOW + 5)
        self.assertGreater(self.dem(1, h(11), h(12)), 0, 'HOLD còn hạn chiếm phòng')
        self.setUp(); self.them(1, h(10), h(13), 'HOLD', han=NOW - 1)
        self.assertEqual(self.dem(1, h(11), h(12)), 0, 'HOLD quá hạn không chiếm phòng dù chưa chuyển EXPIRED')

    def test_tra_som_ban_lai_phan_du(self):
        # Check-out sớm: PKG_DAT_PHONG rút DEN_LUC của đoạn về giờ trả thực tế (BR-37, D-33)
        d = self.them(1, h(14), h(36), 'CHECKED_OUT')
        self.db.execute('UPDATE doan SET den_luc = ? WHERE id = ?', (h(20), d))
        self.assertEqual(self.dem(1, h(21), h(30)), 0, 'phần dư sau giờ trả thực tế + đệm được bán lại')
        self.assertGreater(self.dem(1, h(20, 10), h(30)), 0, 'nhưng vẫn giữ đệm 30 phút')

    def test_bo_qua_chinh_no(self):
        d = self.them(1, h(10), h(13))
        self.assertEqual(self.dem(1, h(10), h(13), bo_qua=d), 0, 'đoạn đang kiểm tra không tự xung đột với chính nó')

    def test_tuong_duong_cong_thuc_br08(self):
        """Câu SQL đã viết lại (đưa đệm sang phía tham số để dùng chỉ mục) phải tương đương công thức BR-08 gốc:
        nhận A < trả B + đệm và nhận B < trả A + đệm."""
        rnd = random.Random(7)
        for _ in range(20000):
            a0 = rnd.randint(0, 600); a1 = a0 + rnd.randint(1, 300)
            b0 = rnd.randint(0, 600); b1 = b0 + rnd.randint(1, 300)
            goc = a0 < b1 + DEM and b0 < a1 + DEM
            viet_lai = b0 < a1 + DEM and b1 > a0 - DEM     # d = B, tham số = A
            self.assertEqual(goc, viet_lai, (a0, a1, b0, b1))

class MayTrangThai(unittest.TestCase):
    """Bảng chuyển trạng thái trong TRG_DAT_PHONG_TRANG_THAI (BR-14, BR-16, BR-18, BR-19)."""
    HOP_LE = {('HOLD','CONFIRMED'),('HOLD','EXPIRED'),('EXPIRED','CONFIRMED'),
              ('CONFIRMED','CHECKED_IN'),('CONFIRMED','CANCELLED'),('CONFIRMED','NO_SHOW'),('CHECKED_IN','CHECKED_OUT')}
    TT = ['HOLD','CONFIRMED','CHECKED_IN','CHECKED_OUT','CANCELLED','NO_SHOW','EXPIRED']
    def test_khong_huy_khi_dang_o(self):
        self.assertNotIn(('CHECKED_IN','CANCELLED'), self.HOP_LE)
        self.assertNotIn(('CHECKED_OUT','CANCELLED'), self.HOP_LE)
    def test_trang_thai_ket_thuc_khong_di_tiep(self):
        for t in ('CHECKED_OUT','CANCELLED','NO_SHOW'):
            self.assertFalse([b for a,b in self.HOP_LE if a == t], t)
    def test_moi_trang_thai_deu_den_duoc(self):
        den_duoc = {b for _, b in self.HOP_LE} | {'HOLD'}
        self.assertEqual(den_duoc | {'CONFIRMED'}, set(self.TT))
    def test_khop_trigger(self):
        with open('04_triggers.sql', encoding='utf8') as f:
            src = f.read()
        for a, b in self.HOP_LE:
            self.assertIn(a, src); self.assertIn(b, src)

if __name__ == '__main__':
    unittest.main(verbosity=2)
