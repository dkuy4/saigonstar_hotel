import httpx
import json
import sys

BASE_URL = "http://127.0.0.1:8000/api/v1"

def login(client, username, password):
    resp = client.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, f"Login failed for {username}: {resp.text}"
    return resp.json()["token"]

def main():
    print("=== TEST F13: BACKGROUND JOBS, NO-SHOW & EXCHANGE RATES ===")
    
    with httpx.Client(timeout=10.0) as client:
        token_ql = login(client, "quanly", "QuanLy123#")
        token_lt = login(client, "letan", "LeTan123#")
        headers_ql = {"Authorization": f"Bearer {token_ql}"}
        headers_lt = {"Authorization": f"Bearer {token_lt}"}

        # 1. RBAC check: LE_TAN accessing /system/jobs should be 403
        print("\n1. Testing RBAC on /system/jobs...")
        resp = client.get(f"{BASE_URL}/system/jobs", headers=headers_lt)
        assert resp.status_code == 403, f"Expected 403 for LE_TAN on /system/jobs, got {resp.status_code}"
        print("PASS: LE_TAN forbidden from /system/jobs (403)")

        # 2. QUAN_LY accessing /system/jobs
        print("\n2. Testing GET /system/jobs as QUAN_LY...")
        resp = client.get(f"{BASE_URL}/system/jobs", headers=headers_ql)
        assert resp.status_code == 200, f"Failed GET /system/jobs: {resp.text}"
        jobs = resp.json()
        assert len(jobs) == 4, f"Expected 4 jobs, got {len(jobs)}"
        job_ids = [j["id"] for j in jobs]
        assert "JOB_HET_HAN_GIU_CHO" in job_ids
        assert "JOB_TU_NO_SHOW" in job_ids
        assert "JOB_DOI_SOAT_PHONG" in job_ids
        assert "JOB_DONG_BO_TY_GIA" in job_ids
        print(f"PASS: Found {len(jobs)} background jobs: {job_ids}")

        # 3. Trigger manual execution for each job via POST /system/jobs/{id}/run
        print("\n3. Testing POST /system/jobs/{id}/run for each job...")
        for jid in job_ids:
            resp = client.post(f"{BASE_URL}/system/jobs/{jid}/run", headers=headers_ql)
            assert resp.status_code == 200, f"Failed running job {jid}: {resp.text}"
            data = resp.json()
            assert data["status"] == "SUCCESS", f"Job {jid} did not return SUCCESS: {data}"
            print(f"PASS: Job {jid} ran successfully in {data['durationMs']:.1f}ms: {data['result']}")

        # 4. Non-existent job run should return 404
        print("\n4. Testing invalid job run (404)...")
        resp = client.post(f"{BASE_URL}/system/jobs/JOB_UNKNOWN/run", headers=headers_ql)
        assert resp.status_code == 404, f"Expected 404 for unknown job, got {resp.status_code}"
        print("PASS: Unknown job returned 404")

        # 5. Room schedule discrepancies GET /system/discrepancies
        print("\n5. Testing GET /system/discrepancies...")
        resp = client.get(f"{BASE_URL}/system/discrepancies", headers=headers_ql)
        assert resp.status_code == 200, f"Failed GET /system/discrepancies: {resp.text}"
        discrepancies = resp.json()
        print(f"PASS: Fetched {len(discrepancies)} room discrepancies. Sample: {discrepancies[:2]}")

        # 6. Manual exchange rate update POST /api/v1/system/exchange-rates/manual
        print("\n6. Testing POST /system/exchange-rates/manual...")
        new_rates = [
            {"currency": "USD", "rateVnd": 25600.0},
            {"currency": "EUR", "rateVnd": 28300.0},
            {"currency": "CNY", "rateVnd": 3880.0},
            {"currency": "KRW", "rateVnd": 19.2},
            {"currency": "JPY", "rateVnd": 165.0}
        ]
        resp = client.post(f"{BASE_URL}/system/exchange-rates/manual", json={"rates": new_rates}, headers=headers_ql)
        assert resp.status_code == 200, f"Failed updating rates: {resp.text}"
        data = resp.json()
        assert data["status"] == "success"
        print("PASS: Updated manual exchange rates via /system/exchange-rates/manual")

        # 7. Also test POST /api/v1/exchange-rates/manual alias
        print("\n7. Testing POST /exchange-rates/manual alias...")
        resp = client.post(f"{BASE_URL}/exchange-rates/manual", json={"rates": new_rates}, headers=headers_ql)
        assert resp.status_code == 200, f"Failed updating rates via alias: {resp.text}"
        print("PASS: Updated manual exchange rates via alias /exchange-rates/manual")

        # 8. Check GET /api/v1/exchange-rates has updated rates
        print("\n8. Testing GET /exchange-rates...")
        resp = client.get(f"{BASE_URL}/exchange-rates")
        assert resp.status_code == 200, f"Failed GET /exchange-rates: {resp.text}"
        rates_list = resp.json()
        usd_rate = next((r for r in rates_list if r["currency"] == "USD"), None)
        assert usd_rate is not None and usd_rate["rate_vnd"] == 25600.0, f"USD rate not updated: {usd_rate}"
        print(f"PASS: Exchange rates active in public API: USD = {usd_rate['rate_vnd']:,.0f} VND")

        # 9. Test Manual No-Show: POST /api/v1/bookings/{id}/no-show
        print("\n9. Testing Manual No-Show on a CONFIRMED booking...")
        resp = client.get(f"{BASE_URL}/bookings?status=CONFIRMED&pageSize=5", headers=headers_lt)
        assert resp.status_code == 200, f"Failed searching bookings: {resp.text}"
        data = resp.json()
        confirmed_bookings = data.get("items") or data.get("data", {}).get("items") or []
        if not confirmed_bookings:
            print("Creating a temporary test booking to test NO_SHOW...")
            from datetime import datetime, timezone, timedelta
            tu = datetime.now(timezone.utc) + timedelta(days=5)
            den = datetime.now(timezone.utc) + timedelta(days=6)
            b_payload = {
                "customer": {"fullName": "Khách Test NoShow", "phone": "0987111222", "email": "noshow@gmail.com"},
                "roomTypeId": 1,
                "bookingType": "NGAY",
                "checkIn": tu.isoformat(),
                "checkOut": den.isoformat(),
                "channel": "QUAY"
            }
            b_resp = client.post(f"{BASE_URL}/bookings", json=b_payload, headers=headers_lt)
            assert b_resp.status_code == 201, f"Failed creating test booking: {b_resp.text}"
            b_created = b_resp.json()
            target_b_id = b_created.get("id") or b_created.get("data", {}).get("id")
        else:
            target_b_id = confirmed_bookings[0]["id"]

        print(f"Testing NO_SHOW on booking ID: {target_b_id}...")
        resp = client.post(f"{BASE_URL}/bookings/{target_b_id}/no-show", headers=headers_lt)
        assert resp.status_code == 200, f"Failed marking NO_SHOW: {resp.text}"
        ns_data = resp.json()
        assert ns_data["newStatus"] == "NO_SHOW"
        print(f"PASS: Booking {target_b_id} marked as NO_SHOW: {ns_data['message']}")

        # 10. Attempting NO_SHOW again on the same booking should fail with invalid state error
        print("\n10. Testing duplicate NO_SHOW on already closed booking...")
        resp = client.post(f"{BASE_URL}/bookings/{target_b_id}/no-show", headers=headers_lt)
        assert resp.status_code in [400, 409], f"Expected error when marking NO_SHOW on already NO_SHOW booking, got {resp.status_code}"
        print(f"PASS: Duplicate NO_SHOW correctly rejected with HTTP {resp.status_code}: {resp.json().get('error')}")

        print("\n=== ALL 10 TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    main()
