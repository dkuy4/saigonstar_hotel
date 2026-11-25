import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class UserItem(BaseModel):
    id: int
    tenDangNhap: str
    hoTen: str
    vaiTro: str
    trangThai: str
    soLanSai: int = 0
    phaiDoiMatKhau: bool = False
    ngayTao: Optional[str] = None


class UserListResponse(BaseModel):
    success: bool = True
    total: int
    data: list[UserItem]


class UserCreateRequest(BaseModel):
    tenDangNhap: str = Field(..., min_length=3, max_length=30)
    hoTen: str = Field(..., min_length=2, max_length=100)
    vaiTro: str = Field(...)
    matKhau: Optional[str] = None

    @field_validator("tenDangNhap")
    @classmethod
    def validate_username(cls, v: str) -> str:
        clean = v.strip().lower()
        if not re.match(r"^[a-z0-9_]{3,30}$", clean):
            raise ValueError("Tên đăng nhập chỉ gồm chữ thường (a-z), số (0-9) và dấu gạch dưới (_), độ dài 3-30 ký tự")
        return clean

    @field_validator("vaiTro")
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid_roles = {"LE_TAN", "BUONG_PHONG", "QUAN_LY"}
        role = v.strip().upper()
        if role not in valid_roles:
            raise ValueError("Vai trò không hợp lệ. Chỉ chấp nhận LE_TAN, BUONG_PHONG, QUAN_LY")
        return role

    @field_validator("matKhau")
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip() != "":
            if len(v) < 8:
                raise ValueError("Mật khẩu phải có ít nhất 8 ký tự")
            return v
        return None


class UserUpdateRequest(BaseModel):
    hoTen: str = Field(..., min_length=2, max_length=100)
    vaiTro: str = Field(...)

    @field_validator("vaiTro")
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid_roles = {"LE_TAN", "BUONG_PHONG", "QUAN_LY"}
        role = v.strip().upper()
        if role not in valid_roles:
            raise ValueError("Vai trò không hợp lệ. Chỉ chấp nhận LE_TAN, BUONG_PHONG, QUAN_LY")
        return role


class UserLockRequest(BaseModel):
    khoa: bool


class UserCreateResponse(BaseModel):
    success: bool = True
    user: UserItem
    matKhauTam: str
    message: str = "Tạo tài khoản thành công"


class UserResetPasswordResponse(BaseModel):
    success: bool = True
    matKhauTam: str
    message: str = "Đặt lại mật khẩu thành công"
