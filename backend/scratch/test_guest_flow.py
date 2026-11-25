import sys
import time
import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_guest_workflow():
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)
    ts = int(time.time())
    email = f"guest_{ts}@testmail.com"
    phone = f"09{ts % 100000000:08d}"
    name = "Nguyễn Hoàng Nam"
    pwd = "GuestPassword123#"
    
    print("\n=== BẮT ĐẦU KIỂM THỬ LUỒNG KHÁCH HÀNG & ĐỒNG BỘ ADMIN ===")
    
    # 1. Đăng ký tài khoản
    print("1. Kiểm tra Đăng ký tài khoản khách hàng...")
    res = client.post("/guest/register", json={
        "ho_ten": name,
        "sdt": phone,
        "email": email,
        "mat_khau": pwd,
        "quoc_tich": "VNM",
        "ngon_ngu": "vi"
    })
    assert res.status_code == 201, f"Register failed: {res.text}"
    reg_data = res.json()
    token = reg_data["access_token"]
    assert reg_data["user"]["ho_ten"] == name
    print(f"PASS: Đăng ký thành công! ID: {reg_data['user']['khach_hang_id']}, Token: {token[:15]}...")
    
    # 2. Đăng nhập
    print("2. Kiểm tra Đăng nhập tài khoản bằng Email...")
    res_login = client.post("/guest/login", json={
        "tai_khoan": email,
        "mat_khau": pwd
    })
    assert res_login.status_code == 200, f"Login failed: {res_login.text}"
    print("PASS: Đăng nhập bằng Email thành công!")

    print("2b. Kiểm tra Đăng nhập tài khoản bằng Số điện thoại...")
    res_login_phone = client.post("/guest/login", json={
        "tai_khoan": phone,
        "mat_khau": pwd
    })
    assert res_login_phone.status_code == 200, f"Login by phone failed: {res_login_phone.text}"
    print("PASS: Đăng nhập bằng Số điện thoại thành công!")

    # 3. Quên mật khẩu
    print("3. Kiểm tra Quên mật khẩu (xác minh thông tin không OTP)...")
    new_pwd = "NewPassword456#"
    res_forgot = client.post("/guest/forgot-password", json={
        "email": email,
        "sdt": phone,
        "ho_ten": name,
        "mat_khau_moi": new_pwd
    })
    assert res_forgot.status_code == 200, f"Forgot password failed: {res_forgot.text}"
    print(f"PASS: {res_forgot.json()['message']}")

    # Đăng nhập lại với mật khẩu mới
    res_relogin = client.post("/guest/login", json={
        "tai_khoan": email,
        "mat_khau": new_pwd
    })
    assert res_relogin.status_code == 200, "Re-login with new password failed"
    token = res_relogin.json()["access_token"]
    print("PASS: Đăng nhập lại với mật khẩu mới thành công!")

    # 4. Tạo đơn đặt phòng
    print("4. Khách tạo đơn đặt phòng...")
    # Lấy ngày tương lai năm 2031
    tu_luc = "2031-10-10T14:00:00+07:00"
    den_luc = "2031-10-12T12:00:00+07:00"
    res_booking = client.post("/bookings", json={
        "loaiDat": "NGAY",
        "maHang": "STANDARD",
        "nhanLuc": tu_luc,
        "traLuc": den_luc,
        "soKhach": 2,
        "thanhToan": "TRUC_TUYEN",
        "ngonNgu": "vi",
        "dongYChinhSach": True,
        "customer": {
            "fullName": name,
            "phone": phone,
            "email": email,
            "nationality": "VN"
        }
    })
    assert res_booking.status_code == 201, f"Booking failed: {res_booking.text}"
    booking_data = res_booking.json()
    code = booking_data["booking_code"]
    booking_id = booking_data["id"]
    print(f"PASS: Đơn phòng tạo thành công! Mã: {code}, Trạng thái: {booking_data['status']}")

    # 5. Kiểm tra danh sách 'Chuyến đi của tôi'
    print("5. Kiểm tra API /guest/my-bookings...")
    res_my = client.get("/guest/my-bookings", headers={"Authorization": f"Bearer {token}"})
    assert res_my.status_code == 200, f"My bookings failed: {res_my.text}"
    my_bookings = res_my.json()
    assert any(b["ma_tra_cuu"] == code for b in my_bookings), "Booking not found in guest's my-bookings list!"
    print(f"PASS: Đơn {code} đã xuất hiện trong danh sách chuyến đi của khách!")

    # 6. Đồng bộ Admin: Lễ tân đăng nhập và xem đơn
    print("6. Kiểm tra Đồng bộ Admin: Nhân viên xem đơn của khách...")
    res_staff_login = client.post("/auth/login", json={"username": "letan", "password": "LeTan123#"})
    assert res_staff_login.status_code == 200, f"Staff login failed: {res_staff_login.text}"
    staff_token = res_staff_login.json()["token"]

    res_staff_search = client.get(f"/bookings?q={code}", headers={"Authorization": f"Bearer {staff_token}"})
    assert res_staff_search.status_code == 200
    items = res_staff_search.json()["items"]
    assert len(items) > 0 and (items[0].get("bookingCode") == code or items[0].get("booking_code") == code)
    print(f"PASS: Nhân viên lễ tân tìm thấy đơn {code} của khách ngay lập tức trên hệ thống (Sơ đồ phòng / Quản lý đơn)!")

    print("\n=== TOÀN BỘ KIỂM THỬ KHÁCH HÀNG & ĐỒNG BỘ ADMIN ĐÃ ĐẠT 100%! ===")

if __name__ == "__main__":
    test_guest_workflow()
