import re
from typing import Dict, Any, Optional

TIME_REGEX = re.compile(r"^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$")

SETTINGS_META: Dict[str, Dict[str, Any]] = {
    "KHOANG_DEM_PHUT": {
        "ten": "Khoảng đệm dọn phòng",
        "kieu": "SO",
        "don_vi": "phút",
        "min": 0,
        "max": 240,
        "mo_ta": "Khoảng thời gian đệm dọn phòng bắt buộc giữa 2 lượt khách",
        "canh_bao": "Thay đổi này áp dụng cho kiểm tra trùng và đặt phòng mới; đơn đã có không đổi."
    },
    "PHUT_GIU_CHO": {
        "ten": "Thời gian giữ chỗ thanh toán (HOLD)",
        "kieu": "SO",
        "don_vi": "phút",
        "min": 1,
        "max": 120,
        "mo_ta": "Thời gian giữ phòng tạm thời khi khách thanh toán trực tuyến",
        "canh_bao": None
    },
    "NGUONG_GIO_TINH_NGAY": {
        "ten": "Ngưỡng giờ tính trần giá ngày",
        "kieu": "SO",
        "don_vi": "giờ",
        "min": 1,
        "max": 23,
        "mo_ta": "Đơn thuê theo giờ từ ngưỡng này trở lên sẽ tính trần bằng 1 giá ngày",
        "canh_bao": None
    },
    "BUOC_PHUT_DON_GIO": {
        "ten": "Bước phút chọn giờ thuê",
        "kieu": "SO",
        "don_vi": "phút",
        "min": 5,
        "max": 60,
        "mo_ta": "Khoảng bước phút chia ca khi chọn giờ nhận phòng theo giờ (15p, 30p...)",
        "canh_bao": None
    },
    "SO_GIO_TOI_DA_DON_GIO": {
        "ten": "Số giờ thuê tối đa theo giờ",
        "kieu": "SO",
        "don_vi": "giờ",
        "min": 1,
        "max": 24,
        "mo_ta": "Số giờ thuê tối đa trong 1 lượt đặt phòng theo giờ",
        "canh_bao": None
    },
    "GIO_HUY_MIEN_PHI": {
        "ten": "Thời hạn hủy phòng miễn phí",
        "kieu": "SO",
        "don_vi": "giờ",
        "min": 0,
        "max": 168,
        "mo_ta": "Số giờ trước giờ nhận phòng được phép hủy phòng hoàn tiền 100%",
        "canh_bao": None
    },
    "GIO_CHO_NO_SHOW": {
        "ten": "Thời hạn chờ khách không đến (đơn ngày)",
        "kieu": "SO",
        "don_vi": "giờ",
        "min": 0,
        "max": 24,
        "mo_ta": "Số giờ chờ khách nhận phòng đơn ngày trước khi tự động chuyển NO_SHOW",
        "canh_bao": None
    },
    "PHUT_CHO_NO_SHOW_DON_GIO": {
        "ten": "Thời hạn chờ khách không đến (đơn giờ)",
        "kieu": "SO",
        "don_vi": "phút",
        "min": 0,
        "max": 120,
        "mo_ta": "Số phút chờ khách nhận phòng đơn giờ trước khi tự động chuyển NO_SHOW",
        "canh_bao": None
    },
    "PHUT_AN_HAN_QUA_GIO": {
        "ten": "Thời gian ân hạn quá giờ trả",
        "kieu": "SO",
        "don_vi": "phút",
        "min": 0,
        "max": 120,
        "mo_ta": "Số phút cho phép khách trả phòng trễ trước khi bắt đầu tính phụ thu",
        "canh_bao": None
    },
    "SO_DON_CHUA_TT_TOI_DA": {
        "ten": "Số đơn chưa thanh toán tối đa",
        "kieu": "SO",
        "don_vi": "đơn",
        "min": 1,
        "max": 10,
        "mo_ta": "Giới hạn số đơn CONFIRMED chưa thanh toán cùng lúc trên 1 email hoặc SĐT",
        "canh_bao": None
    },
    "SO_LAN_DANG_NHAP_SAI_TOI_DA": {
        "ten": "Số lần đăng nhập sai tối đa",
        "kieu": "SO",
        "don_vi": "lần",
        "min": 1,
        "max": 20,
        "mo_ta": "Số lần đăng nhập sai liên tiếp trước khi khóa tài khoản tạm thời",
        "canh_bao": None
    },
    "PHUT_KHOA_TAM": {
        "ten": "Thời gian khóa tạm tài khoản",
        "kieu": "SO",
        "don_vi": "phút",
        "min": 1,
        "max": 1440,
        "mo_ta": "Số phút khóa tạm tài khoản sau khi đăng nhập sai vượt ngưỡng",
        "canh_bao": None
    },
    "GIO_NHAN_PHONG": {
        "ten": "Giờ nhận phòng chuẩn (đơn ngày)",
        "kieu": "GIO",
        "don_vi": "",
        "min": None,
        "max": None,
        "mo_ta": "Khung giờ nhận phòng chuẩn của đơn theo ngày (định dạng HH:MM)",
        "canh_bao": "Thay đổi này áp dụng cho kiểm tra trùng và đặt phòng mới; đơn đã có không đổi."
    },
    "GIO_TRA_PHONG": {
        "ten": "Giờ trả phòng chuẩn (đơn ngày)",
        "kieu": "GIO",
        "don_vi": "",
        "min": None,
        "max": None,
        "mo_ta": "Khung giờ trả phòng chuẩn của đơn theo ngày (định dạng HH:MM)",
        "canh_bao": "Thay đổi này áp dụng cho kiểm tra trùng và đặt phòng mới; đơn đã có không đổi."
    },
    "THUE_SUAT_VAT": {
        "ten": "Thuế suất VAT dịch vụ lưu trú",
        "kieu": "TY_LE",
        "don_vi": "%",
        "min": 0.0,
        "max": 1.0,
        "mo_ta": "Thuế suất giá trị gia tăng áp dụng tính tiền phòng và dịch vụ",
        "canh_bao": "Cần kế toán trưởng xác nhận văn bản pháp luật trước khi điều chỉnh thuế suất VAT."
    },
    "SO_LAN_THU_EMAIL_TOI_DA": {
        "ten": "Số lần thử gửi email tối đa",
        "kieu": "SO",
        "don_vi": "lần",
        "min": 1,
        "max": 10,
        "mo_ta": "Số lần thử gửi lại email qua SMTP tối đa trước khi đánh dấu LOI (FR-53)",
        "canh_bao": None
    }
}

def validate_setting_value(ma: str, value: Any) -> tuple[bool, Optional[str], Optional[float], Optional[str]]:
    """
    Validates parameter value against rules in settings_meta.
    Returns: (is_valid, error_message, num_val, str_val)
    """
    ma = ma.upper().strip()
    if ma not in SETTINGS_META:
        return False, f"Tham số '{ma}' không tồn tại trong hệ thống", None, None

    meta = SETTINGS_META[ma]
    kieu = meta["kieu"]

    if kieu in ("SO", "TY_LE"):
        try:
            num = float(value)
        except (ValueError, TypeError):
            return False, f"Giá trị của tham số {ma} phải là số", None, None

        if meta["min"] is not None and num < meta["min"]:
            return False, f"Giá trị của {meta['ten']} ({num}) không được nhỏ hơn {meta['min']}", None, None
        if meta["max"] is not None and num > meta["max"]:
            return False, f"Giá trị của {meta['ten']} ({num}) không được lớn hơn {meta['max']}", None, None

        if kieu == "SO" and not float(num).is_integer():
            return False, f"Giá trị của {meta['ten']} phải là số nguyên", None, None

        return True, None, num, None

    elif kieu == "GIO":
        val_str = str(value).strip()
        if not TIME_REGEX.match(val_str):
            return False, f"Giá trị của {meta['ten']} phải có định dạng giờ HH:MM (ví dụ: '14:00')", None, None
        return True, None, None, val_str

    elif kieu == "CHU":
        val_str = str(value).strip()
        if not val_str:
            return False, f"Giá trị của {meta['ten']} không được để trống", None, None
        return True, None, None, val_str

    return False, "Kiểu dữ liệu tham số không được hỗ trợ", None, None
