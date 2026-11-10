from datetime import datetime, timezone, timedelta
import pytest
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)
VN_TZ = timezone(timedelta(hours=7))

def test_get_room_types_vi():
    response = client.get("/api/v1/room-types", params={"lang": "vi"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4
    codes = [r["code"] for r in data]
    assert "STANDARD" in codes
    assert "SUPERIOR" in codes
    assert "DELUXE" in codes
    assert "SUITE" in codes

    standard = next(r for r in data if r["code"] == "STANDARD")
    assert standard["hourly_allowed"] is True
    assert standard["hourly_price"] == 80000.0
    assert standard["daily_price"] == 550000.0
    assert "Standard" in standard["name"]

    superior = next(r for r in data if r["code"] == "SUPERIOR")
    assert superior["hourly_allowed"] is False
    assert superior["daily_price"] == 950000.0

def test_get_room_types_en():
    response = client.get("/api/v1/room-types", params={"lang": "en"})
    assert response.status_code == 200
    data = response.json()
    standard = next(r for r in data if r["code"] == "STANDARD")
    assert standard["name"] == "Standard Room"
    assert "Wi-Fi" in (standard["amenities"] or "")

def test_get_exchange_rates():
    response = client.get("/api/v1/exchange-rates")
    assert response.status_code == 200
    data = response.json()
    currencies = {r["currency"]: r["rate_vnd"] for r in data}
    assert "USD" in currencies
    assert "EUR" in currencies
    assert currencies["USD"] > 20000

def test_availability_daily_two_nights_appendix_b():
    # 2 nights: 2026-12-01 14:00 to 2026-12-03 12:00
    checkin = "2026-12-01T14:00:00+07:00"
    checkout = "2026-12-03T12:00:00+07:00"
    response = client.get(
        "/api/v1/availability",
        params={"type": "NGAY", "checkin": checkin, "checkout": checkout}
    )
    assert response.status_code == 200
    res = response.json()
    assert res["type"] == "NGAY"
    items = res["items"]
    assert len(items) == 4

    superior = next(r for r in items if r["code"] == "SUPERIOR")
    # Appendix B: Superior 2 nights = 1.900.000 + 152.000 VAT = 2.052.000
    assert superior["room_amount"] == 1900000.0
    assert superior["vat_rate"] == 0.08
    assert superior["vat_amount"] == 152000.0
    assert superior["total_amount"] == 2052000.0
    assert superior["converted_prices"]["USD"] > 0

def test_availability_hourly_appendix_b():
    # 3 hours: 10:00 to 13:00
    ci_3h = "2026-12-01T10:00:00+07:00"
    co_3h = "2026-12-01T13:00:00+07:00"
    r3 = client.get(
        "/api/v1/availability",
        params={"type": "GIO", "checkin": ci_3h, "checkout": co_3h}
    )
    assert r3.status_code == 200
    items3 = r3.json()["items"]
    assert len(items3) == 1
    std3 = items3[0]
    assert std3["code"] == "STANDARD"
    assert std3["room_amount"] == 240000.0
    assert std3["vat_amount"] == 19200.0
    assert std3["total_amount"] == 259200.0

    # 5 hours: 10:00 to 15:00
    co_5h = "2026-12-01T15:00:00+07:00"
    r5 = client.get(
        "/api/v1/availability",
        params={"type": "GIO", "checkin": ci_3h, "checkout": co_5h}
    )
    assert r5.status_code == 200
    std5 = r5.json()["items"][0]
    assert std5["room_amount"] == 400000.0
    assert std5["vat_amount"] == 32000.0
    assert std5["total_amount"] == 432000.0

    # 6 hours: 10:00 to 16:00 -> capped at daily rate 550.000
    co_6h = "2026-12-01T16:00:00+07:00"
    r6 = client.get(
        "/api/v1/availability",
        params={"type": "GIO", "checkin": ci_3h, "checkout": co_6h}
    )
    assert r6.status_code == 200
    std6 = r6.json()["items"][0]
    assert std6["room_amount"] == 550000.0
    assert std6["vat_amount"] == 44000.0
    assert std6["total_amount"] == 594000.0

def test_hourly_not_allowed_for_superior_ac05():
    ci = "2026-12-01T10:00:00+07:00"
    co = "2026-12-01T13:00:00+07:00"
    response = client.get(
        "/api/v1/availability",
        params={"type": "GIO", "checkin": ci, "checkout": co, "room_type": "SUPERIOR"}
    )
    assert response.status_code == 422
    err = response.json()
    assert err["code"] == "HOURLY_NOT_ALLOWED"

def test_hourly_validation_non_15_min_step():
    ci = "2026-12-01T10:10:00+07:00"
    co = "2026-12-01T12:10:00+07:00"
    response = client.get(
        "/api/v1/availability",
        params={"type": "GIO", "checkin": ci, "checkout": co}
    )
    assert response.status_code == 422
    err = response.json()
    assert err["code"] == "VALIDATION_ERROR"

def test_hourly_validation_non_integer_hours():
    ci = "2026-12-01T10:00:00+07:00"
    co = "2026-12-01T11:30:00+07:00"
    response = client.get(
        "/api/v1/availability",
        params={"type": "GIO", "checkin": ci, "checkout": co}
    )
    assert response.status_code == 422
    err = response.json()
    assert err["code"] == "VALIDATION_ERROR"
