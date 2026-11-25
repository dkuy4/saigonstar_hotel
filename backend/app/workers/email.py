import logging
import smtplib
from datetime import datetime
from email.message import EmailMessage
from typing import Dict, Any, Optional
import oracledb

from app.config import settings
from app.core.translation_meta import DEFAULT_TRANSLATIONS

logger = logging.getLogger(__name__)

EMAIL_SUBJECTS: Dict[str, Dict[str, str]] = {
    "XAC_NHAN": {
        "vi": "[Khách sạn Sài Gòn Star] Xác nhận đặt phòng #{ma_don}",
        "en": "[Saigon Star Hotel] Booking Confirmation #{ma_don}",
        "zh-CN": "[西贡之星酒店] 预订确认 #{ma_don}",
        "ko": "[사이공 스타 호텔] 예약 확인 #{ma_don}",
        "ja": "[サイゴンスターホテル] ご予約確認 #{ma_don}",
        "es": "[Saigon Star Hotel] Confirmación de reserva #{ma_don}",
        "fr": "[Saigon Star Hotel] Confirmation de réservation #{ma_don}",
    },
    "THAY_DOI_DON": {
        "vi": "[Khách sạn Sài Gòn Star] Thông báo thay đổi đơn #{ma_don}",
        "en": "[Saigon Star Hotel] Reservation Update #{ma_don}",
        "zh-CN": "[西贡之星酒店] 预订变更通知 #{ma_don}",
        "ko": "[사이공 스타 호텔] 예약 변경 안내 #{ma_don}",
        "ja": "[サイゴンスターホテル] ご予約変更のお知らせ #{ma_don}",
        "es": "[Saigon Star Hotel] Actualización de reserva #{ma_don}",
        "fr": "[Saigon Star Hotel] Modification de réservation #{ma_don}",
    },
    "HUY_HOAN_TIEN": {
        "vi": "[Khách sạn Sài Gòn Star] Xác nhận hủy đơn & hoàn tiền #{ma_don}",
        "en": "[Saigon Star Hotel] Cancellation & Refund Notice #{ma_don}",
        "zh-CN": "[西贡之星酒店] 取消与退款通知 #{ma_don}",
        "ko": "[사이공 스타 호텔] 예약 취소 및 환불 안내 #{ma_don}",
        "ja": "[サイゴンスターホテル] キャンセル・返金のご案内 #{ma_don}",
        "es": "[Saigon Star Hotel] Cancelación y reembolso #{ma_don}",
        "fr": "[Saigon Star Hotel] Annulation et remboursement #{ma_don}",
    },
    "HET_HAN_GIU_CHO": {
        "vi": "[Khách sạn Sài Gòn Star] Đơn đặt phòng #{ma_don} đã hết hạn giữ chỗ",
        "en": "[Saigon Star Hotel] Reservation Hold Expired #{ma_don}",
        "zh-CN": "[西贡之星酒店] 预订保留已过期 #{ma_don}",
        "ko": "[사이공 스타 호텔] 예약 유지 시간 만료 안내 #{ma_don}",
        "ja": "[サイゴンスターホテル] 仮押さえ期限切れのお知らせ #{ma_don}",
        "es": "[Saigon Star Hotel] Reserva expirada #{ma_don}",
        "fr": "[Saigon Star Hotel] Réservation expirée #{ma_don}",
    },
    "THANH_TOAN_VE_MUON": {
        "vi": "[Khách sạn Sài Gòn Star] Xử lý thanh toán về muộn cho đơn #{ma_don}",
        "en": "[Saigon Star Hotel] Late Payment Resolution #{ma_don}",
        "zh-CN": "[西贡之星酒店] 逾期付款处理通知 #{ma_don}",
        "ko": "[사이공 스타 호텔] 지연 결제 처리 안내 #{ma_don}",
        "ja": "[サイゴンスターホテル] 遅延決済処理のご案内 #{ma_don}",
        "es": "[Saigon Star Hotel] Resolución de pago tardío #{ma_don}",
        "fr": "[Saigon Star Hotel] Traitement de paiement tardif #{ma_don}",
    },
}


class EmailWorker:
    """
    Background email worker reading from HANG_DOI_EMAIL with FOR UPDATE SKIP LOCKED (F14, FR-53).
    Renders email body from NOI_DUNG_DICH (fallback DEFAULT_TRANSLATIONS) and sends via SMTP.
    """

    @staticmethod
    def _get_max_retries(conn: oracledb.Connection) -> int:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT gia_tri_so
                      FROM cau_hinh_he_thong
                     WHERE ma_tham_so = 'SO_LAN_THU_EMAIL_TOI_DA'
                       AND hieu_luc_tu <= SYSTIMESTAMP
                     ORDER BY hieu_luc_tu DESC
                     FETCH FIRST 1 ROW ONLY
                    """
                )
                row = cur.fetchone()
                if row and row[0] is not None:
                    return max(1, int(row[0]))
        except Exception as e:
            logger.debug(f"Could not read SO_LAN_THU_EMAIL_TOI_DA from DB, using default 3: {e}")
        return 3

    @staticmethod
    def _get_template(conn: oracledb.Connection, ma_khoa: str, lang: str) -> str:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT noi_dung
                  FROM noi_dung_dich
                 WHERE ma_noi_dung = :ma_khoa AND ngon_ngu = :ngon_ngu
                """,
                {"ma_khoa": ma_khoa, "ngon_ngu": lang},
            )
            row = cur.fetchone()
            if row and row[0]:
                val = row[0]
                return val.read() if hasattr(val, "read") else str(val)

            if lang != "vi":
                cur.execute(
                    """
                    SELECT noi_dung
                      FROM noi_dung_dich
                     WHERE ma_noi_dung = :ma_khoa AND ngon_ngu = 'vi'
                    """,
                    {"ma_khoa": ma_khoa},
                )
                row_vi = cur.fetchone()
                if row_vi and row_vi[0]:
                    val = row_vi[0]
                    return val.read() if hasattr(val, "read") else str(val)

        tpl_map = DEFAULT_TRANSLATIONS.get(ma_khoa, {})
        return tpl_map.get(lang) or tpl_map.get("vi") or ""

    @staticmethod
    def _fmt_dt(dt: Any) -> str:
        if not dt:
            return "-"
        if isinstance(dt, datetime):
            return dt.strftime("%H:%M %d/%m/%Y")
        return str(dt)

    @staticmethod
    def _fmt_money(amount: Any) -> str:
        try:
            return f"{float(amount or 0):,.0f} VND"
        except Exception:
            return "0 VND"

    @staticmethod
    def _fetch_booking_context(conn: oracledb.Connection, dat_phong_id: int, lang: str) -> Optional[Dict[str, Any]]:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT dp.dat_phong_id, dp.ma_tra_cuu, dp.trang_thai, dp.loai_dat,
                       dp.tu_luc, dp.den_luc, dp.tong_tien, dp.ngon_ngu,
                       kh.ho_ten, kh.email, kh.sdt,
                       NVL(lpd.ten, lp.ma_hang) AS ten_hang
                  FROM dat_phong dp
                  JOIN khach_hang kh ON kh.khach_hang_id = dp.khach_hang_id
                  LEFT JOIN (
                    SELECT d.dat_phong_id, MIN(d.phong_id) AS phong_id
                      FROM dat_phong_doan d
                     GROUP BY d.dat_phong_id
                  ) seg ON seg.dat_phong_id = dp.dat_phong_id
                  LEFT JOIN phong p ON p.phong_id = seg.phong_id
                  LEFT JOIN loai_phong lp ON lp.loai_phong_id = p.loai_phong_id
                  LEFT JOIN loai_phong_dich lpd ON lpd.loai_phong_id = lp.loai_phong_id AND lpd.ngon_ngu = :lang
                 WHERE dp.dat_phong_id = :dp_id
                """,
                {"dp_id": dat_phong_id, "lang": lang},
            )
            row = cur.fetchone()
            if not row:
                return None

            cols = [c[0].lower() for c in cur.description]
            dp = dict(zip(cols, row))

            cur.execute(
                """
                SELECT DISTINCT p.ma_phong
                  FROM dat_phong_doan d
                  JOIN phong p ON p.phong_id = d.phong_id
                 WHERE d.dat_phong_id = :dp_id
                 ORDER BY p.ma_phong
                """,
                {"dp_id": dat_phong_id},
            )
            rooms = [r[0] for r in cur.fetchall() if r[0]]
            room_str = ", ".join(rooms) if rooms else ("Chưa xếp phòng" if lang == "vi" else "Pending assignment")

            cur.execute(
                """
                SELECT NVL(SUM(ht.so_tien), 0) AS tong_hoan
                  FROM hoan_tien ht
                  JOIN giao_dich_thanh_toan gd ON gd.giao_dich_id = ht.giao_dich_id
                 WHERE gd.dat_phong_id = :dp_id
                """,
                {"dp_id": dat_phong_id},
            )
            ref_row = cur.fetchone()
            tien_hoan = float(ref_row[0] or 0) if ref_row else 0.0

            return {
                "dat_phong_id": dp["dat_phong_id"],
                "ma_don": dp["ma_tra_cuu"],
                "trang_thai": dp["trang_thai"],
                "loai_dat": dp["loai_dat"],
                "ten_khach": dp["ho_ten"],
                "email": dp["email"],
                "ten_hang": dp["ten_hang"] or "Standard",
                "so_phong": room_str,
                "thoi_gian_nhan": EmailWorker._fmt_dt(dp["tu_luc"]),
                "thoi_gian_tra": EmailWorker._fmt_dt(dp["den_luc"]),
                "tong_tien": EmailWorker._fmt_money(dp["tong_tien"]),
                "tien_hoan": EmailWorker._fmt_money(tien_hoan),
                "link_tra_cuu": f"http://127.0.0.1:5173/don/{dp['ma_tra_cuu']}",
                "link_dat_lai": "http://127.0.0.1:5173/",
            }

    @staticmethod
    def _render_email(conn: oracledb.Connection, loai_email: str, lang: str, ctx: Dict[str, Any]) -> tuple[str, str]:
        ma_khoa = f"EMAIL_{loai_email}"
        template = EmailWorker._get_template(conn, ma_khoa, lang)
        policy = EmailWorker._get_template(conn, "CHINH_SACH_HUY", lang)

        subject_map = EMAIL_SUBJECTS.get(loai_email, EMAIL_SUBJECTS["XAC_NHAN"])
        subject_tpl = subject_map.get(lang) or subject_map.get("vi") or "[Saigon Star Hotel] #{ma_don}"
        subject = subject_tpl.format(ma_don=ctx["ma_don"])

        replacements = {
            "{ma_don}": ctx["ma_don"],
            "{ten_khach}": ctx["ten_khach"],
            "{ten_hang}": f"{ctx['ten_hang']} (Phòng: {ctx['so_phong']})" if lang == "vi" else f"{ctx['ten_hang']} (Room: {ctx['so_phong']})",
            "{thoi_gian_nhan}": ctx["thoi_gian_nhan"],
            "{thoi_gian_tra}": ctx["thoi_gian_tra"],
            "{tong_tien}": ctx["tong_tien"],
            "{link_tra_cuu}": ctx["link_tra_cuu"],
            "{thong_tin_cu}": "Theo lịch trước đó" if lang == "vi" else "Previous schedule",
            "{thong_tin_moi}": f"{ctx['thoi_gian_nhan']} - {ctx['thoi_gian_tra']} ({ctx['so_phong']})",
            "{chenh_lech}": ctx["tong_tien"],
            "{tien_hoan}": ctx["tien_hoan"],
            "{phuong_thuc}": "Theo phương thức thanh toán ban đầu" if lang == "vi" else "Original payment method",
            "{thoi_gian_du_kien}": "1 - 3 ngày làm việc" if lang == "vi" else "1 - 3 business days",
            "{link_dat_lai}": ctx["link_dat_lai"],
            "{noi_dung_xu_ly}": "Hệ thống đã ghi nhận giao dịch về muộn và tạo yêu cầu hoàn tiền tự động (BR-19)." if lang == "vi" else "Late payment has been recorded and an automatic refund request has been created (BR-19).",
        }

        body = template
        for k, v in replacements.items():
            body = body.replace(k, str(v))

        if policy:
            body += f"\n\n---\n{policy}"

        return subject, body

    @staticmethod
    def _send_smtp(to_email: str, subject: str, body: str) -> None:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to_email
        msg.set_content(body, charset="utf-8")

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=1) as server:
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

    @staticmethod
    def process_queue(conn: oracledb.Connection, batch_size: int = 10) -> Dict[str, Any]:
        """
        Process pending emails in HANG_DOI_EMAIL using FOR UPDATE SKIP LOCKED.
        """
        max_retries = EmailWorker._get_max_retries(conn)
        sent_count = 0
        retry_count = 0
        failed_count = 0

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT email_id, dat_phong_id, loai_email, ngon_ngu, so_lan_thu
                  FROM hang_doi_email
                 WHERE trang_thai = 'CHO_GUI'
                 ORDER BY ngay_tao ASC, email_id ASC
                   FOR UPDATE SKIP LOCKED
                """
            )
            rows = cur.fetchmany(batch_size)

            for row in rows:
                email_id, dp_id, loai_email, lang, attempts = row
                attempts = int(attempts or 0)
                ctx = EmailWorker._fetch_booking_context(conn, dp_id, lang)
                if not ctx or not ctx.get("email"):
                    cur.execute(
                        """
                        UPDATE hang_doi_email
                           SET trang_thai = 'LOI',
                               so_lan_thu = :attempts,
                               lan_gui_cuoi = SYSTIMESTAMP,
                               loi = :loi
                         WHERE email_id = :email_id
                        """,
                        {
                            "attempts": attempts + 1,
                            "loi": "Không tìm thấy thông tin đơn hoặc email khách hàng",
                            "email_id": email_id,
                        },
                    )
                    failed_count += 1
                    continue

                try:
                    subject, body = EmailWorker._render_email(conn, loai_email, lang, ctx)
                    EmailWorker._send_smtp(ctx["email"], subject, body)
                    cur.execute(
                        """
                        UPDATE hang_doi_email
                           SET trang_thai = 'DA_GUI',
                               lan_gui_cuoi = SYSTIMESTAMP,
                               loi = NULL
                         WHERE email_id = :email_id
                        """,
                        {"email_id": email_id},
                    )
                    sent_count += 1
                    logger.info(f"Sent email #{email_id} ({loai_email}, {lang}) to {ctx['email']}")
                except Exception as exc:
                    new_attempts = attempts + 1
                    new_status = "LOI" if new_attempts >= max_retries else "CHO_GUI"
                    err_text = str(exc)[:950]
                    cur.execute(
                        """
                        UPDATE hang_doi_email
                           SET so_lan_thu = :attempts,
                               trang_thai = :st,
                               lan_gui_cuoi = SYSTIMESTAMP,
                               loi = :loi
                         WHERE email_id = :email_id
                        """,
                        {
                            "attempts": new_attempts,
                            "st": new_status,
                            "loi": err_text,
                            "email_id": email_id,
                        },
                    )
                    if new_status == "LOI":
                        failed_count += 1
                    else:
                        retry_count += 1
                    logger.warning(
                        f"Failed sending email #{email_id} (attempt {new_attempts}/{max_retries} -> {new_status}): {err_text}"
                    )

        conn.commit()
        return {
            "processed": len(rows),
            "sent": sent_count,
            "retrying": retry_count,
            "failed": failed_count,
            "max_retries": max_retries,
        }
