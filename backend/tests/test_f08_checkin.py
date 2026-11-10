import uuid
import random
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db import get_pool
from app.services.crypto import decrypt_id_document
from app.security import create_access_token
from contextlib import contextmanager

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

def test_checkin_requires_staff_auth():
    # 1. Unauthenticated -> 401
    res = client.post("/api/v1/bookings/1/check-in", json={
        "loaiGiayTo": "CCCD",
        "soGiayTo": "079201001234",
        "quocTich": "VN"
    })
    assert res.status_code == 401

    # 2. Housekeeping -> 403
    hk_headers = get_housekeeping_headers()
    res = client.post("/api/v1/bookings/1/check-in", json={
        "loaiGiayTo": "CCCD",
        "soGiayTo": "079201001234",
        "quocTich": "VN"
    }, headers=hk_headers)
    assert res.status_code == 403

def test_checkin_validation_missing_fields():
    headers = get_receptionist_headers()
    res = client.post("/api/v1/bookings/1/check-in", json={
        "quocTich": "VN"
    }, headers=headers)
    assert res.status_code == 422

def test_checkin_too_early_blocked_ac21():
    headers = get_receptionist_headers()
    uid = uuid.uuid4().hex[:6]
    
    # Create daily booking 10 days in future
    future_date = (datetime.now(timezone.utc) + timedelta(days=10)).date()
    day_str = future_date.strftime("%Y-%m-%d")
    next_day_str = (future_date + timedelta(days=1)).strftime("%Y-%m-%d")

    payload = {
        "loaiDat": "NGAY",
        "maHang": "STANDARD",
        "nhanLuc": f"{day_str}T14:00:00+07:00",
        "traLuc": f"{next_day_str}T12:00:00+07:00",
        "soKhach": 2,
        "thanhToan": "KHI_NHAN_PHONG",
        "dongYChinhSach": True,
        "customer": {
            "fullName": f"Early Guest {uid}",
            "phone": random_phone(),
            "email": f"early_{uid}@hoteltest.com",
            "nationality": "VN"
        }
    }
    create_res = client.post("/api/v1/bookings", json=payload, headers=headers)
    assert create_res.status_code == 201
    booking_id = create_res.json()["id"]

    # Attempt Check-in now (too early, AC-21, BR-32)
    ci_res = client.post(f"/api/v1/bookings/{booking_id}/check-in", json={
        "loaiGiayTo": "CCCD",
        "soGiayTo": "079201008888",
        "quocTich": "VN"
    }, headers=headers)

    assert ci_res.status_code == 409
    err = ci_res.json()
    assert err["code"] == "CHECKIN_TOO_EARLY"

def test_checkin_room_not_ready_blocked_br31():
    headers = get_receptionist_headers()
    uid = uuid.uuid4().hex[:6]

    # Create hourly booking starting at current 15-min mark
    now_dt = datetime.now(timezone(timedelta(hours=7)))
    minute_block = (now_dt.minute // 15) * 15
    checkin_dt = now_dt.replace(minute=minute_block, second=0, microsecond=0)
    checkout_dt = checkin_dt + timedelta(hours=2)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.phong_id, p.ma_phong
                  FROM phong p
                  JOIN loai_phong lp ON lp.loai_phong_id = p.loai_phong_id
                 WHERE lp.ma_hang = 'STANDARD'
                   AND p.trang_thai = 'TRONG'
                   AND p.phong_id NOT IN (
                       SELECT dpd.phong_id FROM dat_phong_doan dpd
                        WHERE dpd.tu_luc <= SYSTIMESTAMP + INTERVAL '3' HOUR
                          AND dpd.den_luc >= SYSTIMESTAMP - INTERVAL '1' HOUR
                   )
                 ORDER BY p.phong_id DESC
                 FETCH FIRST 1 ROW ONLY
            """)
            r_info = cur.fetchone()
            assert r_info is not None
            room_id, _ = r_info

    payload = {
        "loaiDat": "GIO",
        "maHang": "STANDARD",
        "phongId": room_id,
        "nhanLuc": checkin_dt.isoformat(),
        "traLuc": checkout_dt.isoformat(),
        "soKhach": 1,
        "thanhToan": "KHI_NHAN_PHONG",
        "dongYChinhSach": True,
        "customer": {
            "fullName": f"Dirty Room Guest {uid}",
            "phone": random_phone(),
            "email": f"dirty_{uid}@hoteltest.com",
            "nationality": "VN"
        }
    }
    create_res = client.post("/api/v1/bookings", json=payload, headers=headers)
    assert create_res.status_code == 201
    booking_id = create_res.json()["id"]

    # Temporarily set room status to DANG_DON (BR-31)
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE phong SET trang_thai = 'DANG_DON' WHERE phong_id = :rid", {"rid": room_id})
        conn.commit()

    try:
        # Check-in must be rejected with ROOM_NOT_READY
        ci_res = client.post(f"/api/v1/bookings/{booking_id}/check-in", json={
            "loaiGiayTo": "CCCD",
            "soGiayTo": "079201007777",
            "quocTich": "VN"
        }, headers=headers)
        assert ci_res.status_code == 409
        err = ci_res.json()
        assert err["code"] == "ROOM_NOT_READY"
    finally:
        # Restore room to TRONG
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE phong SET trang_thai = 'TRONG' WHERE phong_id = :rid", {"rid": room_id})
            conn.commit()

def test_checkin_success_flow_and_encrypted_document_nfr13():
    headers = get_receptionist_headers()
    uid = uuid.uuid4().hex[:6]
    raw_cccd = "079201009999"

    # Pick an available room for hourly booking starting at current 15-min mark
    now_dt = datetime.now(timezone(timedelta(hours=7)))
    minute_block = (now_dt.minute // 15) * 15
    checkin_dt = now_dt.replace(minute=minute_block, second=0, microsecond=0)
    checkout_dt = checkin_dt + timedelta(hours=2)

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.phong_id, p.ma_phong
                  FROM phong p
                  JOIN loai_phong lp ON lp.loai_phong_id = p.loai_phong_id
                 WHERE lp.ma_hang = 'STANDARD'
                   AND p.trang_thai = 'TRONG'
                   AND p.phong_id NOT IN (
                       SELECT dpd.phong_id FROM dat_phong_doan dpd
                        WHERE dpd.tu_luc <= SYSTIMESTAMP + INTERVAL '3' HOUR
                          AND dpd.den_luc >= SYSTIMESTAMP - INTERVAL '1' HOUR
                   )
                 ORDER BY p.phong_id ASC
                 FETCH FIRST 1 ROW ONLY
            """)
            r_info = cur.fetchone()
            assert r_info is not None
            room_id, room_number = r_info

    payload = {
        "loaiDat": "GIO",
        "maHang": "STANDARD",
        "phongId": room_id,
        "nhanLuc": checkin_dt.isoformat(),
        "traLuc": checkout_dt.isoformat(),
        "soKhach": 1,
        "thanhToan": "KHI_NHAN_PHONG",
        "dongYChinhSach": True,
        "customer": {
            "fullName": f"Happy CheckIn Guest {uid}",
            "phone": random_phone(),
            "email": f"happyci_{uid}@hoteltest.com",
            "nationality": "VN"
        }
    }
    create_res = client.post("/api/v1/bookings", json=payload, headers=headers)
    assert create_res.status_code == 201
    booking_id = create_res.json()["id"]

    # 1. Execute Check-in
    ci_res = client.post(f"/api/v1/bookings/{booking_id}/check-in", json={
        "loaiGiayTo": "CCCD",
        "soGiayTo": raw_cccd,
        "quocTich": "VN",
        "anhUrl": "/uploads/documents/sample_cccd.jpg"
    }, headers=headers)

    assert ci_res.status_code == 200
    data = ci_res.json()
    assert data["booking_id"] == booking_id
    assert data["status"] == "CHECKED_IN"
    assert data["room_id"] == room_id
    assert room_number in data["room_number"]

    # 2. Verify Database State
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            # Check dat_phong
            cur.execute("SELECT trang_thai, nhan_thuc_te FROM dat_phong WHERE dat_phong_id = :id", {"id": booking_id})
            dp_row = cur.fetchone()
            assert dp_row[0] == "CHECKED_IN"
            assert dp_row[1] is not None

            # Check phong
            cur.execute("SELECT trang_thai FROM phong WHERE phong_id = :rid", {"rid": room_id})
            p_row = cur.fetchone()
            assert p_row[0] == "DANG_O"

            # Check giay_to_khach: must be ENCRYPTED (NFR-13)
            cur.execute("""
                SELECT gtk.so_giay_to, gtk.loai_giay_to, gtk.anh_url
                  FROM giay_to_khach gtk
                  JOIN dat_phong dp ON dp.khach_hang_id = gtk.khach_hang_id
                 WHERE dp.dat_phong_id = :id
            """, {"id": booking_id})
            gtk_row = cur.fetchone()
            assert gtk_row is not None
            enc_so_giay_to = gtk_row[0]
            # Ensure plaintext raw_cccd is NOT stored directly
            assert enc_so_giay_to != raw_cccd
            # Ensure it decrypts back to raw_cccd
            decrypted = decrypt_id_document(enc_so_giay_to)
            assert decrypted == raw_cccd

    # 3. Verify Staff Detail view masks ID and logs audit
    detail_res = client.get(f"/api/v1/bookings/{booking_id}", headers=headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["status"] == "CHECKED_IN"
    assert detail_data["customer"]["identificationId"] == "0792****9999"

    # Verify audit log recorded "XEM_GIAY_TO"
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT hanh_dong, bang FROM nhat_ky_kiem_toan
                 WHERE bang = 'GIAY_TO_KHACH' AND hanh_dong = 'XEM_GIAY_TO'
                 ORDER BY nhat_ky_id DESC
                 FETCH FIRST 1 ROW ONLY
            """)
            audit_row = cur.fetchone()
            assert audit_row is not None

def test_upload_document_photo():
    headers = get_receptionist_headers()
    # Upload sample file
    file_content = b"%PDF-1.4 test document content"
    files = {"file": ("test_passport.pdf", file_content, "application/pdf")}
    res = client.post("/api/v1/bookings/1/upload-document", files=files, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "photo_url" in data
    assert data["photo_url"].startswith("/uploads/documents/doc_")
    assert data["photo_url"].endswith(".pdf")
