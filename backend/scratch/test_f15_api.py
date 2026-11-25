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
    print("=== BẮT ĐẦU KIỂM THỬ F15: BUỒNG PHÒNG VÀ BẢO TRÌ ===")
    client = httpx.Client(timeout=10.0)

    # 1. Đăng nhập 3 tài khoản: Buồng phòng, Lễ tân, Quản lý
    res_bp = client.post(f"{BASE_URL}/auth/login", json={"username": "buongphong", "password": "BuongPhong123#"})
    assert res_bp.status_code == 200, "Đăng nhập buongphong thất bại"
    bp_token = res_bp.json()["token"]
    bp_headers = {"Authorization": f"Bearer {bp_token}"}

    res_lt = client.post(f"{BASE_URL}/auth/login", json={"username": "letan", "password": "LeTan123#"})
    assert res_lt.status_code == 200, "Đăng nhập letan thất bại"
    lt_token = res_lt.json()["token"]
    lt_headers = {"Authorization": f"Bearer {lt_token}"}

    res_mgr = client.post(f"{BASE_URL}/auth/login", json={"username": "quanly", "password": "QuanLy123#"})
    assert res_mgr.status_code == 200, "Đăng nhập quanly thất bại"
    mgr_token = res_mgr.json()["token"]
    mgr_headers = {"Authorization": f"Bearer {mgr_token}"}

    print_test("1. Đăng nhập buongphong, letan, quanly thành công", True)

    # 2. Kiểm tra RBAC: buongphong không được gọi bảo trì phòng (403 Forbidden)
    res_rb = client.post(
        f"{BASE_URL}/rooms/1/maintenance",
        headers=bp_headers,
        json={"reason": "Test RBAC"}
    )
    print_test("2. RBAC: Buồng phòng gọi /rooms/{id}/maintenance bị 403 Forbidden", res_rb.status_code == 403, f"Status: {res_rb.status_code}")

    # 3. Lấy danh sách nhiệm vụ buồng phòng (GET /housekeeping/tasks)
    res_tasks = client.get(f"{BASE_URL}/housekeeping/tasks?status=ALL", headers=bp_headers)
    print_test("3. Buồng phòng truy cập GET /housekeeping/tasks?status=ALL thành công", res_tasks.status_code == 200)
    tasks_data = res_tasks.json()
    items = tasks_data.get("items", [])
    print(f"   -> Tổng số phòng lấy được: {len(items)}")

    # 4. Kiểm tra nguyên tắc bảo mật thông tin khách hàng AC-16 & FR-25
    forbidden_keys = [
        "ho_ten", "hoten", "customer_name", "customername", "customer",
        "sdt", "phone", "customer_phone", "customerphone",
        "email", "customer_email", "customeremail",
        "tien_phong", "price", "tong_tien", "totalamount", "amount",
        "khach_hang_id", "khachhangid", "customerid"
    ]
    privacy_violation = False
    violating_key = ""
    for it in items:
        for k in it.keys():
            if k.lower() in forbidden_keys:
                privacy_violation = True
                violating_key = k
                break
        if privacy_violation:
            break

    print_test(
        "4. AC-16 & FR-25: Tuyệt đối không chứa thông tin khách hàng hoặc giá tiền",
        not privacy_violation,
        f"Vi phạm: {violating_key}" if privacy_violation else "Hoàn toàn sạch thông tin nhạy cảm"
    )

    # 5. Chuẩn bị phòng thử nghiệm dọn dẹp
    # Lấy 1 phòng đang trống để chuyển sang DANG_DON
    pool = get_pool()
    test_room_id = None
    test_room_number = None
    with pool.acquire() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT phong_id, ma_phong FROM hotel_owner.phong WHERE trang_thai = 'TRONG' AND dang_hoat_dong = 1 FETCH FIRST 1 ROWS ONLY")
            row = cur.fetchone()
            assert row is not None, "Không tìm thấy phòng trống để test"
            test_room_id = row[0]
            test_room_number = row[1]
            # Đưa phòng về DANG_DON để kiểm thử quy trình dọn
            cur.execute("UPDATE hotel_owner.phong SET trang_thai = 'DANG_DON' WHERE phong_id = :1", [test_room_id])
            conn.commit()

    print(f"   -> Sử dụng phòng id {test_room_id} ({test_room_number}) cho kiểm thử dọn phòng")

    # 6. Bắt đầu dọn phòng: POST /housekeeping/{id}/start (FR-24, US-16)
    res_start = client.post(f"{BASE_URL}/housekeeping/{test_room_id}/start", headers=bp_headers)
    print_test(
        "5. Buồng phòng bắt đầu dọn (POST /housekeeping/{id}/start)",
        res_start.status_code == 200 and res_start.json().get("status") == "DANG_DON",
        res_start.text
    )

    # Kiểm tra nhật ký kiểm toán có hành động BAT_DAU_DON không
    with pool.acquire() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) FROM hotel_owner.nhat_ky_kiem_toan
                 WHERE bang = 'PHONG' AND khoa_dong = :1 AND hanh_dong = 'BAT_DAU_DON'
                """,
                [str(test_room_id)]
            )
            audit_count = cur.fetchone()[0]
    print_test("6. Nhật ký kiểm toán đã ghi nhận hành động BAT_DAU_DON", audit_count > 0, f"Count: {audit_count}")

    # 7. Dọn xong phòng: POST /housekeeping/{id}/done (FR-24, US-16)
    res_done = client.post(f"{BASE_URL}/housekeeping/{test_room_id}/done", headers=bp_headers)
    print_test(
        "7. Buồng phòng dọn xong (POST /housekeeping/{id}/done) -> Phòng về TRONG",
        res_done.status_code == 200 and res_done.json().get("status") == "TRONG",
        res_done.text
    )

    # 8. Gọi dọn xong lần nữa khi phòng đã TRONG -> Phải báo lỗi ROOM_STATE_INVALID (409)
    res_invalid_done = client.post(f"{BASE_URL}/housekeeping/{test_room_id}/done", headers=bp_headers)
    print_test(
        "8. Gọi dọn xong khi phòng không ở trạng thái DANG_DON báo 409 ROOM_STATE_INVALID",
        res_invalid_done.status_code == 409 and "ROOM_STATE_INVALID" in res_invalid_done.text,
        f"Status: {res_invalid_done.status_code}"
    )

    # 9. Kiểm thử Lễ tân & Quản lý: Đưa phòng vào bảo trì (F15, BR-40, BR-41)
    # 9.1 Kiểm tra phòng có đơn tương lai
    with pool.acquire() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT d.phong_id, p.ma_phong
                  FROM hotel_owner.dat_phong_doan d
                  JOIN hotel_owner.dat_phong dp ON dp.dat_phong_id = d.dat_phong_id
                  JOIN hotel_owner.phong p ON p.phong_id = d.phong_id
                 WHERE d.den_luc > SYSTIMESTAMP
                   AND dp.trang_thai IN ('CONFIRMED', 'CHECKED_IN')
                 FETCH FIRST 1 ROWS ONLY
                """
            )
            booked_row = cur.fetchone()

    if booked_row:
        booked_room_id, booked_room_num = booked_row
        print(f"   -> Phòng có đơn tương lai: {booked_room_num} (id: {booked_room_id})")

        # Gọi xem danh sách đơn ảnh hưởng
        res_aff = client.get(f"{BASE_URL}/rooms/{booked_room_id}/affected-bookings", headers=lt_headers)
        print_test(
            "9. Lễ tân lấy danh sách đơn ảnh hưởng (GET /rooms/{id}/affected-bookings)",
            res_aff.status_code == 200 and len(res_aff.json()) > 0,
            f"Số đơn ảnh hưởng: {len(res_aff.json()) if res_aff.status_code == 200 else 0}"
        )

        # Gọi bảo trì KHÔNG bỏ qua đơn ảnh hưởng -> Phải trả về 409 MAINTENANCE_HAS_BOOKINGS
        res_maint_conflict = client.post(
            f"{BASE_URL}/rooms/{booked_room_id}/maintenance",
            headers=lt_headers,
            json={"reason": "Sơn lại tường phòng", "ignoreAffectedBookings": False}
        )
        print_test(
            "10. Đưa phòng có đơn tương lai vào bảo trì chưa xác nhận trả về 409 MAINTENANCE_HAS_BOOKINGS",
            res_maint_conflict.status_code == 409 and "MAINTENANCE_HAS_BOOKINGS" in res_maint_conflict.text,
            f"Status: {res_maint_conflict.status_code}"
        )

    # 9.2 Bảo trì phòng trống không có đơn tương lai (test_room_id hiện đang TRONG)
    res_maint = client.post(
        f"{BASE_URL}/rooms/{test_room_id}/maintenance",
        headers=lt_headers,
        json={"reason": "Thay bóng đèn chùm phòng ngủ", "ignoreAffectedBookings": False}
    )
    print_test(
        "11. Lễ tân đưa phòng trống vào bảo trì (POST /rooms/{id}/maintenance)",
        res_maint.status_code == 200 and res_maint.json().get("status") == "BAO_TRI",
        res_maint.text
    )

    # Kiểm tra trạng thái trong DB và ghi chú
    with pool.acquire() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT trang_thai, ghi_chu FROM hotel_owner.phong WHERE phong_id = :1", [test_room_id])
            st, gc = cur.fetchone()
    print_test(
        "12. Kiểm tra DB: Phòng chuyển sang BAO_TRI và ghi nhận lý do vào ghi chú",
        st == "BAO_TRI" and "Thay bóng đèn" in gc,
        f"Trạng thái: {st}, Ghi chú: {gc}"
    )

    # 9.3 Đưa phòng đã BAO_TRI vào bảo trì tiếp -> Phải báo 409 ROOM_STATE_INVALID
    res_maint_repeat = client.post(
        f"{BASE_URL}/rooms/{test_room_id}/maintenance",
        headers=lt_headers,
        json={"reason": "Bảo trì thêm lần nữa"}
    )
    print_test(
        "13. Đưa phòng đang BAO_TRI vào bảo trì lần 2 báo 409 ROOM_STATE_INVALID",
        res_maint_repeat.status_code == 409 and "ROOM_STATE_INVALID" in res_maint_repeat.text,
        f"Status: {res_maint_repeat.status_code}"
    )

    # 9.4 Kết thúc bảo trì: POST /rooms/{id}/end-maintenance
    res_end_maint = client.post(f"{BASE_URL}/rooms/{test_room_id}/end-maintenance", headers=mgr_headers)
    print_test(
        "14. Quản lý kết thúc bảo trì (POST /rooms/{id}/end-maintenance) -> Phòng về TRONG",
        res_end_maint.status_code == 200 and res_end_maint.json().get("status") == "TRONG",
        res_end_maint.text
    )

    # 9.5 Kết thúc bảo trì lần nữa khi phòng đã TRONG -> Phải báo 409 ROOM_STATE_INVALID
    res_end_repeat = client.post(f"{BASE_URL}/rooms/{test_room_id}/end-maintenance", headers=mgr_headers)
    print_test(
        "15. Kết thúc bảo trì khi phòng không ở trạng thái BAO_TRI báo 409 ROOM_STATE_INVALID",
        res_end_repeat.status_code == 409 and "ROOM_STATE_INVALID" in res_end_repeat.text,
        f"Status: {res_end_repeat.status_code}"
    )

    print("\n=== TẤT CẢ 15/15 BƯỚC KIỂM THỬ BACKEND F15 ĐÃ VƯỢT QUA XUẤT SẮC! ===")

if __name__ == "__main__":
    main()
