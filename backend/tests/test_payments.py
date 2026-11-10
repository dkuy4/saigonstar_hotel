import uuid
import random
from datetime import datetime, timezone, timedelta
import pytest
from starlette.testclient import TestClient
from app.main import app
from app.db import get_pool
from app.services.payment import get_payment_gateway, MockPaymentGateway

client = TestClient(app)

def random_phone():
    return f"091{random.randint(1000000, 9999999)}"

def create_test_hold_booking():
    uid = uuid.uuid4().hex[:6]
    email = f"pay_{uid}@test.com"
    
    # Pick random month and day in 2028 to guarantee fresh empty rooms
    month = random.randint(1, 12)
    day = random.randint(1, 25)
    payload = {
        "loaiDat": "NGAY",
        "maHang": "STANDARD",
        "nhanLuc": f"2028-{month:02d}-{day:02d}T14:00:00+07:00",
        "traLuc": f"2028-{month:02d}-{day+2:02d}T12:00:00+07:00",
        "soKhach": 2,
        "thanhToan": "TRUC_TUYEN",
        "dongYChinhSach": True,
        "customer": {
            "fullName": f"Payment Test {uid}",
            "phone": random_phone(),
            "email": email,
            "nationality": "VN"
        }
    }
    res = client.post("/api/v1/bookings", json=payload)
    assert res.status_code == 201
    return res.json(), email

def test_init_online_payment_success():
    booking, email = create_test_hold_booking()
    code = booking["booking_code"]

    res = client.post("/api/v1/payments/online", json={
        "bookingCode": code,
        "email": email
    })
    assert res.status_code == 200
    data = res.json()
    b_code = data.get("booking_code") or data.get("bookingCode")
    ref = data.get("reference_code") or data.get("referenceCode")
    assert b_code == code
    assert ref.startswith("MOCK_")
    assert "/mock-pay/" in (data.get("payment_url") or data.get("paymentUrl"))
    assert data["amount"] == 1188000.0

def test_init_online_payment_wrong_email_rejected():
    booking, _ = create_test_hold_booking()
    code = booking["booking_code"]

    res = client.post("/api/v1/payments/online", json={
        "bookingCode": code,
        "email": "wrong.email@test.com"
    })
    assert res.status_code == 404
    assert res.json()["code"] == "BOOKING_NOT_FOUND"

def test_payment_callback_success_confirms_booking_ac07():
    booking, email = create_test_hold_booking()
    code = booking["booking_code"]

    # 1. Init payment
    init_res = client.post("/api/v1/payments/online", json={
        "bookingCode": code,
        "email": email
    })
    assert init_res.status_code == 200
    data = init_res.json()
    ref = data.get("reference_code") or data.get("referenceCode")

    # 2. Mock payment callback (Success)
    gateway = get_payment_gateway()
    assert isinstance(gateway, MockPaymentGateway)
    sig = gateway.generate_signature(ref, True)

    cb_res = client.post("/api/v1/payments/callback", json={
        "referenceCode": ref,
        "isSuccess": True,
        "signature": sig
    })
    assert cb_res.status_code == 200
    assert cb_res.json()["result"] == "XAC_NHAN"

    # 3. Verify booking is now CONFIRMED
    get_res = client.get(f"/api/v1/bookings/{code}")
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "CONFIRMED"

def test_payment_callback_replay_idempotent():
    booking, email = create_test_hold_booking()
    code = booking["booking_code"]

    init_res = client.post("/api/v1/payments/online", json={
        "bookingCode": code,
        "email": email
    })
    ref = init_res.json().get("reference_code") or init_res.json().get("referenceCode")

    gateway = get_payment_gateway()
    sig = gateway.generate_signature(ref, True)

    # First call
    r1 = client.post("/api/v1/payments/callback", json={
        "referenceCode": ref,
        "isSuccess": True,
        "signature": sig
    })
    assert r1.status_code == 200
    assert r1.json()["result"] == "XAC_NHAN"

    # Second call (replay / duplicate webhook) -> DA_XU_LY
    r2 = client.post("/api/v1/payments/callback", json={
        "referenceCode": ref,
        "isSuccess": True,
        "signature": sig
    })
    assert r2.status_code == 200
    assert r2.json()["result"] == "DA_XU_LY"

def test_payment_callback_fail_expires_booking():
    booking, email = create_test_hold_booking()
    code = booking["booking_code"]

    init_res = client.post("/api/v1/payments/online", json={
        "bookingCode": code,
        "email": email
    })
    ref = init_res.json().get("reference_code") or init_res.json().get("referenceCode")

    gateway = get_payment_gateway()
    sig = gateway.generate_signature(ref, False)

    cb_res = client.post("/api/v1/payments/callback", json={
        "referenceCode": ref,
        "isSuccess": False,
        "signature": sig
    })
    assert cb_res.status_code == 200
    assert cb_res.json()["result"] == "THAT_BAI"

    # Verify booking is now EXPIRED
    get_res = client.get(f"/api/v1/bookings/{code}")
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "EXPIRED"

def test_payment_callback_invalid_signature_rejected():
    booking, email = create_test_hold_booking()
    code = booking["booking_code"]

    init_res = client.post("/api/v1/payments/online", json={
        "bookingCode": code,
        "email": email
    })
    ref = init_res.json().get("reference_code") or init_res.json().get("referenceCode")

    # Bad signature
    cb_res = client.post("/api/v1/payments/callback", json={
        "referenceCode": ref,
        "isSuccess": True,
        "signature": "tampered_fake_signature"
    })
    assert cb_res.status_code == 401
    assert cb_res.json()["code"] == "UNAUTHORIZED"

def test_late_payment_success_room_free_ac08():
    # AC-08: Late payment when room is still free -> XAC_NHAN_MUON
    booking, email = create_test_hold_booking()
    code = booking["booking_code"]

    init_res = client.post("/api/v1/payments/online", json={
        "bookingCode": code,
        "email": email
    })
    ref = init_res.json().get("reference_code") or init_res.json().get("referenceCode")

    # Simulate expired hold in DB
    pool = get_pool()
    with pool.acquire() as conn:
        with conn.cursor() as cur:
            cur.execute("ALTER SESSION SET CURRENT_SCHEMA = HOTEL_OWNER")
            cur.execute(
                "UPDATE dat_phong SET trang_thai = 'EXPIRED', han_giu_cho = SYSTIMESTAMP - INTERVAL '5' MINUTE WHERE ma_tra_cuu = :code",
                {"code": code}
            )
        conn.commit()

    gateway = get_payment_gateway()
    sig = gateway.generate_signature(ref, True)

    cb_res = client.post("/api/v1/payments/callback", json={
        "referenceCode": ref,
        "isSuccess": True,
        "signature": sig
    })
    assert cb_res.status_code == 200
    assert cb_res.json()["result"] == "XAC_NHAN_MUON"

def test_late_payment_room_rebooked_refund_ac09():
    # AC-09: Late payment when room has already been taken by someone else -> HOAN_TIEN
    booking1, email1 = create_test_hold_booking()
    code1 = booking1["booking_code"]

    init_res1 = client.post("/api/v1/payments/online", json={
        "bookingCode": code1,
        "email": email1
    })
    ref1 = init_res1.json().get("reference_code") or init_res1.json().get("referenceCode")

    # Expire booking 1 and get assigned room_id and times
    pool = get_pool()
    with pool.acquire() as conn:
        with conn.cursor() as cur:
            cur.execute("ALTER SESSION SET CURRENT_SCHEMA = HOTEL_OWNER")
            cur.execute("""
                SELECT d.dat_phong_id, s.phong_id, s.tu_luc, s.den_luc, d.khach_hang_id
                FROM dat_phong d
                JOIN dat_phong_doan s ON s.dat_phong_id = d.dat_phong_id
                WHERE d.ma_tra_cuu = :code
            """, {"code": code1})
            row = cur.fetchone()
            dp1_id, phong_id, tu_luc, den_luc, kh_id = row

            # Expire booking 1
            cur.execute(
                "UPDATE dat_phong SET trang_thai = 'EXPIRED', han_giu_cho = SYSTIMESTAMP - INTERVAL '10' MINUTE WHERE dat_phong_id = :id",
                {"id": dp1_id}
            )

            # Insert Booking 2 taking this exact room directly into dat_phong & dat_phong_doan
            cur.execute("""
                INSERT INTO dat_phong (
                    ma_tra_cuu, khach_hang_id, loai_dat, kenh_dat, trang_thai,
                    tu_luc, den_luc, so_khach, don_gia_ap_dung, don_gia_ngay_ap_dung,
                    tien_phong, thue_suat, tien_vat, tong_tien, ngon_ngu
                ) VALUES (
                    'B2_' || DBMS_RANDOM.STRING('X', 6),
                    :kh_id, 'NGAY', 'WEB', 'CONFIRMED',
                    :tu, :den, 1, 1000000, 1000000,
                    1000000, 0.1, 100000, 1100000, 'vi'
                )
            """, {"kh_id": kh_id, "tu": tu_luc, "den": den_luc})

            cur.execute("SELECT MAX(dat_phong_id) FROM dat_phong")
            b2_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO dat_phong_doan (dat_phong_id, phong_id, tu_luc, den_luc)
                VALUES (:b2_id, :phong_id, :tu, :den)
            """, {"b2_id": b2_id, "phong_id": phong_id, "tu": tu_luc, "den": den_luc})
        conn.commit()

    # Now Booking 1 callback arrives (late)
    gateway = get_payment_gateway()
    sig = gateway.generate_signature(ref1, True)

    cb_res = client.post("/api/v1/payments/callback", json={
        "referenceCode": ref1,
        "isSuccess": True,
        "signature": sig
    })
    assert cb_res.status_code == 200
    assert cb_res.json()["result"] == "HOAN_TIEN"

