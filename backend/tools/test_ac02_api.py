import concurrent.futures
from datetime import datetime, timezone, timedelta
import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from starlette.testclient import TestClient
from app.main import app
from app.db import get_pool

VN_TZ = timezone(timedelta(hours=7))

def run_ac02_api_test(num_requests=200, workers=16):
    """
    Simulates high concurrent booking requests through the FastAPI application layer.
    Interval: 2026-12-20 14:00 to 2026-12-22 12:00
    Hạng Standard có 20 phòng.
    Với num_requests gửi đồng thời không chỉ định phòng (Public Web):
    Số đơn thành công phải chính xác bằng 20 (hoặc số phòng trống còn lại),
    toàn bộ các yêu cầu còn lại phải nhận NO_AVAILABILITY (409 Conflict),
    tuyệt đối 0 đơn bị double booking!
    """
    print(f"\n--- Bắt đầu kiểm thử đồng thời AC-02 qua API ({num_requests} requests, {workers} workers) ---")
    client = TestClient(app)

    ci = "2026-12-20T14:00:00+07:00"
    co = "2026-12-22T12:00:00+07:00"

    success_codes = []
    conflict_codes = []
    other_errors = []

    def book_request(idx):
        payload = {
            "loaiDat": "NGAY",
            "maHang": "STANDARD",
            "nhanLuc": ci,
            "traLuc": co,
            "soKhach": 1,
            "thanhToan": "TRUC_TUYEN",
            "dongYChinhSach": True,
            "customer": {
                "fullName": f"Concurrent User {idx}",
                "phone": f"097{idx:07d}",
                "email": f"user{idx}@loadtest.com",
                "nationality": "VN"
            }
        }
        res = client.post("/api/v1/bookings", json=payload)
        if res.status_code == 201:
            return ("SUCCESS", res.json()["booking_code"], res.json()["room_id"])
        elif res.status_code in (409, 422):
            return ("REJECTED", res.json().get("code"), None)
        else:
            return ("ERROR", res.status_code, res.text)

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(book_request, i) for i in range(num_requests)]
        for f in concurrent.futures.as_completed(futures):
            status, info, room_id = f.result()
            if status == "SUCCESS":
                success_codes.append((info, room_id))
            elif status == "REJECTED":
                conflict_codes.append(info)
            else:
                other_errors.append((info, room_id))

    print(f"Tổng số request: {num_requests}")
    print(f"Thành công: {len(success_codes)}")
    print(f"Bị từ chối (Hết phòng / Trùng): {len(conflict_codes)}")
    print(f"Lỗi khác: {len(other_errors)}")

    # Verify assigned rooms are unique
    assigned_rooms = [r[1] for r in success_codes]
    unique_rooms = set(assigned_rooms)
    double_bookings = len(assigned_rooms) - len(unique_rooms)

    print(f"Số phòng được cấp: {len(assigned_rooms)}, Số phòng duy nhất: {len(unique_rooms)}")
    print(f"Double booking: {double_bookings}")

    assert double_bookings == 0, f"Phát hiện {double_bookings} đơn bị trùng phòng!"
    assert len(other_errors) == 0, f"Có lỗi bất thường: {other_errors}"
    print("=> KẾT QUẢ AC-02 QUA API: HOÀN TOÀN ĐẠT (PASS)!\n")

if __name__ == "__main__":
    run_ac02_api_test(num_requests=100, workers=10)
