"""
F11: Invoice PDF service – tạo PDF hóa đơn từ HTML template.
Dùng WeasyPrint nếu có; fallback sang HTML tĩnh.
"""
import logging
import os
import tempfile
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Thử import WeasyPrint (cài sẵn trong Docker)
_WEASYPRINT_AVAILABLE = False
try:
    from weasyprint import HTML as WeasyHTML
    _WEASYPRINT_AVAILABLE = True
except ImportError:
    logger.warning("WeasyPrint not available – will serve printable HTML instead of PDF")


def _fmt_vnd(amount: float) -> str:
    """Format VND với dấu phân cách hàng nghìn."""
    sign = "-" if amount < 0 else ""
    return f"{sign}{abs(amount):,.0f} ₫"


def _fmt_dt(dt) -> str:
    """Format datetime ISO → DD/MM/YYYY HH:MM."""
    if dt is None:
        return "—"
    if hasattr(dt, "strftime"):
        return dt.strftime("%d/%m/%Y %H:%M")
    try:
        return datetime.fromisoformat(str(dt)).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(dt)


def build_invoice_html(invoice: Dict[str, Any]) -> str:
    """
    Tạo HTML hóa đơn từ dict invoice (kết quả InvoiceRepository.get_invoice).
    Dùng Tailwind-compatible inline CSS để in đẹp.
    """
    lines = invoice.get("chiTiet") or invoice.get("lines", [])
    total = float(invoice.get("tongTien") or invoice.get("total_amount") or 0)
    inv_number = invoice.get("soHoaDon") or invoice.get("invoice_number") or 0
    is_adjust = invoice.get("laDieuChinh") or invoice.get("is_adjustment") or False
    issued_at = _fmt_dt(invoice.get("ngayLap") or invoice.get("issued_at"))
    created_by = invoice.get("nguoiLap") or invoice.get("created_by") or "—"

    guest_name = invoice.get("hoTen") or invoice.get("customer_name") or "—"
    guest_phone = invoice.get("sdt") or invoice.get("customer_phone") or "—"
    room_number = invoice.get("maPhong") or invoice.get("room_number") or "—"
    room_type = invoice.get("maHang") or invoice.get("room_type") or "—"
    checkin = _fmt_dt(invoice.get("nhanThucTe") or invoice.get("actual_checkin") or invoice.get("checkin"))
    checkout = _fmt_dt(invoice.get("traThucTe") or invoice.get("actual_checkout") or invoice.get("checkout"))

    type_label = "ĐIỀU CHỈNH" if is_adjust else "NỘI BỘ"
    goc_id = invoice.get("hoaDonGocId") or invoice.get("original_invoice_id")
    goc_note = f"<p style='color:#b45309;font-size:12px;margin:0'>Điều chỉnh cho HĐ gốc #{goc_id}</p>" if goc_note_cond := (is_adjust and goc_id) else ""  # noqa

    # Lines HTML
    lines_html = ""
    line_type_labels = {
        "TIEN_PHONG": "Tiền phòng",
        "QUA_GIO": "Ở quá giờ trả phòng",
        "PHU_THU": "Phụ thu",
        "GIAM_GIA": "Giảm giá",
        "VAT": "Thuế GTGT",
    }
    for line in lines:
        lt = line.get("loaiDong") or line.get("line_type", "")
        desc = line.get("moTa") or line.get("description", lt)
        amt = float(line.get("soTien") or line.get("amount") or 0)
        vat_rate = line.get("thueSuat") or line.get("vat_rate")
        label = line_type_labels.get(lt, lt)
        if vat_rate:
            desc = f"{desc} ({round(vat_rate * 100)}%)"
        color = "#dc2626" if amt < 0 else "#1e293b"
        lines_html += f"""
        <tr>
            <td style="padding:8px 12px;font-size:13px;border-bottom:1px solid #e2e8f0">{label}</td>
            <td style="padding:8px 12px;font-size:13px;border-bottom:1px solid #e2e8f0;color:#64748b">{desc}</td>
            <td style="padding:8px 12px;font-size:13px;border-bottom:1px solid #e2e8f0;text-align:right;font-family:monospace;font-weight:600;color:{color}">{_fmt_vnd(amt)}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <title>Hóa đơn #{inv_number} – Khách sạn Sài Gòn Star</title>
  <style>
    @media print {{
      body {{ margin: 0; }}
      .no-print {{ display: none !important; }}
      @page {{ size: A4; margin: 1.5cm; }}
    }}
    body {{ font-family: 'Helvetica Neue', Arial, sans-serif; color: #1e293b; background: #f8fafc; margin: 0; padding: 24px; }}
    .card {{ background: #fff; border-radius: 12px; box-shadow: 0 1px 8px rgba(0,0,0,.08); max-width: 720px; margin: 0 auto; padding: 36px 40px; }}
    h1 {{ font-size: 22px; font-weight: 900; margin: 0 0 2px; letter-spacing: -0.5px; }}
    .subtitle {{ font-size: 12px; color: #64748b; margin: 0 0 24px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    .total-row td {{ font-size: 15px; font-weight: 800; padding: 12px; background: #0f172a; color: #f8fafc; border-radius: 8px; }}
    .print-btn {{ display: block; margin: 24px auto 0; padding: 10px 28px; background: #0f172a; color: #fff; border: none; border-radius: 8px; font-size: 14px; font-weight: 700; cursor: pointer; }}
  </style>
</head>
<body>
  <div class="card">
    <!-- Header -->
    <div style="display:flex;justify-content:space-between;align-items:flex-start;border-bottom:2px solid #e2e8f0;padding-bottom:20px;margin-bottom:20px">
      <div>
        <h1>🏨 Khách sạn Sài Gòn Star</h1>
        <p class="subtitle">HÓA ĐƠN {type_label}</p>
        {(f"<p style='color:#b45309;font-size:12px;margin:0'>Điều chỉnh cho HĐ gốc #{goc_id}</p>" if is_adjust and goc_id else "")}
      </div>
      <div style="text-align:right">
        <div style="font-size:28px;font-weight:900;font-family:monospace;color:#0f172a">#{inv_number}</div>
        <div style="font-size:11px;color:#64748b">Ngày lập: {issued_at}</div>
        <div style="font-size:11px;color:#64748b">Nhân viên: {created_by}</div>
      </div>
    </div>

    <!-- Guest & Stay Info -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:24px">
      <div style="background:#f1f5f9;border-radius:8px;padding:14px">
        <div style="font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;margin-bottom:6px">Khách hàng</div>
        <div style="font-size:14px;font-weight:700;margin-bottom:2px">{guest_name}</div>
        <div style="font-size:12px;color:#475569">📞 {guest_phone}</div>
      </div>
      <div style="background:#f1f5f9;border-radius:8px;padding:14px">
        <div style="font-size:10px;font-weight:700;color:#94a3b8;text-transform:uppercase;margin-bottom:6px">Thông tin lưu trú</div>
        <div style="font-size:13px;font-weight:600">Phòng {room_number} · {room_type}</div>
        <div style="font-size:11px;color:#475569">Nhận: {checkin}</div>
        <div style="font-size:11px;color:#475569">Trả:  {checkout}</div>
      </div>
    </div>

    <!-- Line Items -->
    <table>
      <thead>
        <tr style="background:#f8fafc;font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase">
          <th style="padding:8px 12px;text-align:left">Khoản mục</th>
          <th style="padding:8px 12px;text-align:left">Mô tả</th>
          <th style="padding:8px 12px;text-align:right">Số tiền</th>
        </tr>
      </thead>
      <tbody>
        {lines_html}
      </tbody>
      <tfoot>
        <tr class="total-row">
          <td colspan="2" style="border-radius:8px 0 0 8px">TỔNG CỘNG</td>
          <td style="text-align:right;font-family:monospace;font-size:17px;border-radius:0 8px 8px 0">{_fmt_vnd(total)}</td>
        </tr>
      </tfoot>
    </table>

    <p style="font-size:11px;color:#94a3b8;margin-top:20px;text-align:center">
      Hóa đơn nội bộ — Không có giá trị khai thuế • Khách sạn Sài Gòn Star
    </p>

    <button class="print-btn no-print" onclick="window.print()">🖨 In hóa đơn</button>
  </div>
</body>
</html>"""


def generate_invoice_pdf(invoice: Dict[str, Any]) -> bytes:
    """
    Sinh PDF bytes từ dict invoice.
    Nếu WeasyPrint không có thì raise ImportError để router trả HTML.
    """
    if not _WEASYPRINT_AVAILABLE:
        raise ImportError("WeasyPrint unavailable")

    html_str = build_invoice_html(invoice)
    return WeasyHTML(string=html_str, base_url=".").write_pdf()
