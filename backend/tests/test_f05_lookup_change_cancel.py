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
    return f"092{random.randint(1000000, 9999999)}"

def create_and_confirm_booking(days_ahead=None, payment_method="TRUC_TUYEN"):
    uid = uuid.uuid4().hex[:6]
    email = f"guest_{uid}@test.com"

    # Base date with random offset to ensure always fresh available rooms
    if days_ahead is None:
        days_ahead = random.randint(30, 800)
    base_date = datetime.now(timezone.utc).date() + timedelta(days=days_ahead)
    out_date = base_date + timedelta(days=2)

    checkin_str = f"{base_date.isoformat()}T14:00:00+07:00"
    checkout_str = f"{out_date.isoformat()}T12:00:00+07:00"

    payload = {
        "loaiDat": "NGAY",
        "maHang": "STANDARD",
        "nhanLuc": checkin_str,
        "traLuc": checkout_str,
        "soKhach": 2,
        "thanhToan": payment_method,
        "dongYChinhSach": True,
        "customer": {
            "fullName": f"Guest F05 {uid}",
            "phone": random_phone(),
            "email": email,
            "nationality": "VN"
        }
    }
    res = client.post("/api/v1/bookings", json=payload)
    assert res.status_code == 201, f"Failed to create booking: {res.text}"
    booking = res.json()
    code = booking["booking_code"]

    if payment_method == "TRUC_TUYEN":
        # Pay via online gateway to make it CONFIRMED
        init_res = client.post("/api/v1/payments/online", json={"bookingCode": code, "email": email})
        assert init_res.status_code == 200
        ref = init_res.json().get("reference_code") or init_res.json().get("referenceCode")

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

    return code, email, booking

def test_lookup_booking_success():
    code, email, booking = create_and_confirm_booking()

    res = client.post("/api/v1/bookings/lookup", json={
        "bookingCode": code,
        "email": email.upper() # should be case-insensitive
    })
    assert res.status_code == 200
    data = res.json()
    assert "token" in data
    assert data["token"]
    assert data["booking"]["booking_code"] == code
    assert data["booking"]["status"] == "CONFIRMED"

def test_lookup_booking_wrong_email_or_code_returns_404():
    code, email, _ = create_and_confirm_booking()

    # Wrong email
    r1 = client.post("/api/v1/bookings/lookup", json={
        "bookingCode": code,
        "email": "wrong_guest@test.com"
    })
    assert r1.status_code == 404
    assert r1.json()["code"] == "BOOKING_NOT_FOUND"

    # Wrong code
    r2 = client.post("/api/v1/bookings/lookup", json={
        "bookingCode": "DP_NONEXISTENT",
        "email": email
    })
    assert r2.status_code == 404
    assert r2.json()["code"] == "BOOKING_NOT_FOUND"

def test_unauthorized_operations_without_token():
    code, _, _ = create_and_confirm_booking()

    # Preview refund without token
    r1 = client.get(f"/api/v1/bookings/{code}/refund-preview")
    assert r1.status_code == 401
    assert r1.json()["code"] == "UNAUTHORIZED"

    # Cancel without token
    r2 = client.post(f"/api/v1/bookings/{code}/cancel", json={"reason": "Cancel test"})
    assert r2.status_code == 401
    assert r2.json()["code"] == "UNAUTHORIZED"

def test_refund_preview_and_cancel_over_24h_full_refund_ac09():
    # AC-09: Canceling >= 24h before checkin gives 100% refund of paid amount
    code, email, _ = create_and_confirm_booking()

    # 1. Lookup to get token
    lookup = client.post("/api/v1/bookings/lookup", json={"bookingCode": code, "email": email}).json()
    token = lookup["token"]
    headers = {"X-Booking-Token": token}

    # 2. Preview refund
    preview_res = client.get(f"/api/v1/bookings/{code}/refund-preview", headers=headers)
    assert preview_res.status_code == 200
    prev = preview_res.json()
    assert prev["isEligible"] is True
    assert prev["paidAmount"] == 1188000.0
    assert prev["expectedRefund"] == 1188000.0

    # 3. Cancel booking
    cancel_res = client.post(f"/api/v1/bookings/{code}/cancel", json={"reason": "Bận việc đột xuất"}, headers=headers)
    assert cancel_res.status_code == 200
    cdata = cancel_res.json()
    assert cdata["status"] == "success"
    assert cdata["newStatus"] == "CANCELLED"
    assert cdata["refundAmount"] == 1188000.0

    # 4. Verify booking is now CANCELLED in DB
    get_res = client.get(f"/api/v1/bookings/{code}")
    assert get_res.json()["status"] == "CANCELLED"

def test_refund_preview_under_24h_zero_refund():
    # Canceling < 24h before checkin gives 0 refund (BR-24)
    code, email, _ = create_and_confirm_booking()

    # Set checkin to 12 hours from now in DB
    pool = get_pool()
    with pool.acquire() as conn:
        with conn.cursor() as cur:
            cur.execute("ALTER SESSION SET CURRENT_SCHEMA = HOTEL_OWNER")
            cur.execute(
                "UPDATE dat_phong SET tu_luc = SYSTIMESTAMP + INTERVAL '12' HOUR WHERE ma_tra_cuu = :code",
                {"code": code}
            )
        conn.commit()

    lookup = client.post("/api/v1/bookings/lookup", json={"bookingCode": code, "email": email}).json()
    token = lookup["token"]
    headers = {"X-Booking-Token": token}

    preview_res = client.get(f"/api/v1/bookings/{code}/refund-preview", headers=headers)
    assert preview_res.status_code == 200
    prev = preview_res.json()
    assert prev["isEligible"] is False
    assert prev["paidAmount"] == 1188000.0
    assert prev["expectedRefund"] == 0.0

    # Cancel
    cancel_res = client.post(f"/api/v1/bookings/{code}/cancel", json={"reason": "Cancel late"}, headers=headers)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["newStatus"] == "CANCELLED"
    assert cancel_res.json()["refundAmount"] == 0.0

def test_cannot_cancel_checked_in_booking_ac10():
    # AC-10: Cannot cancel CHECKED_IN booking -> CANCEL_NOT_ALLOWED
    code, email, _ = create_and_confirm_booking()

    # Simulate CHECKED_IN in DB
    pool = get_pool()
    with pool.acquire() as conn:
        with conn.cursor() as cur:
            cur.execute("ALTER SESSION SET CURRENT_SCHEMA = HOTEL_OWNER")
            cur.execute(
                "UPDATE dat_phong SET trang_thai = 'CHECKED_IN', nhan_thuc_te = SYSTIMESTAMP WHERE ma_tra_cuu = :code",
                {"code": code}
            )
        conn.commit()

    lookup = client.post("/api/v1/bookings/lookup", json={"bookingCode": code, "email": email}).json()
    token = lookup["token"]
    headers = {"X-Booking-Token": token}

    cancel_res = client.post(f"/api/v1/bookings/{code}/cancel", json={"reason": "Try cancel checked in"}, headers=headers)
    assert cancel_res.status_code == 409
    assert cancel_res.json()["code"] == "CANCEL_NOT_ALLOWED"

def test_reschedule_booking_same_category_keeps_locked_price_d29():
    code, email, _ = create_and_confirm_booking()

    lookup = client.post("/api/v1/bookings/lookup", json={"bookingCode": code, "email": email}).json()
    token = lookup["token"]
    headers = {"X-Booking-Token": token}

    base_date = datetime.now(timezone.utc).date() + timedelta(days=random.randint(900, 1200))
    out_date = base_date + timedelta(days=2) # still 2 nights

    new_checkin = f"{base_date.isoformat()}T14:00:00+07:00"
    new_checkout = f"{out_date.isoformat()}T12:00:00+07:00"

    res = client.put(
        f"/api/v1/bookings/{code}",
        json={
            "nhanLuc": new_checkin,
            "traLuc": new_checkout
        },
        headers=headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["newStatus"] == "CONFIRMED"
    assert data["difference"] == 0.0
    assert data["newTotal"] == data["oldTotal"]
