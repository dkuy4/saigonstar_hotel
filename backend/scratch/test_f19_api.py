import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx
import oracledb
from app.db import get_pool

BASE_URL = "http://127.0.0.1:8000/api/v1"


def print_test(name: str, passed: bool, extra: str = ""):
    status_str = "[PASS]" if passed else "[FAIL]"
    print(f"{status_str} {name}" + (f" - {extra}" if extra else ""))
    if not passed:
        raise AssertionError(f"Test failed: {name} - {extra}")


def main():
    print("=== BẮT ĐẦU KIỂM THỬ F19: NHẬT KÝ KIỂM TOÁN (AUDIT LOGS) ===")
    client = httpx.Client(timeout=10.0)

    # 1. Đăng nhập 3 vai trò
    res_mgr = client.post(f"{BASE_URL}/auth/login", json={"username": "quanly", "password": "QuanLy123#"})
    assert res_mgr.status_code == 200, "Đăng nhập quanly thất bại"
    mgr_token = res_mgr.json()["token"]
    mgr_headers = {"Authorization": f"Bearer {mgr_token}"}

    res_lt = client.post(f"{BASE_URL}/auth/login", json={"username": "letan", "password": "LeTan123#"})
    assert res_lt.status_code == 200, "Đăng nhập letan thất bại"
    lt_token = res_lt.json()["token"]
    lt_headers = {"Authorization": f"Bearer {lt_token}"}

    res_bp = client.post(f"{BASE_URL}/auth/login", json={"username": "buongphong", "password": "BuongPhong123#"})
    assert res_bp.status_code == 200, "Đăng nhập buongphong thất bại"
    bp_token = res_bp.json()["token"]
    bp_headers = {"Authorization": f"Bearer {bp_token}"}

    print_test("Đăng nhập tài khoản Quản lý, Lễ tân, Buồng phòng", True)

    # 2. Phân quyền: Không token -> 401
    res_no_auth = client.get(f"{BASE_URL}/audit-logs")
    print_test("Không token truy cập /audit-logs trả về 401", res_no_auth.status_code == 401, f"Status: {res_no_auth.status_code}")

    res_no_auth_state = client.get(f"{BASE_URL}/audit-logs/state-at?bang=PHONG&khoaDong=1&thoiDiem=2026-11-24T00:00:00")
    print_test("Không token truy cập /audit-logs/state-at trả về 401", res_no_auth_state.status_code == 401, f"Status: {res_no_auth_state.status_code}")

    # 3. Phân quyền: Lễ tân & Buồng phòng -> 403
    res_lt_call = client.get(f"{BASE_URL}/audit-logs", headers=lt_headers)
    print_test("Lễ tân truy cập /audit-logs trả về 403", res_lt_call.status_code == 403, f"Status: {res_lt_call.status_code}")

    res_bp_call = client.get(f"{BASE_URL}/audit-logs", headers=bp_headers)
    print_test("Buồng phòng truy cập /audit-logs trả về 403", res_bp_call.status_code == 403, f"Status: {res_bp_call.status_code}")

    # 4. Quản lý lấy danh sách nhật ký kiểm toán -> 200 OK
    res_logs = client.get(f"{BASE_URL}/audit-logs?page=1&pageSize=10", headers=mgr_headers)
    print_test("Quản lý lấy danh sách nhật ký trả về 200", res_logs.status_code == 200, f"Status: {res_logs.status_code}")
    data_logs = res_logs.json()
    assert data_logs["success"] is True
    assert data_logs["total"] > 0
    assert len(data_logs["items"]) <= 10
    assert len(data_logs["tables"]) > 0
    print_test(
        "Dữ liệu nhật ký có phân trang và metadata",
        True,
        f"Tổng số dòng: {data_logs['total']}, Danh sách bảng: {data_logs['tables']}"
    )

    # 5. Kiểm tra chi tiết trường trong từng dòng nhật ký
    first_item = data_logs["items"][0]
    expected_fields = ["nhatKyId", "bang", "khoaDong", "hanhDong", "thoiDiem", "vaiTro", "kenh"]
    all_fields_present = all(field in first_item for field in expected_fields)
    print_test(
        "Cấu trúc dòng nhật ký chuẩn (ID, Bảng, Khóa dòng, Hành động, Thời điểm, Vai trò, Kênh)",
        all_fields_present,
        f"Mẫu dòng ID {first_item['nhatKyId']}: Bảng {first_item['bang']} ({first_item['hanhDong']}) bởi {first_item.get('tenDangNhap') or first_item['vaiTro']}"
    )

    # 6. Lọc theo bảng DAT_PHONG
    res_dp = client.get(f"{BASE_URL}/audit-logs?bang=DAT_PHONG&pageSize=5", headers=mgr_headers)
    assert res_dp.status_code == 200
    dp_items = res_dp.json()["items"]
    dp_filtered_ok = all(item["bang"] == "DAT_PHONG" for item in dp_items)
    print_test("Lọc nhật ký theo bảng DAT_PHONG", dp_filtered_ok, f"Số dòng: {len(dp_items)}")

    # 7. Lọc theo bảng PHONG
    res_phong = client.get(f"{BASE_URL}/audit-logs?bang=PHONG&pageSize=5", headers=mgr_headers)
    assert res_phong.status_code == 200
    phong_items = res_phong.json()["items"]
    phong_filtered_ok = all(item["bang"] == "PHONG" for item in phong_items)
    print_test("Lọc nhật ký theo bảng PHONG", phong_filtered_ok, f"Số dòng: {len(phong_items)}")

    # 8. Kiểm tra API State-At (Tái hiện trạng thái quá khứ)
    # Lấy một dòng nhật ký có sẵn để test
    test_log = phong_items[0] if phong_items else first_item
    test_bang = test_log["bang"]
    test_khoa = test_log["khoaDong"]
    target_time_iso = test_log["thoiDiem"]

    res_state = client.get(
        f"{BASE_URL}/audit-logs/state-at?bang={test_bang}&khoaDong={test_khoa}&thoiDiem={target_time_iso}",
        headers=mgr_headers
    )
    print("res_state:", res_state.json())
    print_test("Truy vấn trạng thái tại thời điểm state-at trả về 200", res_state.status_code == 200)
    state_data = res_state.json()
    assert state_data["success"] is True
    assert state_data["found"] is True
    print_test(
        "Tái hiện trạng thái quá khứ thành công",
        state_data["found"] is True and (state_data["state"] is not None or state_data["action"] == "XOA"),
        f"Bảng {test_bang} ID {test_khoa} tại {target_time_iso}"
    )

    # 9. State-at với mốc thời gian quá khứ xa (trước khi tạo) -> found: False
    res_state_past = client.get(
        f"{BASE_URL}/audit-logs/state-at?bang={test_bang}&khoaDong={test_khoa}&thoiDiem=2000-01-01T00:00:00",
        headers=mgr_headers
    )
    assert res_state_past.status_code == 200
    assert res_state_past.json()["found"] is False
    print_test("State-at trước khi bản ghi được tạo trả về found = False", True)

    # 10. AC-14: Kiểm tra tính bất biến (AUDIT_IMMUTABLE) trực tiếp qua Oracle
    pool = get_pool()
    with pool.acquire() as conn:
        with conn.cursor() as cur:
            cur.execute("ALTER SESSION SET CURRENT_SCHEMA = HOTEL_OWNER")

            # Thử UPDATE -> Phải bị chặn (bởi GRANT thiếu UPDATE hoặc TRIGGER AUDIT_IMMUTABLE)
            update_blocked = False
            try:
                cur.execute("UPDATE NHAT_KY_KIEM_TOAN SET LY_DO = 'hack' WHERE ROWNUM = 1")
                conn.commit()
            except oracledb.DatabaseError as ex:
                err_obj, = ex.args
                msg = str(err_obj.message).lower()
                if "audit_immutable" in msg or "update privilege" in msg or "insufficient privileges" in msg or err_obj.code in (20030, 41900, 1031):
                    update_blocked = True
            print_test("AC-14: Hành vi sửa nhật ký bị từ chối (Privilege / AUDIT_IMMUTABLE)", update_blocked)

            # Thử DELETE -> Phải bị chặn
            delete_blocked = False
            try:
                cur.execute("DELETE FROM NHAT_KY_KIEM_TOAN WHERE ROWNUM = 1")
                conn.commit()
            except oracledb.DatabaseError as ex:
                err_obj, = ex.args
                msg = str(err_obj.message).lower()
                if "audit_immutable" in msg or "delete privilege" in msg or "insufficient privileges" in msg or err_obj.code in (20030, 41900, 1031):
                    delete_blocked = True
            print_test("AC-14: Hành vi xóa nhật ký bị từ chối (Privilege / AUDIT_IMMUTABLE)", delete_blocked)

            # Kiểm tra không chứa mật khẩu băm
            cur.execute("SELECT COUNT(*) FROM NHAT_KY_KIEM_TOAN WHERE BANG = 'NGUOI_DUNG' AND GIA_TRI_MOI LIKE '%mat_khau_bam%'")
            count_pw = cur.fetchone()[0]
            print_test("AC-14: Nhật ký kiểm toán tuyệt đối không chứa mật khẩu băm", count_pw == 0, f"Số bản ghi vi phạm: {count_pw}")

    print("\n=== TẤT CẢ CÁC BÀI KIỂM THỬ F19 ĐÃ HOÀN TẤT VÀ VƯỢT QUA 100% ===")


if __name__ == "__main__":
    main()
