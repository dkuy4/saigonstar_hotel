from typing import Optional
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, description="Tên đăng nhập")
    password: str = Field(..., min_length=1, description="Mật khẩu")

class UserInfo(BaseModel):
    id: int
    username: str
    name: str
    role: str

class LoginResponseData(BaseModel):
    token: str
    expires_at: str = Field(alias="expiresAt")
    user: UserInfo

    model_config = {"populate_by_name": True}

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, alias="currentPassword")
    new_password: str = Field(..., min_length=8, alias="newPassword", description="Mật khẩu mới tối thiểu 8 ký tự")

    model_config = {"populate_by_name": True}
