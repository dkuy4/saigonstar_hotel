import sys
import time
from datetime import datetime, timezone, timedelta
import httpx

sys.path.insert(0, r"D:\HQT-CSDL\saigonstar_hotel\backend")
from app.config import settings

BASE_URL = "http://127.0.0.1:8000"
API_V1 = f"{BASE_URL}/api/v1"


def main():
    print("=== TEST F21: OPENAPI DOCS, API KEY, SECURITY HEADERS & RATE LIMITING ===")

    with httpx.Client(timeout=15.0) as client:
        # 1. OpenAPI & Swagger Docs
        print("\n1. Testing /docs and /openapi.json...")
        r_docs = client.get(f"{BASE_URL}/docs")
        assert r_docs.status_code == 200, f"Expected 200 for /docs, got {r_docs.status_code}"
        assert "Swagger UI" in r_docs.text or "swagger-ui" in r_docs.text.lower()

        r_spec = client.get(f"{BASE_URL}/openapi.json")
        assert r_spec.status_code == 200, f"Expected 200 for /openapi.json, got {r_spec.status_code}"
        spec = r_spec.json()
        assert "/api/v1/bookings" in spec.get("paths", {})
        assert len(spec.get("tags", [])) >= 8
        print(f"PASS: /docs & /openapi.json accessible ({len(spec['paths'])} endpoints, {len(spec['tags'])} tags)")

        # 2. Security Headers (NFR-16)
        print("\n2. Testing Security Headers...")
        assert r_spec.headers.get("X-Content-Type-Options") == "nosniff"
        assert r_spec.headers.get("X-Frame-Options") == "SAMEORIGIN"
        assert r_spec.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        print("PASS: Security headers present (X-Content-Type-Options, X-Frame-Options, Referrer-Policy)")

        # 3. Invalid X-API-Key rejected with 401 UNAUTHORIZED (AC-18)
        print("\n3. Testing invalid X-API-Key rejected with 401...")
        tz_vn = timezone(timedelta(hours=7))
        tu = (datetime.now(tz_vn) + timedelta(days=15)).replace(hour=14, minute=0, second=0, microsecond=0)
        den = (tu + timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
        ts = int(time.time())
        booking_payload = {
            "loaiDat": "NGAY",
            "maHang": "STANDARD",
            "nhanLuc": tu.isoformat(),
            "traLuc": den.isoformat(),
            "soKhach": 1,
            "thanhToan": "KHI_NHAN_PHONG",
            "ngonNgu": "vi",
            "dongYChinhSach": True,
            "customer": {
                "fullName": "Partner API Guest",
                "phone": f"09{ts % 100000000:08d}",
                "email": f"partner_{ts}@example.com",
                "nationality": "VN",
            },
        }
        r_bad_key = client.post(
            f"{API_V1}/bookings",
            json=booking_payload,
            headers={"X-API-Key": "wrong-api-key"},
        )
        assert r_bad_key.status_code == 401, f"Expected 401 for bad API key, got {r_bad_key.status_code}: {r_bad_key.text}"
        assert r_bad_key.json().get("code") == "UNAUTHORIZED"
        print("PASS: Invalid X-API-Key rejected with 401 UNAUTHORIZED")

        # 4. Valid X-API-Key creates booking on channel API (AC-18)
        print("\n4. Testing valid X-API-Key booking creation...")
        r_ok_key = client.post(
            f"{API_V1}/bookings",
            json=booking_payload,
            headers={"X-API-Key": settings.API_KEY_INTEGRATION},
        )
        assert r_ok_key.status_code == 201, f"Expected 201 for valid API key, got {r_ok_key.status_code}: {r_ok_key.text}"
        b_data = r_ok_key.json()
        assert b_data["booking_code"].startswith("DP")
        print(f"PASS: Booking created via X-API-Key channel: {b_data['booking_code']} (total: {b_data['total_amount']:,.0f} đ)")

        # 5. Rate limiting on /auth/login (20 consecutive requests -> 429 RATE_LIMITED)
        print("\n5. Testing Rate Limiting on POST /api/v1/auth/login (20 consecutive requests)...")
        statuses = []
        for i in range(20):
            r_login = client.post(
                f"{API_V1}/auth/login",
                json={"username": "nonexistent_rate_test", "password": "wrongpassword"},
            )
            statuses.append(r_login.status_code)
            if r_login.status_code == 429:
                assert r_login.json().get("code") == "RATE_LIMITED"

        count_429 = statuses.count(429)
        assert count_429 >= 1, f"Expected at least one 429 RATE_LIMITED in 20 consecutive requests, got: {statuses}"
        print(f"PASS: Rate limiting triggered ({count_429}/20 requests returned 429 RATE_LIMITED)")

    print("\n=== ALL F21 TESTS PASSED SUCCESSFULLY! ===")


if __name__ == "__main__":
    main()
