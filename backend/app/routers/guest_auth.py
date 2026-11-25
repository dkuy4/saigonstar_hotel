from datetime import datetime, timezone
from typing import Optional, List
import oracledb
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.db import get_conn
from app.context import set_db_context
from app.security import (
    create_access_token,
    verify_password,
    hash_password,
    get_current_user
)

router = APIRouter(prefix="/guest", tags=["Khách Hàng (Tài Khoản & Chuyến Đi)"])


# --- Schemas ---

class GuestRegisterRequest(BaseModel):
    ho_ten: str = Field(..., min_length=2, max_length=100, description="Họ và tên khách hàng")
    sdt: str = Field(..., min_length=8, max_length=20, description="Số điện thoại liên hệ")
    email: str = Field(..., description="Địa chỉ email đăng ký")
    mat_khau: str = Field(..., min_length=6, description="Mật khẩu tài khoản (tối thiểu 6 ký tự)")
    quoc_tich: Optional[str] = Field("VNM", description="Mã quốc tịch")
    ngon_ngu: Optional[str] = Field("vi", description="Ngôn ngữ ưu tiên")


class GuestLoginRequest(BaseModel):
    tai_khoan: str = Field(..., description="Email hoặc Số điện thoại đăng ký")
    mat_khau: str = Field(..., description="Mật khẩu tài khoản")


class GuestForgotPasswordRequest(BaseModel):
    email: str = Field(..., description="Email đã đăng ký")
    sdt: str = Field(..., description="Số điện thoại đã đăng ký")
    ho_ten: str = Field(..., description="Họ tên chính xác đã đăng ký")
    mat_khau_moi: str = Field(..., min_length=6, description="Mật khẩu mới muốn đặt")


class GuestProfileResponse(BaseModel):
    khach_hang_id: int
    ho_ten: str
    sdt: str
    email: str
    quoc_tich: Optional[str]
    ngon_ngu_uu_tien: str
    role: str = "KHACH"


class GuestAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: GuestProfileResponse


class BookingSummaryItem(BaseModel):
    dat_phong_id: int
    ma_tra_cuu: str
    loai_dat: str
    kenh_dat: str
    trang_thai: str
    tu_luc: str
    den_luc: str
    so_khach: int
    tien_phong: float
    tien_vat: float
    tong_tien: float
    ma_hang: Optional[str] = None
    ten_hang: Optional[str] = None
    so_phong: Optional[str] = None
    ngay_tao: str


# --- Endpoints ---

@router.post("/register", response_model=GuestAuthResponse, status_code=status.HTTP_201_CREATED)
def register_guest(req: GuestRegisterRequest, conn: oracledb.Connection = Depends(get_conn)):
    """Đăng ký tài khoản khách hàng mới."""
    cur = conn.cursor()
    set_db_context(conn, vai_tro="KHACH", kenh="WEB", ly_do="DANG_KY_KHACH")

    # Kiểm tra xem email hoặc sdt đã có tài khoản mật khẩu chưa
    cur.execute(
        """
        SELECT khach_hang_id, mat_khau_bam 
        FROM hotel_owner.khach_hang 
        WHERE email = :email OR sdt = :sdt
        """,
        {"email": req.email.strip().lower(), "sdt": req.sdt.strip()}
    )
    existing = cur.fetchone()
    hashed_pwd = hash_password(req.mat_khau)

    if existing:
        khach_id, existing_pwd = existing[0], existing[1]
        if existing_pwd:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email hoặc số điện thoại này đã được đăng ký tài khoản. Quý khách vui lòng đăng nhập hoặc dùng chức năng quên mật khẩu."
            )
        # Nếu đã có thông tin từ lần đặt phòng trước nhưng chưa có tài khoản mật khẩu, cập nhật lại
        cur.execute(
            """
            UPDATE hotel_owner.khach_hang
            SET ho_ten = :ho_ten,
                mat_khau_bam = :pwd,
                ngay_dang_ky = SYSTIMESTAMP,
                quoc_tich = :quoc_tich,
                ngon_ngu_uu_tien = :lang
            WHERE khach_hang_id = :kid
            """,
            {
                "ho_ten": req.ho_ten.strip(),
                "pwd": hashed_pwd,
                "quoc_tich": req.quoc_tich or "VNM",
                "lang": req.ngon_ngu or "vi",
                "kid": khach_id
            }
        )
    else:
        # Tạo mới khách hàng (KHACH_HANG_ID là IDENTITY)
        cur.execute(
            """
            INSERT INTO hotel_owner.khach_hang (
                ho_ten, sdt, email, quoc_tich, ngon_ngu_uu_tien, ngay_tao, mat_khau_bam, ngay_dang_ky
            ) VALUES (
                :ho_ten, :sdt, :email, :quoc_tich, :lang, SYSTIMESTAMP, :pwd, SYSTIMESTAMP
            ) RETURNING khach_hang_id INTO :new_id
            """,
            {
                "ho_ten": req.ho_ten.strip(),
                "sdt": req.sdt.strip(),
                "email": req.email.strip().lower(),
                "quoc_tich": req.quoc_tich or "VNM",
                "lang": req.ngon_ngu or "vi",
                "pwd": hashed_pwd,
                "new_id": cur.var(oracledb.NUMBER)
            }
        )
        khach_id = int(cur.bindvars["new_id"].getvalue()[0])

    conn.commit()

    profile = GuestProfileResponse(
        khach_hang_id=khach_id,
        ho_ten=req.ho_ten.strip(),
        sdt=req.sdt.strip(),
        email=req.email.strip().lower(),
        quoc_tich=req.quoc_tich,
        ngon_ngu_uu_tien=req.ngon_ngu or "vi"
    )

    token = create_access_token(
        data={"sub": str(khach_id), "role": "KHACH", "name": req.ho_ten.strip(), "email": req.email.strip().lower()}
    )

    return GuestAuthResponse(access_token=token, user=profile)


@router.post("/login", response_model=GuestAuthResponse)
def login_guest(req: GuestLoginRequest, conn: oracledb.Connection = Depends(get_conn)):
    """Đăng nhập bằng Email hoặc Số điện thoại."""
    cur = conn.cursor()
    account_input = req.tai_khoan.strip().lower()

    cur.execute(
        """
        SELECT khach_hang_id, ho_ten, sdt, email, quoc_tich, ngon_ngu_uu_tien, mat_khau_bam
        FROM hotel_owner.khach_hang
        WHERE LOWER(email) = :acc OR sdt = :acc
        """,
        {"acc": account_input}
    )
    row = cur.fetchone()
    if not row or not row[6]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thông tin đăng nhập hoặc mật khẩu không chính xác. Xin quý khách kiểm tra lại."
        )

    khach_id, ho_ten, sdt, email, quoc_tich, lang, hashed_pwd = row

    if not verify_password(req.mat_khau, hashed_pwd):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Thông tin đăng nhập hoặc mật khẩu không chính xác. Xin quý khách kiểm tra lại."
        )

    profile = GuestProfileResponse(
        khach_hang_id=khach_id,
        ho_ten=ho_ten,
        sdt=sdt,
        email=email,
        quoc_tich=quoc_tich,
        ngon_ngu_uu_tien=lang or "vi"
    )

    token = create_access_token(
        data={"sub": str(khach_id), "role": "KHACH", "name": ho_ten, "email": email}
    )

    return GuestAuthResponse(access_token=token, user=profile)


@router.post("/forgot-password")
def forgot_password_guest(req: GuestForgotPasswordRequest, conn: oracledb.Connection = Depends(get_conn)):
    """Đặt lại mật khẩu dựa trên thông tin định danh trùng khớp (không dùng OTP)."""
    cur = conn.cursor()
    set_db_context(conn, vai_tro="KHACH", kenh="WEB", ly_do="QUEN_MAT_KHAU")

    cur.execute(
        """
        SELECT khach_hang_id, ho_ten, mat_khau_bam
        FROM hotel_owner.khach_hang
        WHERE LOWER(email) = :email AND sdt = :sdt
        """,
        {"email": req.email.strip().lower(), "sdt": req.sdt.strip()}
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy thông tin tài khoản phù hợp với email và số điện thoại đã cung cấp."
        )

    khach_id, ho_ten_db, mat_khau_db = row
    if req.ho_ten.strip().lower() not in ho_ten_db.lower() and ho_ten_db.lower() not in req.ho_ten.strip().lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Họ và tên không khớp với hồ sơ lưu trú đã đăng ký."
        )

    # Đổi mật khẩu mới
    new_hashed = hash_password(req.mat_khau_moi)
    cur.execute(
        """
        UPDATE hotel_owner.khach_hang
        SET mat_khau_bam = :pwd,
            ngay_dang_ky = NVL(ngay_dang_ky, SYSTIMESTAMP)
        WHERE khach_hang_id = :kid
        """,
        {"pwd": new_hashed, "kid": khach_id}
    )
    conn.commit()

    return {
        "success": True,
        "message": "Đặt lại mật khẩu thành công. Quý khách có thể đăng nhập ngay bằng mật khẩu mới."
    }


@router.get("/me", response_model=GuestProfileResponse)
def get_guest_profile(
    current_user = Depends(get_current_user),
    conn: oracledb.Connection = Depends(get_conn)
):
    """Lấy thông tin tài khoản khách đang đăng nhập."""
    role = getattr(current_user, "role", None) or (current_user.get("role") if isinstance(current_user, dict) else None)
    khach_id = getattr(current_user, "user_id", None) or (int(current_user["sub"]) if isinstance(current_user, dict) and "sub" in current_user else None)
    user_email = getattr(current_user, "email", None) or (current_user.get("email") if isinstance(current_user, dict) else "")
    username = getattr(current_user, "username", "")

    cur = conn.cursor()
    if role != "KHACH":
        cur.execute(
            """
            SELECT khach_hang_id, ho_ten, sdt, email, quoc_tich, ngon_ngu_uu_tien
            FROM hotel_owner.khach_hang
            WHERE (email IS NOT NULL AND LOWER(email) = LOWER(:em))
               OR sdt = :un
               OR LOWER(email) = LOWER(:un)
               AND ROWNUM = 1
            """,
            {"em": user_email or username, "un": username}
        )
        row = cur.fetchone()
        if row:
            return GuestProfileResponse(
                khach_hang_id=row[0],
                ho_ten=row[1],
                sdt=row[2],
                email=row[3],
                quoc_tich=row[4],
                ngon_ngu_uu_tien=row[5] or "vi"
            )
        return GuestProfileResponse(
            khach_hang_id=khach_id or 0,
            ho_ten=getattr(current_user, "full_name", "Quý khách"),
            sdt="",
            email=user_email,
            quoc_tich="VNM",
            ngon_ngu_uu_tien="vi"
        )

    cur.execute(
        """
        SELECT khach_hang_id, ho_ten, sdt, email, quoc_tich, ngon_ngu_uu_tien
        FROM hotel_owner.khach_hang
        WHERE khach_hang_id = :kid
        """,
        {"kid": khach_id}
    )
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy thông tin khách hàng.")

    return GuestProfileResponse(
        khach_hang_id=row[0],
        ho_ten=row[1],
        sdt=row[2],
        email=row[3],
        quoc_tich=row[4],
        ngon_ngu_uu_tien=row[5] or "vi"
    )


@router.get("/my-bookings", response_model=List[BookingSummaryItem])
def get_guest_bookings(
    current_user = Depends(get_current_user),
    conn: oracledb.Connection = Depends(get_conn)
):
    """Danh sách các chuyến đi/đơn đặt phòng của khách hàng đang đăng nhập."""
    role = getattr(current_user, "role", None) or (current_user.get("role") if isinstance(current_user, dict) else None)
    khach_id = getattr(current_user, "user_id", None) or (int(current_user["sub"]) if isinstance(current_user, dict) and "sub" in current_user else None)
    user_email = getattr(current_user, "email", None) or (current_user.get("email") if isinstance(current_user, dict) else "")
    username = getattr(current_user, "username", "")

    cur = conn.cursor()
    if role != "KHACH":
        cur.execute(
            """
            SELECT khach_hang_id, email FROM hotel_owner.khach_hang
            WHERE (email IS NOT NULL AND LOWER(email) = LOWER(:em))
               OR sdt = :un
               OR LOWER(email) = LOWER(:un)
               AND ROWNUM = 1
            """,
            {"em": user_email or username, "un": username}
        )
        found = cur.fetchone()
        if found:
            khach_id = found[0]
            user_email = found[1] or ""
        else:
            return []
    cur.execute(
        """
        SELECT 
            dp.dat_phong_id,
            dp.ma_tra_cuu,
            dp.loai_dat,
            dp.kenh_dat,
            dp.trang_thai,
            TO_CHAR(dp.tu_luc, 'YYYY-MM-DD"T"HH24:MI:SSTZH:TZM'),
            TO_CHAR(dp.den_luc, 'YYYY-MM-DD"T"HH24:MI:SSTZH:TZM'),
            dp.so_khach,
            dp.tien_phong,
            dp.tien_vat,
            dp.tong_tien,
            (SELECT lp.ma_hang FROM hotel_owner.dat_phong_doan dpd
               JOIN hotel_owner.phong p ON p.phong_id = dpd.phong_id
               JOIN hotel_owner.loai_phong lp ON lp.loai_phong_id = p.loai_phong_id
              WHERE dpd.dat_phong_id = dp.dat_phong_id AND ROWNUM = 1) AS ma_hang,
            (SELECT lpd.ten FROM hotel_owner.dat_phong_doan dpd
               JOIN hotel_owner.phong p ON p.phong_id = dpd.phong_id
               JOIN hotel_owner.loai_phong lp ON lp.loai_phong_id = p.loai_phong_id
               LEFT JOIN hotel_owner.loai_phong_dich lpd ON (lpd.loai_phong_id = lp.loai_phong_id AND lpd.ngon_ngu = 'vi')
              WHERE dpd.dat_phong_id = dp.dat_phong_id AND ROWNUM = 1) AS ten_hang,
            (SELECT p.ma_phong FROM hotel_owner.dat_phong_doan dpd
               JOIN hotel_owner.phong p ON p.phong_id = dpd.phong_id
              WHERE dpd.dat_phong_id = dp.dat_phong_id AND ROWNUM = 1) AS so_phong,
            TO_CHAR(dp.ngay_tao, 'YYYY-MM-DD"T"HH24:MI:SSTZH:TZM')
        FROM hotel_owner.dat_phong dp
        LEFT JOIN hotel_owner.khach_hang kh ON dp.khach_hang_id = kh.khach_hang_id
        WHERE dp.khach_hang_id = :kid 
           OR dp.nguoi_tao_id = :kid 
           OR (kh.email IS NOT NULL AND LOWER(kh.email) = LOWER(:email))
        ORDER BY dp.ngay_tao DESC
        """,
        {"kid": khach_id, "email": user_email}
    )

    items = []
    for r in cur.fetchall():
        items.append(BookingSummaryItem(
            dat_phong_id=r[0],
            ma_tra_cuu=r[1],
            loai_dat=r[2],
            kenh_dat=r[3],
            trang_thai=r[4],
            tu_luc=r[5],
            den_luc=r[6],
            so_khach=r[7],
            tien_phong=float(r[8] or 0),
            tien_vat=float(r[9] or 0),
            tong_tien=float(r[10] or 0),
            ma_hang=r[11],
            ten_hang=r[12],
            so_phong=r[13],
            ngay_tao=r[14]
        ))

    return items
