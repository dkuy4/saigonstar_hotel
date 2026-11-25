"""
Kịch bản kiểm thử tự động API F16.5: Quản lý Bản dịch chính sách và Mẫu email.
Sử dụng urllib.request để không phụ thuộc requests.
"""
import urllib.request
import urllib.error
import urllib.parse
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def request_json(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    body = None
    if data is not None:
        if isinstance(data, dict):
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif isinstance(data, (bytes, str)):
            body = data.encode("utf-8") if isinstance(data, str) else data

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            return response.status, json.loads(res_body) if res_body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(err_body)
        except Exception:
            return e.code, {"raw": err_body}

def login(username, password):
    payload = {"username": username, "password": password}
    status, data = request_json(f"{BASE_URL}/auth/login", method="POST", data=payload)
    assert status == 200, f"Login failed for {username}: {data}"
    return data.get("token") or data.get("access_token")

def test_f16_5():
    print("--- 1. Login accounts ---")
    token_manager = login("quanly", "QuanLy123#")
    token_receptionist = login("letan", "LeTan123#")
    headers_mgr = {"Authorization": f"Bearer {token_manager}"}
    headers_rec = {"Authorization": f"Bearer {token_receptionist}"}

    print("--- 2. Test 401 Unauthorized without token ---")
    status, data = request_json(f"{BASE_URL}/translations")
    assert status == 401, f"Expected 401, got {status}: {data}"
    print("✓ 401 checked for unauthenticated request")

    print("--- 3. Test 403 Forbidden for Receptionist (LE_TAN) ---")
    status, data = request_json(
        f"{BASE_URL}/translations/CHINH_SACH_HUY/en",
        method="PUT",
        data={"noiDung": "Updated policy"},
        headers=headers_rec,
    )
    assert status == 403, f"Expected 403, got {status}: {data}"
    print("✓ 403 checked for receptionist")

    print("--- 4. Test 422 VALIDATION_ERROR when Vietnamese text is empty (BR-55) ---")
    status, data = request_json(
        f"{BASE_URL}/translations/CHINH_SACH_HUY/vi",
        method="PUT",
        data={"noiDung": "   "},
        headers=headers_mgr,
    )
    assert status == 422, f"Expected 422, got {status}: {data}"
    assert data.get("code") == "VALIDATION_ERROR", f"Expected VALIDATION_ERROR, got {data}"
    assert "tiếng Việt" in data.get("detail", ""), f"Expected Vietnamese note in detail, got {data}"
    print("✓ 422 checked: Empty Vietnamese content rejected per BR-55")

    print("--- 5. Test 422 VALIDATION_ERROR when email template is missing required placeholder ---")
    # EMAIL_XAC_NHAN requires: {ma_don}, {ten_khach}, {ten_hang}, {thoi_gian_nhan}, {thoi_gian_tra}, {tong_tien}, {link_tra_cuu}
    invalid_template = "Kính gửi {ten_khach}, đơn {ten_hang} từ {thoi_gian_nhan} đến {thoi_gian_tra}, tổng {tong_tien}, link {link_tra_cuu}"
    # missing {ma_don}
    status, data = request_json(
        f"{BASE_URL}/translations/EMAIL_XAC_NHAN/en",
        method="PUT",
        data={"noiDung": invalid_template},
        headers=headers_mgr,
    )
    assert status == 422, f"Expected 422, got {status}: {data}"
    assert data.get("code") == "VALIDATION_ERROR", f"Expected VALIDATION_ERROR, got {data}"
    assert "{ma_don}" in data.get("detail", ""), f"Expected missing {{ma_don}} in detail: {data}"
    print(f"✓ 422 checked: Missing required template variable correctly caught ({data.get('detail')})")

    print("--- 6. Test valid update for Korean email template with warning flag ---")
    valid_ko_template = (
        "{ten_khach} 고객님께,\n\n"
        "사이공 스타 호텔입니다. 예약 번호 {ma_don}의 예약이 확정되었습니다.\n"
        "- 객실: {ten_hang}\n"
        "- 체크인: {thoi_gian_nhan}\n"
        "- 체크아웃: {thoi_gian_tra}\n"
        "- 총액: {tong_tien}\n\n"
        "예약 확인 링크: {link_tra_cuu}\n"
        "감사합니다."
    )
    status, update_data = request_json(
        f"{BASE_URL}/translations/EMAIL_XAC_NHAN/ko",
        method="PUT",
        data={"noiDung": valid_ko_template},
        headers=headers_mgr,
    )
    assert status == 200, f"Expected 200, got {status}: {update_data}"
    assert update_data["success"] is True
    assert update_data["maNoiDung"] == "EMAIL_XAC_NHAN"
    assert update_data["ngonNgu"] == "ko"
    assert update_data.get("canhBao") is not None, "Warning flag expected for non-primary language"
    print(f"✓ 200 checked: Korean email template updated with warning: {update_data.get('canhBao')}")

    print("--- 7. Test GET single translation ---")
    status, single_data = request_json(f"{BASE_URL}/translations/EMAIL_XAC_NHAN/ko")
    assert status == 200
    assert single_data["maNoiDung"] == "EMAIL_XAC_NHAN"
    assert single_data["ngonNgu"] == "ko"
    assert "{ma_don}" in single_data["noiDung"]
    print("✓ GET single translation verified")

    print("--- 8. Test GET all translation matrix items ---")
    status, matrix = request_json(f"{BASE_URL}/translations", headers=headers_mgr)
    assert status == 200
    assert len(matrix) >= 8, f"Expected at least 8 matrix items, got {len(matrix)}"
    for item in matrix:
        assert "maNoiDung" in item
        assert "loai" in item
        assert "tieuDe" in item
        assert "banDich" in item
        assert "chuaRa" in item
        assert item["chuaRa"]["vi"] is False
        assert item["chuaRa"]["en"] is False
        assert item["chuaRa"]["ko"] is True
        assert item["chuaRa"]["zh-CN"] is True
    print(f"✓ GET full translation matrix verified ({len(matrix)} items across 7 languages)")

    print("\nALL F16.5 AUTOMATED API TESTS PASSED 100%!")

if __name__ == "__main__":
    test_f16_5()
