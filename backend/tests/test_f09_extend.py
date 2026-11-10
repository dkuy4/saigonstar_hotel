import uuid
import random
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db import get_pool
from app.security import create_access_token

client = TestClient(app)

@contextmanager
def get_db_connection():
    pool = get_pool()
    with pool.acquire() as conn:
        with conn.cursor() as cur:
            cur.execute("ALTER SESSION SET CURRENT_SCHEMA = HOTEL_OWNER")
        yield conn

def get_staff_token(role="LE_TAN", username="letan", user_id=22):
    return create_access_token({
        "sub": str(user_id),
        "username": username,
        "role": role,
        "full_name": f"Test {role}"
    })

def get_receptionist_headers():
    token = get_staff_token(role="LE_TAN", username="letan", user_id=22)
    return {"Authorization": f"Bearer {token}"}

def get_housekeeping_headers():
    token = get_staff_token(role="BUONG_PHONG", username="buongphong", user_id=23)
    return {"Authorization": f"Bearer {token}"}

def random_phone():
    return f"09{random.randint(10000000, 99999999)}"

def find_free_standard_room(hours_ahead: int = 24) -> tuple[int, str]:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.phong_id, p.ma_phong
                  FROM phong p
                  JOIN loai_phong lp ON lp.loai_phong_id = p.loai_phong_id
                 WHERE lp.ma_hang = 'STANDARD'
                   AND p.trang_thai = 'TRONG'
                   AND p.dang_hoat_dong = TRUE
                   AND pkg_kiem_tra_trung.dem_xung_dot(
                           p.phong_id,
                           SYSTIMESTAMP - INTERVAL '30' MINUTE,
                           SYSTIMESTAMP + NUMTODSINTERVAL(:hrs, 'HOUR')
                       ) = 0
                 ORDER BY p.phong_id DESC
                 FETCH FIRST 1 ROW ONLY
            """, {"hrs": hours_ahead})
            row = cur.fetchone()
            assert row is not None, "No free STANDARD room found for F09 test"
            return int(row[0]), str(row[1])

def find_any_free_room(hours_ahead: int = 72) -> tuple[int, str, str, float]:
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.phong_id, p.ma_phong, lp.ma_hang,
                       pkg_gia.don_gia(lp.loai_phong_id, 'NGAY') AS don_gia_ngay
                  FROM phong p
                  JOIN loai_phong lp ON lp.loai_phong_id = p.loai_phong_id
                 WHERE p.trang_thai = 'TRONG'
                   AND p.dang_hoat_dong = TRUE
                   AND pkg_kiem_tra_trung.dem_xung_dot(
                           p.phong_id,
                           SYSTIMESTAMP - INTERVAL '30' MINUTE,
                           SYSTIMESTAMP + NUMTODSINTERVAL(:hrs, 'HOUR')
                       ) = 0
                 ORDER BY p.phong_id DESC
                 FETCH FIRST 1 ROW ONLY
            """, {"hrs": hours_ahead})
            row = cur.fetchone()
            assert row is not None, "No free room found for F09 daily test"
            return int(row[0]), str(row[1]), str(row[2]), float(row[3])

def create_and_checkin_hourly_booking(room_id: int, duration_hours: int = 1):
    headers = get_receptionist_headers()
    uid = uuid.uuid4().hex[:6]

    now_vn = datetime.now(timezone(timedelta(hours=7)))
    minute_block = (now_vn.minute // 15) * 15
    checkin_dt = now_vn.replace(minute=minute_block, second=0, microsecond=0)
    checkout_dt = checkin_dt + timedelta(hours=duration_hours)

    create_res = client.post("/api/v1/bookings", json={
        "loaiDat": "GIO",
        "maHang": "STANDARD",
        "phongId": room_id,
        "nhanLuc": checkin_dt.isoformat(),
        "traLuc": checkout_dt.isoformat(),
        "soKhach": 1,
        "thanhToan": "KHI_NHAN_PHONG",
        "dongYChinhSach": True,
        "customer": {
            "fullName": f"Extend Guest {uid}",
            "phone": random_phone(),
            "email": f"extend_{uid}@hoteltest.com",
            "nationality": "VN"
        }
    }, headers=headers)
    assert create_res.status_code == 201, create_res.text
    booking = create_res.json()
    booking_id = booking["id"]

    ci_res = client.post(f"/api/v1/bookings/{booking_id}/check-in", json={
        "loaiGiayTo": "CCCD",
        "soGiayTo": f"079201{random.randint(100000, 999999)}",
        "quocTich": "VN"
    }, headers=headers)
    assert ci_res.status_code == 200, ci_res.text
    return booking, checkin_dt, checkout_dt

def cleanup_room_to_empty(room_id: int, booking_ids: list[int]):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            for bid in booking_ids:
                cur.execute("UPDATE dat_phong SET trang_thai = 'CANCELLED', ly_do_huy = 'Test cleanup' WHERE dat_phong_id = :id AND trang_thai IN ('CONFIRMED', 'HOLD')", {"id": bid})
            cur.execute("UPDATE phong SET trang_thai = 'TRONG' WHERE phong_id = :rid", {"rid": room_id})
        conn.commit()

def test_extend_requires_staff_auth():
    r1 = client.post("/api/v1/bookings/1/extend", json={"soDonVi": 1})
    assert r1.status_code == 401

    r2 = client.get("/api/v1/bookings/1/extend-preview?units=1")
    assert r2.status_code == 401

    hk_headers = get_housekeeping_headers()
    r3 = client.post("/api/v1/bookings/1/extend", json={"soDonVi": 1}, headers=hk_headers)
    assert r3.status_code == 403

def test_extend_requires_checked_in_state():
    headers = get_receptionist_headers()
    uid = uuid.uuid4().hex[:6]
    future = (datetime.now(timezone.utc) + timedelta(days=20)).date()

    create_res = client.post("/api/v1/bookings", json={
        "loaiDat": "NGAY",
        "maHang": "STANDARD",
        "nhanLuc": f"{future.strftime('%Y-%m-%d')}T14:00:00+07:00",
        "traLuc": f"{(future + timedelta(days=1)).strftime('%Y-%m-%d')}T12:00:00+07:00",
        "soKhach": 1,
        "thanhToan": "KHI_NHAN_PHONG",
        "dongYChinhSach": True,
        "customer": {
            "fullName": f"Not CheckedIn {uid}",
            "phone": random_phone(),
            "email": f"notci_{uid}@hoteltest.com",
            "nationality": "VN"
        }
    }, headers=headers)
    assert create_res.status_code == 201
    bid = create_res.json()["id"]

    res = client.post(f"/api/v1/bookings/{bid}/extend", json={"soDonVi": 1}, headers=headers)
    assert res.status_code == 409
    assert res.json()["code"] == "BOOKING_STATE_INVALID"

def test_extend_hourly_to_3h_and_to_6h_daily_threshold_br33():
    headers = get_receptionist_headers()
    room_id, _ = find_free_standard_room(hours_ahead=24)
    booking, checkin_dt, checkout_dt = create_and_checkin_hourly_booking(room_id, duration_hours=1)
    bid = booking["id"]

    try:
        # Initial 1h: 80.000 + 6.400 VAT = 86.400
        assert booking["room_amount"] == 80000
        assert booking["total_amount"] == 86400

        # 1. Preview +2 hours -> 3 hours (240.000 room + 19.200 VAT = 259.200)
        prev1 = client.get(f"/api/v1/bookings/{bid}/extend-preview?units=2", headers=headers)
        assert prev1.status_code == 200, prev1.text
        p1 = prev1.json()
        assert p1["new_room_amount"] == 240000
        assert p1["new_vat_amount"] == 19200
        assert p1["new_total_amount"] == 259200
        assert p1["added_amount"] == 172800
        assert p1["switched_to_daily_rate"] is False
        assert p1["has_conflict"] is False

        # Execute extend +2h
        ext1 = client.post(f"/api/v1/bookings/{bid}/extend", json={"soDonVi": 2}, headers=headers)
        assert ext1.status_code == 200, ext1.text
        e1 = ext1.json()
        assert e1["room_amount"] == 240000
        assert e1["vat_amount"] == 19200
        assert e1["total_amount"] == 259200
        assert e1["added_amount"] == p1["added_amount"]

        # 2. Preview +3 hours -> total 6 hours (>5h threshold -> 1 daily rate = 550.000 room, BR-33)
        prev2 = client.get(f"/api/v1/bookings/{bid}/extend-preview?units=3", headers=headers)
        assert prev2.status_code == 200, prev2.text
        p2 = prev2.json()
        assert p2["new_room_amount"] == 550000
        assert p2["new_vat_amount"] == 44000
        assert p2["new_total_amount"] == 594000
        assert p2["added_amount"] == 594000 - 259200
        assert p2["switched_to_daily_rate"] is True

        # Execute extend +3h
        ext2 = client.post(f"/api/v1/bookings/{bid}/extend", json={"soDonVi": 3}, headers=headers)
        assert ext2.status_code == 200, ext2.text
        e2 = ext2.json()
        assert e2["room_amount"] == 550000
        assert e2["vat_amount"] == 44000
        assert e2["total_amount"] == 594000
        assert e2["added_amount"] == p2["added_amount"]
    finally:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE phong SET trang_thai = 'TRONG' WHERE phong_id = :rid", {"rid": room_id})
                cur.execute("UPDATE dat_phong SET trang_thai = 'CHECKED_OUT' WHERE dat_phong_id = :id", {"id": bid})
            conn.commit()

def test_extend_conflict_with_next_booking_buffer_ac12():
    headers = get_receptionist_headers()
    room_id, _ = find_free_standard_room(hours_ahead=24)
    booking, checkin_dt, checkout_dt = create_and_checkin_hourly_booking(room_id, duration_hours=1)
    bid1 = booking["id"]
    uid = uuid.uuid4().hex[:6]

    # Create Booking 2 on SAME room starting at checkout_dt + 1h15m
    # So there is only 15m buffer if Booking 1 extends by +1h (needs 30m buffer -> AC-12 conflict!)
    next_checkin = checkout_dt + timedelta(minutes=75)
    next_checkout = next_checkin + timedelta(hours=1)
    b2_res = client.post("/api/v1/bookings", json={
        "loaiDat": "GIO",
        "maHang": "STANDARD",
        "phongId": room_id,
        "nhanLuc": next_checkin.isoformat(),
        "traLuc": next_checkout.isoformat(),
        "soKhach": 1,
        "thanhToan": "KHI_NHAN_PHONG",
        "dongYChinhSach": True,
        "customer": {
            "fullName": f"Next Guest {uid}",
            "phone": random_phone(),
            "email": f"next_{uid}@hoteltest.com",
            "nationality": "VN"
        }
    }, headers=headers)
    assert b2_res.status_code == 201, b2_res.text
    bid2 = b2_res.json()["id"]

    try:
        # Preview should detect conflict & suggest rooms
        prev = client.get(f"/api/v1/bookings/{bid1}/extend-preview?units=1", headers=headers)
        assert prev.status_code == 200
        pdata = prev.json()
        assert pdata["has_conflict"] is True
        assert len(pdata["suggested_rooms"]) > 0
        assert all(r["room_id"] != room_id for r in pdata["suggested_rooms"])

        # Attempting extend +1h must fail with 409 EXTEND_CONFLICT + suggested_rooms (AC-12)
        ext = client.post(f"/api/v1/bookings/{bid1}/extend", json={"soDonVi": 1}, headers=headers)
        assert ext.status_code == 409
        err = ext.json()
        assert err["code"] == "EXTEND_CONFLICT"
        assert "suggested_rooms" in err["data"]
        assert len(err["data"]["suggested_rooms"]) > 0
    finally:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE dat_phong SET trang_thai = 'CANCELLED', ly_do_huy = 'Cleanup' WHERE dat_phong_id = :id", {"id": bid2})
                cur.execute("UPDATE dat_phong SET trang_thai = 'CHECKED_OUT' WHERE dat_phong_id = :id", {"id": bid1})
                cur.execute("UPDATE phong SET trang_thai = 'TRONG' WHERE phong_id = :rid", {"rid": room_id})
            conn.commit()

def test_extend_daily_booking_keeps_locked_rate_br34():
    headers = get_receptionist_headers()
    room_id, _, ma_hang, daily_rate = find_any_free_room(hours_ahead=72)
    uid = uuid.uuid4().hex[:6]

    now_vn = datetime.now(timezone(timedelta(hours=7)))
    today_str = now_vn.strftime("%Y-%m-%d")
    tomorrow_str = (now_vn + timedelta(days=1)).strftime("%Y-%m-%d")

    create_res = client.post("/api/v1/bookings", json={
        "loaiDat": "NGAY",
        "maHang": ma_hang,
        "phongId": room_id,
        "nhanLuc": f"{today_str}T14:00:00+07:00",
        "traLuc": f"{tomorrow_str}T12:00:00+07:00",
        "soKhach": 2,
        "thanhToan": "KHI_NHAN_PHONG",
        "dongYChinhSach": True,
        "customer": {
            "fullName": f"Daily Extend Guest {uid}",
            "phone": random_phone(),
            "email": f"dailyext_{uid}@hoteltest.com",
            "nationality": "VN"
        }
    }, headers=headers)
    assert create_res.status_code == 201, create_res.text
    bid = create_res.json()["id"]

    # Ensure check-in is valid regardless of test execution time of day
    if now_vn.hour < 14:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE dat_phong SET tu_luc = tu_luc - INTERVAL '1' DAY WHERE dat_phong_id = :id", {"id": bid})
                cur.execute("UPDATE dat_phong_doan SET tu_luc = tu_luc - INTERVAL '1' DAY WHERE dat_phong_id = :id", {"id": bid})
            conn.commit()

    ci_res = client.post(f"/api/v1/bookings/{bid}/check-in", json={
        "loaiGiayTo": "CCCD",
        "soGiayTo": f"079201{random.randint(100000, 999999)}",
        "quocTich": "VN"
    }, headers=headers)
    assert ci_res.status_code == 200, ci_res.text

    try:
        expected_2_nights_room = round(daily_rate * 2)
        expected_2_nights_vat = round(expected_2_nights_room * 0.08)
        expected_2_nights_total = expected_2_nights_room + expected_2_nights_vat
        expected_1_night_total = round(daily_rate) + round(daily_rate * 0.08)

        prev = client.get(f"/api/v1/bookings/{bid}/extend-preview?units=1", headers=headers)
        assert prev.status_code == 200, prev.text
        pdata = prev.json()
        assert pdata["new_room_amount"] == expected_2_nights_room
        assert pdata["added_amount"] == expected_1_night_total
        assert pdata["has_conflict"] is False

        ext = client.post(f"/api/v1/bookings/{bid}/extend", json={"soDonVi": 1}, headers=headers)
        assert ext.status_code == 200, ext.text
        edata = ext.json()
        assert edata["room_amount"] == expected_2_nights_room
        assert edata["vat_amount"] == expected_2_nights_vat
        assert edata["total_amount"] == expected_2_nights_total
        assert edata["added_amount"] == expected_1_night_total
    finally:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE dat_phong SET trang_thai = 'CHECKED_OUT' WHERE dat_phong_id = :id", {"id": bid})
                cur.execute("UPDATE phong SET trang_thai = 'TRONG' WHERE phong_id = :rid", {"rid": room_id})
            conn.commit()
