import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import date
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
    print("=== BẮT ĐẦU KIỂM THỬ F12: THANH TOÁN TẠI QUẦY, HOÀN TIỀN & ĐỐI SOÁT ===")
    client = httpx.Client(timeout=10.0)

    # 1. Đăng nhập 2 tài khoản: Lễ tân (letan) và Quản lý (quanly)
    res_lt = client.post(f"{BASE_URL}/auth/login", json={"username": "letan", "password": "LeTan123#"})
    assert res_lt.status_code == 200, "Đăng nhập letan thất bại"
    lt_token = res_lt.json()["token"]
    lt_headers = {"Authorization": f"Bearer {lt_token}"}

    res_mgr = client.post(f"{BASE_URL}/auth/login", json={"username": "quanly", "password": "QuanLy123#"})
    assert res_mgr.status_code == 200, "Đăng nhập quanly thất bại"
    mgr_token = res_mgr.json()["token"]
    mgr_headers = {"Authorization": f"Bearer {mgr_token}"}

    print_test("1. Đăng nhập tài khoản letan và quanly thành công", True)

    # 2. Tìm hoặc chuẩn bị 1 đơn CONFIRMED để test thanh toán quầy và hoàn tiền
    pool = get_pool()
    target_booking_id = None
    target_booking_code = None

    with pool.acquire() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT dp.dat_phong_id, dp.ma_tra_cuu, dp.tong_tien
                  FROM hotel_owner.dat_phong dp
                 WHERE dp.trang_thai = 'CONFIRMED'
                 FETCH FIRST 1 ROWS ONLY
                """
            )
            row = cur.fetchone()
            if row:
                target_booking_id = row[0]
                target_booking_code = row[1]

    assert target_booking_id is not None, "Không tìm thấy đơn CONFIRMED để kiểm thử"
    print(f"   -> Sử dụng đơn đặt phòng id {target_booking_id} ({target_booking_code})")

    # 3. Thu tiền tại quầy bằng tiền mặt (POST /bookings/{id}/payments)
    res_pay1 = client.post(
        f"{BASE_URL}/bookings/{target_booking_id}/payments",
        headers=lt_headers,
        json={"method": "TIEN_MAT", "amount": 500000, "notes": "Khách đặt cọc thêm tiền mặt"}
    )
    print_test(
        "2. Thu tiền tại quầy bằng tiền mặt (TIEN_MAT)",
        res_pay1.status_code == 200 and res_pay1.json().get("method") == "TIEN_MAT",
        res_pay1.text
    )

    # 4. Thu tiền tại quầy bằng chuyển khoản (CHUYEN_KHOAN)
    res_pay2 = client.post(
        f"{BASE_URL}/bookings/{target_booking_id}/payments",
        headers=lt_headers,
        json={"method": "CHUYEN_KHOAN", "amount": 300000, "notes": "Khách chuyển khoản VietQR"}
    )
    print_test(
        "3. Thu tiền tại quầy bằng chuyển khoản (CHUYEN_KHOAN)",
        res_pay2.status_code == 200 and res_pay2.json().get("method") == "CHUYEN_KHOAN",
        res_pay2.text
    )

    # 5. Thu tiền bằng phương thức không hợp lệ -> Phải báo VALIDATION_ERROR (422/400)
    res_pay_invalid = client.post(
        f"{BASE_URL}/bookings/{target_booking_id}/payments",
        headers=lt_headers,
        json={"method": "BITCOIN", "amount": 100000}
    )
    print_test(
        "4. Phương thức thanh toán không hợp lệ bị từ chối",
        res_pay_invalid.status_code in (400, 422),
        f"Status: {res_pay_invalid.status_code}"
    )

    # 6. Kiểm tra validation: Hoàn tiền vượt số đã thu (REFUND_EXCEEDS_PAID) -> Phải báo 409
    res_refund_excess = client.post(
        f"{BASE_URL}/refunds",
        headers=lt_headers,
        json={"bookingId": target_booking_id, "amount": 999999999, "reason": "Thử hoàn vượt mức"}
    )
    print_test(
        "5. Hoàn tiền vượt quá số đã thanh toán báo 409 REFUND_EXCEEDS_PAID",
        res_refund_excess.status_code == 409 and "REFUND_EXCEEDS_PAID" in res_refund_excess.text,
        f"Status: {res_refund_excess.status_code}"
    )

    # 7. Lễ tân tạo yêu cầu hoàn tiền hợp lệ tại quầy (POST /refunds)
    res_refund_req = client.post(
        f"{BASE_URL}/refunds",
        headers=lt_headers,
        json={"bookingId": target_booking_id, "amount": 200000, "reason": "Khách trả phòng sớm 1 ngày"}
    )
    print_test(
        "6. Lễ tân đề xuất hoàn tiền -> Trạng thái CHO_DUYET",
        res_refund_req.status_code == 200 and res_refund_req.json().get("status") == "CHO_DUYET",
        res_refund_req.text
    )

    # Lấy danh sách hoàn tiền để lấy refundId vừa tạo
    res_refunds_list = client.get(
        f"{BASE_URL}/refunds?status=CHO_DUYET&bookingId={target_booking_id}",
        headers=lt_headers
    )
    assert res_refunds_list.status_code == 200, "Lấy danh sách hoàn tiền thất bại"
    refund_items = res_refunds_list.json().get("items", [])
    assert len(refund_items) > 0, "Không tìm thấy yêu cầu hoàn tiền vừa tạo"
    created_refund = refund_items[0]
    refund_id = created_refund["refundId"]
    print(f"   -> Refund ID vừa tạo: {refund_id}")

    # 8. RBAC: Lễ tân thử duyệt hoàn tiền -> Phải bị 403 Forbidden!
    res_lt_approve = client.post(
        f"{BASE_URL}/refunds/{refund_id}/approve",
        headers=lt_headers,
        json={"approved": True, "reason": "Lễ tân tự duyệt"}
    )
    print_test(
        "7. RBAC: Lễ tân không có quyền duyệt hoàn tiền (403 Forbidden)",
        res_lt_approve.status_code == 403,
        f"Status: {res_lt_approve.status_code}"
    )

    # 9. Quản lý duyệt yêu cầu hoàn tiền -> Chuyển sang DA_DUYET
    res_mgr_approve = client.post(
        f"{BASE_URL}/refunds/{refund_id}/approve",
        headers=mgr_headers,
        json={"approved": True, "reason": "Đồng ý hoàn tiền trả phòng sớm"}
    )
    print_test(
        "8. Quản lý phê duyệt hoàn tiền -> Trạng thái chuyển sang DA_DUYET",
        res_mgr_approve.status_code == 200 and res_mgr_approve.json().get("status") == "DA_DUYET",
        res_mgr_approve.text
    )

    # 10. Xác nhận đã chi tiền hoàn tại quầy (POST /refunds/{id}/complete) -> DA_HOAN
    res_complete = client.post(f"{BASE_URL}/refunds/{refund_id}/complete", headers=lt_headers)
    print_test(
        "9. Xác nhận đã chi tiền hoàn (POST /refunds/{id}/complete) -> Trạng thái DA_HOAN",
        res_complete.status_code == 200 and res_complete.json().get("status") == "DA_HOAN",
        res_complete.text
    )

    # 11. Thử xác nhận lại lần nữa khi đã DA_HOAN -> Phải báo 409 REFUND_STATE_INVALID
    res_complete_repeat = client.post(f"{BASE_URL}/refunds/{refund_id}/complete", headers=lt_headers)
    print_test(
        "10. Xác nhận chi tiền lại lần 2 báo 409 REFUND_STATE_INVALID",
        res_complete_repeat.status_code == 409 and "REFUND_STATE_INVALID" in res_complete_repeat.text,
        f"Status: {res_complete_repeat.status_code}"
    )

    # 12. Quản lý hoàn tiền ngoại lệ (POST /refunds/override, BR-26)
    res_override = client.post(
        f"{BASE_URL}/refunds/override",
        headers=mgr_headers,
        json={"bookingId": target_booking_id, "amount": 100000, "reason": "Khách VIP khiếu nại tiếng ồn hành lang"}
    )
    print_test(
        "11. Quản lý hoàn ngoại lệ ngoài chính sách (BR-26) -> Thành công DA_DUYET",
        res_override.status_code == 200 and res_override.json().get("status") == "DA_DUYET",
        res_override.text
    )

    # 13. Thử hoàn ngoại lệ KHÔNG có lý do -> Phải bị từ chối
    res_override_no_reason = client.post(
        f"{BASE_URL}/refunds/override",
        headers=mgr_headers,
        json={"bookingId": target_booking_id, "amount": 50000, "reason": "   "}
    )
    print_test(
        "12. Hoàn tiền ngoại lệ thiếu lý do bị từ chối (422/400)",
        res_override_no_reason.status_code in (400, 422),
        f"Status: {res_override_no_reason.status_code}"
    )

    # 14. Báo cáo đối soát doanh thu ngày (GET /reconciliation/daily, FR-39)
    today_str = date.today().strftime("%Y-%m-%d")
    res_recon = client.get(f"{BASE_URL}/reconciliation/daily?date={today_str}", headers=lt_headers)
    print_test(
        "13. Lấy báo cáo đối soát doanh thu ngày (GET /reconciliation/daily)",
        res_recon.status_code == 200,
        f"Số phương thức: {len(res_recon.json().get('items', []))}"
    )
    recon_data = res_recon.json()
    print(f"   -> Tổng thu: {recon_data.get('grandTotalCollected'):,.0f} VND")
    print(f"   -> Tổng hoàn: {recon_data.get('grandTotalRefunded'):,.0f} VND")
    print(f"   -> Thực thu ròng: {recon_data.get('grandNetRevenue'):,.0f} VND")

    # 15. Xuất báo cáo đối soát CSV (GET /reconciliation/daily/export)
    res_csv = client.get(f"{BASE_URL}/reconciliation/daily/export?date={today_str}", headers=lt_headers)
    print_test(
        "14. Xuất file CSV đối soát ngày thành công",
        res_csv.status_code == 200 and "text/csv" in res_csv.headers.get("content-type", ""),
        f"Kích thước file: {len(res_csv.content)} bytes"
    )

    print("\n=== TẤT CẢ 14/14 BƯỚC KIỂM THỬ BACKEND F12 ĐÃ VƯỢT QUA XUẤT SẮC! ===")

if __name__ == "__main__":
    main()
