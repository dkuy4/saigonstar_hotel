import uuid
import random
from datetime import datetime, timezone, timedelta
import pytest
from starlette.testclient import TestClient
from app.main import app
from app.security import create_access_token

client = TestClient(app)

def get_receptionist_headers():
    token = create_access_token(data={"sub": "1", "username": "letan", "role": "LE_TAN"})
    return {"Authorization": f"Bearer {token}"}

def random_phone():
    return f"091{random.randint(1000000, 9999999)}"

def test_create_daily_booking_web_online_hold():
    uid = uuid.uuid4().hex[:6]
    m = random.randint(1, 12)
    d = random.randint(1, 25)
    payload = {
        "loaiDat": "NGAY",
        "maHang": "STANDARD",
        "nhanLuc": f"2028-{m:02d}-{d:02d}T14:00:00+07:00",
        "traLuc": f"2028-{m:02d}-{d+2:02d}T12:00:00+07:00",
        "soKhach": 2,
        "thanhToan": "TRUC_TUYEN",
        "dongYChinhSach": True,
        "customer": {
            "fullName": f"Test Guest {uid}",
            "phone": random_phone(),
            "email": f"guest_{uid}@test.com",
            "nationality": "VN"
        }
    }
    response = client.post("/api/v1/bookings", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "HOLD"
    assert data["booking_code"].startswith("DP")
    assert data["hold_expires_at"] is not None
    assert data["channel"] == "WEB"
    assert data["total_amount"] == 1188000.0  # 2 nights Standard: 1.100.000 + 88.000 VAT

    # Verify lookup by booking_code
    code = data["booking_code"]
    res_get = client.get(f"/api/v1/bookings/{code}")
    assert res_get.status_code == 200
    assert res_get.json()["booking_code"] == code

def test_create_daily_booking_must_agree_terms():
    uid = uuid.uuid4().hex[:6]
    payload = {
        "loaiDat": "NGAY",
        "maHang": "STANDARD",
        "nhanLuc": "2028-01-15T14:00:00+07:00",
        "traLuc": "2028-01-17T12:00:00+07:00",
        "soKhach": 2,
        "thanhToan": "TRUC_TUYEN",
        "dongYChinhSach": False,  # Did not agree
        "customer": {
            "fullName": f"Disagree Guest {uid}",
            "phone": random_phone(),
            "email": f"disagree_{uid}@test.com",
            "nationality": "VN"
        }
    }
    response = client.post("/api/v1/bookings", json=payload)
    assert response.status_code == 422
    err = response.json()
    assert err["code"] == "VALIDATION_ERROR"

def test_hourly_booking_creation_and_rejection():
    uid = uuid.uuid4().hex[:6]
    m = random.randint(1, 12)
    d = random.randint(1, 25)
    # Standard 3 hours -> 259.200 VND
    payload_std = {
        "loaiDat": "GIO",
        "maHang": "STANDARD",
        "nhanLuc": f"2028-{m:02d}-{d:02d}T10:00:00+07:00",
        "traLuc": f"2028-{m:02d}-{d:02d}T13:00:00+07:00",
        "soKhach": 1,
        "thanhToan": "TRUC_TUYEN",
        "dongYChinhSach": True,
        "customer": {
            "fullName": f"Hourly Guest {uid}",
            "phone": random_phone(),
            "email": f"hourly_{uid}@test.com",
            "nationality": "VN"
        }
    }
    r_std = client.post("/api/v1/bookings", json=payload_std)
    assert r_std.status_code == 201
    assert r_std.json()["total_amount"] == 259200.0

    # Hourly on Superior -> 422 HOURLY_NOT_ALLOWED (AC-05)
    payload_sup = dict(payload_std, maHang="SUPERIOR")
    r_sup = client.post("/api/v1/bookings", json=payload_sup)
    assert r_sup.status_code == 422
    assert r_sup.json()["code"] == "HOURLY_NOT_ALLOWED"

def test_ac01_concurrent_booking_same_room_one_wins():
    headers = get_receptionist_headers()
    uid = uuid.uuid4().hex[:6]
    m = random.randint(1, 12)
    d = random.randint(1, 20)
    ci = f"2029-{m:02d}-{d:02d}T14:00:00+07:00"
    co = f"2029-{m:02d}-{d+2:02d}T12:00:00+07:00"

    payload1 = {
        "loaiDat": "NGAY",
        "maHang": "STANDARD",
        "phongId": 1,
        "nhanLuc": ci,
        "traLuc": co,
        "soKhach": 2,
        "thanhToan": "KHI_NHAN_PHONG",
        "dongYChinhSach": True,
        "customer": {
            "fullName": f"Concurrent Guest 1 {uid}",
            "phone": random_phone(),
            "email": f"c1_{uid}@test.com",
            "nationality": "VN"
        }
    }
    payload2 = {
        "loaiDat": "NGAY",
        "maHang": "STANDARD",
        "phongId": 1,
        "nhanLuc": ci,
        "traLuc": co,
        "soKhach": 2,
        "thanhToan": "KHI_NHAN_PHONG",
        "dongYChinhSach": True,
        "customer": {
            "fullName": f"Concurrent Guest 2 {uid}",
            "phone": random_phone(),
            "email": f"c2_{uid}@test.com",
            "nationality": "VN"
        }
    }

    # First request succeeds
    r1 = client.post("/api/v1/bookings", json=payload1, headers=headers)
    assert r1.status_code == 201

    # Second request conflicting on Room 1 must fail with ROOM_CONFLICT and return suggested rooms
    r2 = client.post("/api/v1/bookings", json=payload2, headers=headers)
    assert r2.status_code == 409
    err2 = r2.json()
    assert err2["code"] == "ROOM_CONFLICT"
    assert "suggested_rooms" in err2.get("data", {})
    assert len(err2["data"]["suggested_rooms"]) > 0

def test_ac03_cleaning_buffer_30_mins():
    headers = get_receptionist_headers()
    uid = uuid.uuid4().hex[:6]
    rand_offset = random.randint(3000, 8000)
    target_date = datetime.now(timezone.utc).date() + timedelta(days=rand_offset)
    day = target_date.strftime("%Y-%m-%d")

    # Order 1: 10:00 to 13:00 on Room 102 (phongId=4)
    p1 = {
        "loaiDat": "GIO",
        "maHang": "STANDARD",
        "phongId": 4,
        "nhanLuc": f"{day}T10:00:00+07:00",
        "traLuc": f"{day}T13:00:00+07:00",
        "soKhach": 1,
        "thanhToan": "KHI_NHAN_PHONG",
        "dongYChinhSach": True,
        "customer": {
            "fullName": f"Buffer Test 1 {uid}",
            "phone": random_phone(),
            "email": f"buf1_{uid}@test.com",
            "nationality": "VN"
        }
    }
    r1 = client.post("/api/v1/bookings", json=p1, headers=headers)
    assert r1.status_code == 201

    # Order 2: 13:20 to 15:20 (overlap with 30-min buffer ending at 13:30)
    p2 = {
        "loaiDat": "GIO",
        "maHang": "STANDARD",
        "phongId": 4,
        "nhanLuc": f"{day}T13:20:00+07:00",
        "traLuc": f"{day}T15:20:00+07:00",
        "soKhach": 1,
        "thanhToan": "KHI_NHAN_PHONG",
        "dongYChinhSach": True,
        "customer": {
            "fullName": f"Buffer Test 2 {uid}",
            "phone": random_phone(),
            "email": f"buf2_{uid}@test.com",
            "nationality": "VN"
        }
    }
    r2 = client.post("/api/v1/bookings", json=p2, headers=headers)
    # Rejected because of 15-min step or buffer overlap
    assert r2.status_code in (409, 422)

    # Order 3: 13:30 to 15:30 (exactly 30 mins after 13:00) -> Accepted!
    p3 = {
        "loaiDat": "GIO",
        "maHang": "STANDARD",
        "phongId": 4,
        "nhanLuc": f"{day}T13:30:00+07:00",
        "traLuc": f"{day}T15:30:00+07:00",
        "soKhach": 1,
        "thanhToan": "KHI_NHAN_PHONG",
        "dongYChinhSach": True,
        "customer": {
            "fullName": f"Buffer Test 3 {uid}",
            "phone": random_phone(),
            "email": f"buf3_{uid}@test.com",
            "nationality": "VN"
        }
    }
    r3 = client.post("/api/v1/bookings", json=p3, headers=headers)
    assert r3.status_code == 201

def test_br21_max_unpaid_confirmed_bookings_limit():
    uid = uuid.uuid4().hex[:6]
    email = f"limit_{uid}@example.com"
    phone = random_phone()
    m = random.randint(1, 12)

    for i in range(1, 4):
        p = {
            "loaiDat": "NGAY",
            "maHang": "STANDARD",
            "nhanLuc": f"2029-{m:02d}-{10+i:02d}T14:00:00+07:00",
            "traLuc": f"2029-{m:02d}-{11+i:02d}T12:00:00+07:00",
            "soKhach": 1,
            "thanhToan": "KHI_NHAN_PHONG",
            "dongYChinhSach": True,
            "customer": {
                "fullName": f"Pending Guest {i} {uid}",
                "phone": phone,
                "email": email,
                "nationality": "VN"
            }
        }
        res = client.post("/api/v1/bookings", json=p)
        assert res.status_code == 201

    # 4th booking with same email/phone -> Must be rejected with PENDING_LIMIT_EXCEEDED
    p4 = {
        "loaiDat": "NGAY",
        "maHang": "STANDARD",
        "nhanLuc": f"2029-{m:02d}-20T14:00:00+07:00",
        "traLuc": f"2029-{m:02d}-21T12:00:00+07:00",
        "soKhach": 1,
        "thanhToan": "KHI_NHAN_PHONG",
        "dongYChinhSach": True,
        "customer": {
            "fullName": f"Pending Guest 4 {uid}",
            "phone": phone,
            "email": email,
            "nationality": "VN"
        }
    }
    r4 = client.post("/api/v1/bookings", json=p4)
    assert r4.status_code == 409
    err4 = r4.json()
    assert err4["code"] == "PENDING_LIMIT_EXCEEDED"
