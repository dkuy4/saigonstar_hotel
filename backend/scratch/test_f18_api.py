import httpx
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"
client = httpx.Client(timeout=10.0)

def print_test(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {name}" + (f" - {detail}" if detail else ""))
    if not passed:
        sys.exit(1)

def run_tests():
    print("=== BAT DAU KIEM THU F18: BAO CAO QUAN TRI & THONG KE KPI ===")

    # 1. Dang nhap tai khoan quan ly, le tan, buong phong
    res_mgr = client.post(f"{BASE_URL}/auth/login", json={"username": "quanly", "password": "QuanLy123#"})
    assert res_mgr.status_code == 200, f"Manager login failed: {res_mgr.text}"
    mgr_token = res_mgr.json()["token"]
    mgr_headers = {"Authorization": f"Bearer {mgr_token}"}

    res_lt = client.post(f"{BASE_URL}/auth/login", json={"username": "letan", "password": "LeTan123#"})
    assert res_lt.status_code == 200, f"Receptionist login failed: {res_lt.text}"
    lt_token = res_lt.json()["token"]
    lt_headers = {"Authorization": f"Bearer {lt_token}"}

    res_bp = client.post(f"{BASE_URL}/auth/login", json={"username": "buongphong", "password": "BuongPhong123#"})
    assert res_bp.status_code == 200, f"Housekeeping login failed: {res_bp.text}"
    bp_token = res_bp.json()["token"]
    bp_headers = {"Authorization": f"Bearer {bp_token}"}

    print_test("Dang nhap tai khoan quan ly, le tan, buong phong", True)

    # 2. Phan quyen: Khong token -> 401
    res = client.get(f"{BASE_URL}/reports/revenue")
    print_test("Khong token truy cap /reports/revenue tra ve 401", res.status_code == 401, f"Status: {res.status_code}")

    # 3. Phan quyen: Le tan va Buong phong -> 403
    res_lt_call = client.get(f"{BASE_URL}/reports/revenue", headers=lt_headers)
    print_test("Le tan truy cap /reports/revenue tra ve 403", res_lt_call.status_code == 403, f"Status: {res_lt_call.status_code}")

    res_bp_call = client.get(f"{BASE_URL}/reports/revenue", headers=bp_headers)
    print_test("Buong phong truy cap /reports/revenue tra ve 403", res_bp_call.status_code == 403, f"Status: {res_bp_call.status_code}")

    # 4. Kiem tra validation ngay thang
    res_inv_date = client.get(f"{BASE_URL}/reports/revenue?from=sai-dinh-dang&to=2026-11-30", headers=mgr_headers)
    print_test("Ngay bat dau sai dinh dang tra ve 422", res_inv_date.status_code == 422)

    res_inv_range = client.get(f"{BASE_URL}/reports/revenue?from=2026-11-30&to=2026-11-01", headers=mgr_headers)
    print_test("Khoang ngay dao nguoc tra ve 422", res_inv_range.status_code == 422)

    # 5. Bao cao doanh thu (JSON)
    res_rev = client.get(f"{BASE_URL}/reports/revenue?from=2026-11-01&to=2026-11-30&unit=NGAY", headers=mgr_headers)
    print_test("Quan ly lay bao cao doanh thu tra ve 200", res_rev.status_code == 200)
    rev_data = res_rev.json()
    assert rev_data["success"] is True
    assert "tongThu" in rev_data and "tongThucThu" in rev_data
    print_test("Du lieu doanh thu co tongThu va tongThucThu", True, f"Tong thuc thu: {rev_data['tongThucThu']:,.0f} VND")

    # Bao cao doanh thu theo thang
    res_rev_m = client.get(f"{BASE_URL}/reports/revenue?from=2026-01-01&to=2026-12-31&unit=THANG", headers=mgr_headers)
    print_test("Bao cao doanh thu theo thang tra ve 200", res_rev_m.status_code == 200 and res_rev_m.json()["donVi"] == "THANG")

    # Xuat Excel bao cao doanh thu
    res_rev_xlsx = client.get(f"{BASE_URL}/reports/revenue?from=2026-11-01&to=2026-11-30&format=xlsx", headers=mgr_headers)
    print_test("Xuat Excel bao cao doanh thu tra ve 200", res_rev_xlsx.status_code == 200)
    assert res_rev_xlsx.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert res_rev_xlsx.content[:4] == b"PK\x03\x04", "File Excel phai bat dau bang zip header PK\\x03\\x04"
    print_test("File Excel doanh thu hop le (chuan OpenXML)", True, f"Kich thuoc: {len(res_rev_xlsx.content)} bytes")

    # 6. Bao cao cong suat phong
    res_occ = client.get(f"{BASE_URL}/reports/occupancy?from=2026-11-01&to=2026-11-30", headers=mgr_headers)
    print_test("Quan ly lay bao cao cong suat tra ve 200", res_occ.status_code == 200)
    occ_data = res_occ.json()
    assert occ_data["success"] is True
    assert len(occ_data["data"]) > 0
    print_test("Bao cao cong suat co danh sach hang phong", True, f"Cong suat trung binh: {occ_data['congSuatTrungBinh']}%")

    # Xuat Excel bao cao cong suat
    res_occ_xlsx = client.get(f"{BASE_URL}/reports/occupancy?from=2026-11-01&to=2026-11-30&format=xlsx", headers=mgr_headers)
    print_test("Xuat Excel bao cao cong suat tra ve 200", res_occ_xlsx.status_code == 200 and res_occ_xlsx.content[:4] == b"PK\x03\x04")

    # 7. Bao cao ty le huy & no-show
    res_canc = client.get(f"{BASE_URL}/reports/cancellations?from=2026-11-01&to=2026-11-30", headers=mgr_headers)
    print_test("Quan ly lay bao cao ty le huy tra ve 200", res_canc.status_code == 200)
    canc_data = res_canc.json()
    assert canc_data["success"] is True
    assert "tongDon" in canc_data and "tyLeHuy" in canc_data
    print_test("Du lieu ty le huy, no-show, het han day du", True, 
               f"Tong don: {canc_data['tongDon']}, Huy: {canc_data['huy']} ({canc_data['tyLeHuy']}%), No-show: {canc_data['noShow']} ({canc_data['tyLeNoShow']}%)")

    # Xuat Excel bao cao ty le huy
    res_canc_xlsx = client.get(f"{BASE_URL}/reports/cancellations?from=2026-11-01&to=2026-11-30&format=xlsx", headers=mgr_headers)
    print_test("Xuat Excel bao cao ty le huy tra ve 200", res_canc_xlsx.status_code == 200 and res_canc_xlsx.content[:4] == b"PK\x03\x04")

    # 8. Bao cao KPI ADR va RevPAR
    res_kpi = client.get(f"{BASE_URL}/reports/kpi?from=2026-11-01&to=2026-11-30", headers=mgr_headers)
    print_test("Quan ly lay bao cao KPI ADR & RevPAR tra ve 200", res_kpi.status_code == 200)
    kpi_data = res_kpi.json()
    assert kpi_data["success"] is True
    assert "adrChung" in kpi_data and "revparChung" in kpi_data
    print_test("Chi so ADR va RevPAR hop le", True, 
               f"ADR chung: {kpi_data['adrChung']:,.0f} VND, RevPAR chung: {kpi_data['revparChung']:,.0f} VND")

    # Xuat Excel bao cao KPI
    res_kpi_xlsx = client.get(f"{BASE_URL}/reports/kpi?from=2026-11-01&to=2026-11-30&format=xlsx", headers=mgr_headers)
    print_test("Xuat Excel bao cao KPI tra ve 200", res_kpi_xlsx.status_code == 200 and res_kpi_xlsx.content[:4] == b"PK\x03\x04")

    print("\n=== TAT CA CAC TEST CHO F18 DA HOAN TAT XUAT SAC ===")

if __name__ == "__main__":
    run_tests()
