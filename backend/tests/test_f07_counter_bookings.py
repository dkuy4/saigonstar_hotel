import uuid
import random
from datetime import datetime, timezone, timedelta
import pytest
from starlette.testclient import TestClient

from app.main import app
from app.security import create_access_token

client = TestClient(app)

def get_staff_token(role="LE_TAN", username="letan1", user_id=2):
    return create_access_token({
        "sub": str(user_id),
        "username": username,
        "role": role,
        "full_name": f"Test {role}"
    })

def random_phone():
    return f"093{random.randint(1000000, 9999999)}"

def test_search_bookings_requires_staff_auth():
    # No auth -> 401
    r1 = client.get("/api/v1/bookings")
    assert r1.status_code == 401
    assert r1.json()["code"] == "UNAUTHORIZED"

    # Buong phong -> 403
    bp_token = get_staff_token(role="BUONG_PHONG", username="tapvu1", user_id=4)
    r2 = client.get("/api/v1/bookings", headers={"Authorization": f"Bearer {bp_token}"})
    assert r2.status_code == 403
    assert r2.json()["code"] == "FORBIDDEN"

def test_search_bookings_pagination_and_filter():
    token = get_staff_token(role="LE_TAN", username="letan1", user_id=2)
    res = client.get("/api/v1/bookings?page=1&pageSize=10", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["page"] == 1
    assert data["pageSize"] == 10
    assert len(data["items"]) <= 10

def test_create_counter_booking_with_specific_room_and_confirm():
    token = get_staff_token(role="LE_TAN", username="letan1", user_id=2)
    uid = uuid.uuid4().hex[:6]
    email = f"counter_{uid}@test.com"

    # Find an available room and dates
    days_ahead = random.randint(1500, 2000)
    base_date = datetime.now(timezone.utc).date() + timedelta(days=days_ahead)
    out_date = base_date + timedelta(days=2)

    checkin_str = f"{base_date.isoformat()}T14:00:00+07:00"
    checkout_str = f"{out_date.isoformat()}T12:00:00+07:00"

    payload = {
        "loaiDat": "NGAY",
        "maHang": "STANDARD",
        "phongId": 1, # specific room 101
        "nhanLuc": checkin_str,
        "traLuc": checkout_str,
        "soKhach": 2,
        "thanhToan": "KHI_NHAN_PHONG",
        "dongYChinhSach": True,
        "customer": {
            "fullName": f"Khách Tại Quầy {uid}",
            "phone": random_phone(),
            "email": email,
            "nationality": "VN"
        }
    }

    res = client.post("/api/v1/bookings", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 201
    booking = res.json()
    code = booking["booking_code"]
    assert booking["status"] == "CONFIRMED" # counter bookings are confirmed directly
    assert booking["channel"] == "QUAY"

    # Test search by guest name or code
    search_res = client.get(f"/api/v1/bookings?q={code}", headers={"Authorization": f"Bearer {token}"})
    assert search_res.status_code == 200
    sdata = search_res.json()
    assert len(sdata["items"]) >= 1
    assert any(b["bookingCode"] == code for b in sdata["items"])

    # Test rich detail endpoint
    detail_res = client.get(f"/api/v1/bookings/{code}", headers={"Authorization": f"Bearer {token}"})
    assert detail_res.status_code == 200
    ddata = detail_res.json()
    b_code = ddata.get("booking_code") or ddata.get("bookingCode")
    assert b_code == code
    assert ddata["status"] == "CONFIRMED"
    assert len(ddata["segments"]) >= 1
    assert (ddata["segments"][0].get("roomNumber") or ddata["segments"][0].get("room_number")) == "101"
    acts = ddata["actions"]
    assert (acts.get("can_check_in") or acts.get("canCheckIn")) is True
    assert (acts.get("can_reschedule") or acts.get("canReschedule")) is True
    assert (acts.get("can_cancel") or acts.get("canCancel")) is True

def test_create_counter_booking_conflict_returns_suggested_rooms():
    token = get_staff_token(role="LE_TAN", username="letan1", user_id=2)
    uid = uuid.uuid4().hex[:6]

    days_ahead = random.randint(2100, 3000)
    base_date = datetime.now(timezone.utc).date() + timedelta(days=days_ahead)
    out_date = base_date + timedelta(days=2)

    checkin_str = f"{base_date.isoformat()}T14:00:00+07:00"
    checkout_str = f"{out_date.isoformat()}T12:00:00+07:00"

    payload1 = {
        "loaiDat": "NGAY",
        "maHang": "STANDARD",
        "phongId": 1,
        "nhanLuc": checkin_str,
        "traLuc": checkout_str,
        "soKhach": 2,
        "thanhToan": "KHI_NHAN_PHONG",
        "dongYChinhSach": True,
        "customer": {
            "fullName": f"Khách 1 {uid}",
            "phone": random_phone(),
            "email": f"k1_{uid}@test.com",
            "nationality": "VN"
        }
    }
    r1 = client.post("/api/v1/bookings", json=payload1, headers={"Authorization": f"Bearer {token}"})
    assert r1.status_code == 201

    # Now attempt booking 2 for the EXACT same room and overlapping dates
    payload2 = {
        "loaiDat": "NGAY",
        "maHang": "STANDARD",
        "phongId": 1,
        "nhanLuc": checkin_str,
        "traLuc": checkout_str,
        "soKhach": 2,
        "thanhToan": "KHI_NHAN_PHONG",
        "dongYChinhSach": True,
        "customer": {
            "fullName": f"Khách 2 {uid}",
            "phone": random_phone(),
            "email": f"k2_{uid}@test.com",
            "nationality": "VN"
        }
    }
    r2 = client.post("/api/v1/bookings", json=payload2, headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 409
    err = r2.json()
    assert err["code"] == "ROOM_CONFLICT"
    assert "suggested_rooms" in err["data"]
    assert len(err["data"]["suggested_rooms"]) > 0
