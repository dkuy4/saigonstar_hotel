import sys
import time
import threading
import socketserver
from datetime import datetime, timezone, timedelta
import httpx

sys.path.insert(0, r"D:\HQT-CSDL\saigonstar_hotel\backend")
from app.db import get_pool
from app.config import settings

BASE_URL = "http://127.0.0.1:8000/api/v1"

RECEIVED_EMAILS = []


class MockSMTPHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.wfile.write(b"220 localhost ESMTP MockSMTP\r\n")
        mail_from = ""
        rcpt_to = []
        in_data = False
        data_lines = []

        while True:
            line = self.rfile.readline()
            if not line:
                break
            text = line.decode("utf-8", errors="replace")

            if in_data:
                if text.strip() == ".":
                    in_data = False
                    RECEIVED_EMAILS.append({
                        "from": mail_from,
                        "to": rcpt_to,
                        "raw": "".join(data_lines),
                    })
                    self.wfile.write(b"250 2.0.0 Ok: queued\r\n")
                else:
                    data_lines.append(text)
                continue

            upper = text.strip().upper()
            if upper.startswith("EHLO") or upper.startswith("HELO"):
                self.wfile.write(b"250-localhost\r\n250 OK\r\n")
            elif upper.startswith("MAIL FROM:"):
                mail_from = text.strip()[10:].strip()
                self.wfile.write(b"250 2.1.0 Ok\r\n")
            elif upper.startswith("RCPT TO:"):
                rcpt_to.append(text.strip()[8:].strip())
                self.wfile.write(b"250 2.1.5 Ok\r\n")
            elif upper == "DATA":
                in_data = True
                data_lines = []
                self.wfile.write(b"354 End data with <CR><LF>.<CR><LF>\r\n")
            elif upper == "QUIT":
                self.wfile.write(b"221 2.0.0 Bye\r\n")
                break
            else:
                self.wfile.write(b"250 OK\r\n")


class ReusableTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


def login(client: httpx.Client, username: str, password: str) -> str:
    resp = client.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["token"]


def cleanup_old_pending_emails():
    pool = get_pool()
    with pool.acquire() as conn:
        with conn.cursor() as cur:
            cur.execute(f"ALTER SESSION SET CURRENT_SCHEMA = {settings.ORA_SCHEMA}")
            cur.execute("UPDATE hang_doi_email SET trang_thai = 'DA_GUI' WHERE trang_thai = 'CHO_GUI'")
            conn.commit()


def main():
    print("=== TEST F14: EMAIL QUEUE, RETRY, RESEND & TEMPLATES ===")
    cleanup_old_pending_emails()

    with httpx.Client(timeout=60.0) as client:
        token_lt = login(client, "letan", "LeTan123#")
        token_ql = login(client, "quanly", "QuanLy123#")
        headers_lt = {"Authorization": f"Bearer {token_lt}"}
        headers_ql = {"Authorization": f"Bearer {token_ql}"}

        # 1. Đảm bảo SMTP đang TẮT trước để test kịch bản: đơn vẫn tạo được, email vào hàng đợi, thử lại -> LOI
        print("\n1. Testing booking creation when SMTP is DOWN...")
        tz_vn = timezone(timedelta(hours=7))
        tu = (datetime.now(tz_vn) + timedelta(days=10)).replace(hour=14, minute=0, second=0, microsecond=0)
        den = (tu + timedelta(days=1)).replace(hour=12, minute=0, second=0, microsecond=0)
        ts_suffix = int(time.time())
        b_payload = {
            "loaiDat": "NGAY",
            "maHang": "STANDARD",
            "nhanLuc": tu.isoformat(),
            "traLuc": den.isoformat(),
            "soKhach": 1,
            "thanhToan": "KHI_NHAN_PHONG",
            "ngonNgu": "vi",
            "dongYChinhSach": True,
            "customer": {
                "fullName": "Nguyen Van Email Test",
                "phone": f"09{ts_suffix % 100000000:08d}",
                "email": f"emailtest_{ts_suffix}@example.com",
                "nationality": "VN",
            },
        }
        res_b = client.post(f"{BASE_URL}/bookings", json=b_payload, headers=headers_lt)
        assert res_b.status_code == 201, f"Create booking failed: {res_b.text}"
        b_data = res_b.json()
        booking_id = b_data["id"]
        booking_code = b_data["booking_code"]
        print(f"PASS: Booking created while SMTP is down: {booking_code} (ID: {booking_id})")

        # Kiểm tra có đúng 1 email XAC_NHAN CHO_GUI trong chi tiết đơn
        detail_res = client.get(f"{BASE_URL}/bookings/{booking_id}", headers=headers_lt)
        assert detail_res.status_code == 200, f"Get detail failed: {detail_res.text}"
        emails = detail_res.json().get("emails", [])
        assert len(emails) >= 1, f"Expected >= 1 email in queue, got {emails}"
        assert emails[0]["emailType"] == "XAC_NHAN"
        assert emails[0]["language"] == "vi"
        assert emails[0]["status"] == "CHO_GUI"
        print(f"PASS: Queue has email #{emails[0]['emailId']} ({emails[0]['emailType']}, {emails[0]['language']}, {emails[0]['status']})")

        # 2. Chạy JOB_GUI_EMAIL cho đến khi email mới tạo thử lại đủ 3 lần và chuyển sang LOI
        print("\n2. Testing email retry & LOI marking when SMTP is DOWN...")
        latest_em = None
        for attempt in range(1, 15):
            r_job = client.post(f"{BASE_URL}/system/jobs/JOB_GUI_EMAIL/run", headers=headers_ql)
            assert r_job.status_code == 200, f"Job run failed: {r_job.text}"
            print(f"   Run #{attempt}: {r_job.json()['result']}")
            detail_after_fail = client.get(f"{BASE_URL}/bookings/{booking_id}", headers=headers_lt).json()
            latest_em = detail_after_fail["emails"][0]
            if latest_em["status"] == "LOI":
                break

        assert latest_em["status"] == "LOI", f"Expected LOI after failures, got {latest_em}"
        assert latest_em["attempts"] == 3, f"Expected 3 attempts, got {latest_em['attempts']}"
        assert latest_em["error"] is not None
        print(f"PASS: Email marked as LOI after {latest_em['attempts']} failed attempts: {latest_em['error'][:80]}")

        # 3. Bật Mock SMTP server ở localhost:1025 và test POST /bookings/{id}/resend-email
        print("\n3. Starting Mock SMTP server on 127.0.0.1:1025 & testing resend-email...")
        smtp_server = ReusableTCPServer(("127.0.0.1", 1025), MockSMTPHandler)
        smtp_thread = threading.Thread(target=smtp_server.serve_forever, daemon=True)
        smtp_thread.start()

        try:
            resend_res = client.post(f"{BASE_URL}/bookings/{booking_id}/resend-email", headers=headers_lt)
            assert resend_res.status_code == 200, f"Resend email failed: {resend_res.text}"
            print(f"PASS: resend-email returned: {resend_res.json()['message']}")

            # Chạy JOB_GUI_EMAIL để gửi email mới xếp
            r_job_ok = client.post(f"{BASE_URL}/system/jobs/JOB_GUI_EMAIL/run", headers=headers_ql)
            assert r_job_ok.status_code == 200, f"Job run failed: {r_job_ok.text}"
            print(f"   Job run with Mock SMTP: {r_job_ok.json()['result']}")

            detail_after_send = client.get(f"{BASE_URL}/bookings/{booking_id}", headers=headers_lt).json()
            sent_em = detail_after_send["emails"][0]
            assert sent_em["status"] == "DA_GUI", f"Expected DA_GUI, got {sent_em}"
            assert len(RECEIVED_EMAILS) >= 1, "Mock SMTP did not receive any email!"
            raw_mail = RECEIVED_EMAILS[-1]["raw"]
            assert booking_code in raw_mail, f"Booking code {booking_code} not found in email body!"
            print(f"PASS: Email #{sent_em['emailId']} delivered (DA_GUI) via SMTP and verified content contains {booking_code}")
        finally:
            smtp_server.shutdown()
            smtp_server.server_close()

        # 4. Kiểm tra RBAC: resend-email không cho phép người dùng chưa đăng nhập
        print("\n4. Testing RBAC on resend-email...")
        unauth_res = client.post(f"{BASE_URL}/bookings/{booking_id}/resend-email")
        assert unauth_res.status_code in (401, 403), f"Expected 401/403 without token, got {unauth_res.status_code}"
        print(f"PASS: Unauthenticated resend-email rejected with HTTP {unauth_res.status_code}")

    print("\n=== ALL F14 TESTS PASSED SUCCESSFULLY! ===")


if __name__ == "__main__":
    main()
