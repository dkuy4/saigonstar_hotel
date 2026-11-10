import os
import uuid
import logging
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
from app.errors import BusinessException

logger = logging.getLogger(__name__)

# Base directory for storing customer documents
BASE_UPLOAD_DIR = Path("uploads/documents")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

def ensure_upload_dir() -> Path:
    BASE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return BASE_UPLOAD_DIR

async def save_document_photo(file: UploadFile) -> str:
    """
    Saves an uploaded identification document photo outside the database (NFR-13).
    Returns the relative path / URL to be stored in GIAY_TO_KHACH.ANH_URL.
    """
    if not file.filename:
        raise BusinessException(code="VALIDATION_ERROR", detail="Tập tin tải lên không hợp lệ")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise BusinessException(
            code="VALIDATION_ERROR",
            detail=f"Định dạng tập tin {ext} không được hỗ trợ. Chấp nhận: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    upload_dir = ensure_upload_dir()
    file_id = uuid.uuid4().hex
    filename = f"doc_{file_id}{ext}"
    target_path = upload_dir / filename

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise BusinessException(
            code="VALIDATION_ERROR",
            detail=f"Kích thước tập tin vượt quá giới hạn tối đa ({MAX_FILE_SIZE // (1024*1024)}MB)"
        )

    with open(target_path, "wb") as f:
        f.write(content)

    logger.info(f"Saved document photo: {target_path} (size={len(content)} bytes)")
    return f"/uploads/documents/{filename}"
