"""
Router Quản lý Bản dịch chính sách và Mẫu email (F16.5, FR-33, BR-55).
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, status
import oracledb

from app.db import get_conn
from app.security import require_role, AuthUser
from app.schemas.translation import (
    TranslationItem,
    TranslationMatrixItem,
    TranslationUpdateRequest,
    TranslationUpdateResponse,
)
from app.repositories.translation_repo import TranslationRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/translations", tags=["Quản trị Bản dịch"])

@router.get(
    "",
    response_model=List[TranslationMatrixItem],
    summary="Lấy ma trận bản dịch 7 ngôn ngữ cho chính sách và mẫu email (F16.5)",
)
def get_translations(
    ma: Optional[str] = Query(None, description="Lọc theo mã nội dung (ví dụ: CHINH_SACH_HUY)"),
    lang: Optional[str] = Query(None, description="Lọc theo mã ngôn ngữ (ví dụ: vi, en, ko)"),
    current_user: AuthUser = Depends(require_role("QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn),
):
    return TranslationRepository.get_translations(conn, ma_noi_dung=ma, ngon_ngu=lang)

@router.get(
    "/public",
    response_model=List[TranslationMatrixItem],
    summary="Tra cứu bản dịch chính sách công khai cho khách hàng",
)
def get_public_translations(
    ma: Optional[str] = Query(None, description="Mã nội dung chính sách"),
    lang: Optional[str] = Query(None, description="Mã ngôn ngữ"),
    conn: oracledb.Connection = Depends(get_conn),
):
    return TranslationRepository.get_translations(conn, ma_noi_dung=ma, ngon_ngu=lang)

@router.get(
    "/{ma}/{lang}",
    response_model=TranslationItem,
    summary="Lấy chi tiết một bản dịch cụ thể",
)
def get_single_translation(
    ma: str = Path(..., description="Mã nội dung"),
    lang: str = Path(..., description="Mã ngôn ngữ"),
    conn: oracledb.Connection = Depends(get_conn),
):
    return TranslationRepository.get_single_translation(conn, ma_noi_dung=ma, ngon_ngu=lang)

@router.put(
    "/{ma}/{lang}",
    response_model=TranslationUpdateResponse,
    summary="Cập nhật bản dịch chính sách hoặc mẫu email (Chỉ Quản lý - F16.5)",
)
def update_translation(
    payload: TranslationUpdateRequest,
    ma: str = Path(..., description="Mã nội dung"),
    lang: str = Path(..., description="Mã ngôn ngữ"),
    current_user: AuthUser = Depends(require_role("QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn),
):
    return TranslationRepository.upsert_translation(
        conn=conn,
        ma_noi_dung=ma,
        ngon_ngu=lang,
        noi_dung=payload.noi_dung,
        current_user=current_user,
    )
