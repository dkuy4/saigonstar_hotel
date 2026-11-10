"""Thử công thức giá của PKG_GIA bằng Python (không có Oracle). Đây là bản dựng lại công thức, dùng để kiểm tra
các ví dụ phụ lục B của BRD và các số kỳ vọng trong 09_tests_nghiep_vu.sql. Nó không chứng minh mã PL/SQL đúng;
bước đó do 09_tests_nghiep_vu.sql chạy trên Oracle đảm nhiệm."""
import math, unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

VN = timezone(timedelta(hours=7))
NGUONG, AN_HAN = 5, 30

def lam_tron(x): return int(Decimal(str(x)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
def tinh_vat(tien, thue): return lam_tron(Decimal(tien) * Decimal(str(thue)))
def so_phut(tu, den): return (den - tu).total_seconds() / 60
def so_dem(tu, den): return (den.astimezone(VN).date() - tu.astimezone(VN).date()).days
def tien_theo_gio(gio, gia_gio, gia_ngay): return gio * gia_gio if gio <= NGUONG else gia_ngay
def tien_phong(loai, tu, den, gia, gia_ngay):
    if loai == 'NGAY': return so_dem(tu, den) * gia_ngay
    p = so_phut(tu, den)
    if p <= 0 or p % 60: raise ValueError('SO_GIO')
    return tien_theo_gio(p / 60, gia, gia_ngay)
def tien_qua_gio(loai, tu, den, ra, gia, gia_ngay):
    qua = so_phut(den, ra)
    if qua <= AN_HAN: return 0
    if loai == 'NGAY': return math.ceil(qua / 1440) * gia_ngay
    g = so_phut(tu, den) / 60
    return tien_theo_gio(g + math.ceil(qua / 60), gia, gia_ngay) - tien_theo_gio(g, gia, gia_ngay)

def t(y, m, d, h=0, mi=0): return datetime(y, m, d, h, mi, tzinfo=VN)
G, N = 80000, 550000

class PhuLucB(unittest.TestCase):
    def test_v1_v2_v3(self):
        self.assertEqual(tien_theo_gio(3, G, N), 240000)
        self.assertEqual(tien_theo_gio(5, G, N), 400000)
        self.assertEqual(tien_theo_gio(6, G, N), 550000)
        self.assertEqual(N - 5 * G, 150000, 'giá nhảy từ giờ thứ 5 sang thứ 6 (ví dụ V3)')
    def test_v4_v9_hai_dem_superior(self):
        tien = tien_phong('NGAY', t(2031, 5, 10, 14), t(2031, 5, 12, 12), 950000, 950000)
        self.assertEqual(tien, 1900000)
        self.assertEqual(tinh_vat(tien, 0.08), 152000)
        self.assertEqual(tien + tinh_vat(tien, 0.08), 2052000)
    def test_v8_gia_han(self):
        self.assertEqual(tien_theo_gio(6, G, N) - tien_theo_gio(4, G, N), 230000)
    def test_v10_o_qua_gio(self):
        den = t(2031, 5, 12, 12)
        self.assertEqual(tien_qua_gio('NGAY', t(2031, 5, 10, 14), den, den + timedelta(hours=3), 950000, 950000), 950000)
        self.assertEqual(tinh_vat(950000, 0.08), 76000)
        self.assertEqual(950000 + 76000, 1026000)
    def test_an_han_30_phut(self):
        den = t(2031, 5, 12, 12)
        self.assertEqual(tien_qua_gio('NGAY', t(2031, 5, 10, 14), den, den + timedelta(minutes=20), 950000, 950000), 0)
        self.assertEqual(tien_qua_gio('NGAY', t(2031, 5, 10, 14), den, den + timedelta(minutes=30), 950000, 950000), 0, 'đúng 30 phút vẫn trong ân hạn')
        self.assertEqual(tien_qua_gio('NGAY', t(2031, 5, 10, 14), den, den + timedelta(minutes=31), 950000, 950000), 950000)
        self.assertEqual(tien_qua_gio('NGAY', t(2031, 5, 10, 14), den, den + timedelta(minutes=1500), 950000, 950000), 1900000)
    def test_qua_gio_don_gio(self):
        tu, den = t(2031, 5, 10, 10), t(2031, 5, 10, 14)
        self.assertEqual(tien_qua_gio('GIO', tu, den, den + timedelta(minutes=150), G, N), 230000, '4 giờ + 3 giờ làm tròn = 7 giờ, một giá ngày')
        self.assertEqual(tien_qua_gio('GIO', tu, den, den + timedelta(minutes=40), G, N), 80000, '4 giờ + 1 giờ = 5 giờ')
    def test_lam_tron_vat(self):
        self.assertEqual(tinh_vat(1006, 0.08), 80)   # 80,48
        self.assertEqual(tinh_vat(1007, 0.08), 81)   # 80,56
        self.assertEqual(tinh_vat(1500, 0.05), 75)
        self.assertEqual(tinh_vat(10, 0.05), 1, '0,5 làm tròn lên')
    def test_2_dem(self):
        self.assertEqual(so_dem(t(2031, 5, 10, 14), t(2031, 5, 12, 12)), 2)
    def test_moc_thue_2027(self):
        # 8% tới hết 31/12/2026, 10% từ 01/01/2027 (BR-58); chốt theo ngày tạo đơn
        self.assertEqual(tinh_vat(1900000, 0.10), 190000)
    def test_dieu_kien_5_gio_khong_vuot_ngay(self):
        self.assertLessEqual(5 * G, N)
        self.assertLessEqual(5 * 110000, N)
        self.assertGreater(5 * 120000, N)    # đúng ca 06_tests.sql và trigger TRG_BANG_GIA_RANG_BUOC

class HoaDon(unittest.TestCase):
    def test_check_out_phu_thu_giam_gia(self):
        tien_phong_don = 80000                      # đơn 1 giờ
        chiu_thue = tien_phong_don + 50000 - 20000
        vat = tinh_vat(chiu_thue, 0.08)
        self.assertEqual((chiu_thue, vat, chiu_thue + vat), (110000, 8800, 118800))
    def test_gia_han_hai_gio(self):
        them = (240000 + tinh_vat(240000, 0.08)) - (80000 + tinh_vat(80000, 0.08))
        self.assertEqual(them, 259200 - 86400)

if __name__ == '__main__':
    unittest.main(verbosity=2)
