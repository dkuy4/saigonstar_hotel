import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
import oracledb

from app.db import get_conn
from app.errors import BusinessException
from app.repositories.booking_repo import BookingRepository
from app.repositories.payment_repo import PaymentRepository
from app.services.payment import get_payment_gateway, MockPaymentGateway
from app.schemas.payment import (
    OnlinePaymentInitRequest,
    OnlinePaymentInitResponse,
    PaymentCallbackRequest,
    PaymentCallbackResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments & Gateways"])

@router.post(
    "/online",
    response_model=OnlinePaymentInitResponse,
    summary="Khởi tạo giao dịch thanh toán trực tuyến cho đơn HOLD (FR-07, FR-35, BR-17)"
)
def init_online_payment(
    payload: OnlinePaymentInitRequest,
    conn: oracledb.Connection = Depends(get_conn)
):
    # 1. Fetch booking by code
    booking = BookingRepository.get_booking_by_code(conn, payload.booking_code)
    if not booking:
        raise BusinessException("BOOKING_NOT_FOUND", f"Không tìm thấy đơn đặt phòng {payload.booking_code}")

    # 2. Check ownership by email
    if booking["customer"].email.lower() != payload.email.lower().strip():
        raise BusinessException("BOOKING_NOT_FOUND", "Mã đơn hoặc email không trùng khớp")

    # 3. Check status is HOLD
    if booking["status"] != "HOLD":
        raise BusinessException("HOLD_EXPIRED", f"Đơn {payload.booking_code} không ở trạng thái giữ chỗ (HOLD)")

    # 4. Create transaction reference via Payment Gateway
    gateway = get_payment_gateway()
    payment_url, reference_code = gateway.create_payment(
        booking=booking,
        return_url=payload.return_url or "/thanh-toan/ket-qua"
    )

    # 5. Record pending gateway transaction in Oracle
    PaymentRepository.create_gateway_transaction(
        conn=conn,
        booking_id=booking["id"],
        reference_code=reference_code
    )

    return OnlinePaymentInitResponse(
        paymentUrl=payment_url,
        referenceCode=reference_code,
        amount=booking["total_amount"],
        expiresAt=booking["hold_expires_at"],
        bookingCode=booking["booking_code"]
    )

@router.post(
    "/callback",
    response_model=PaymentCallbackResponse,
    summary="Webhook / Callback tiếp nhận kết quả từ cổng thanh toán (FR-35, FR-36, BR-18, BR-19)"
)
def payment_callback(
    payload: PaymentCallbackRequest,
    conn: oracledb.Connection = Depends(get_conn)
):
    gateway = get_payment_gateway()

    # 1. Cryptographic signature check
    try:
        ref_code, is_success = gateway.verify_callback(payload.model_dump())
    except Exception as e:
        logger.warning(f"Signature verification failed: {e}")
        raise BusinessException("UNAUTHORIZED", "Chữ ký callback thanh toán không hợp lệ")

    # 2. Process callback in Oracle via PKG_THANH_TOAN.XU_LY_KET_QUA_CONG
    result = PaymentRepository.process_gateway_callback(
        conn=conn,
        reference_code=ref_code,
        is_success=is_success
    )

    messages = {
        "XAC_NHAN": "Đơn đặt phòng đã được thanh toán và xác nhận thành công.",
        "XAC_NHAN_MUON": "Thanh toán thành công (ghi nhận thanh toán về muộn).",
        "HOAN_TIEN": "Thanh toán về muộn và phòng đã hết, hệ thống đã khởi tạo hoàn tiền 100% (BR-19).",
        "THAT_BAI": "Giao dịch thanh toán thất bại hoặc bị hủy.",
        "DA_XU_LY": "Giao dịch này đã được hệ thống ghi nhận trước đó (Idempotent)."
    }

    return PaymentCallbackResponse(
        status="success",
        result=result,
        referenceCode=ref_code,
        message=messages.get(result, f"Kết quả: {result}")
    )

@router.get(
    "/mock-info/{ref}",
    summary="Lấy thông tin và tạo chữ ký kiểm thử cho Mock Gateway UI"
)
def get_mock_payment_info(
    ref: str,
    conn: oracledb.Connection = Depends(get_conn)
):
    info = PaymentRepository.get_payment_info_by_ref(conn, ref)
    if not info:
        raise BusinessException("PAYMENT_NOT_FOUND", f"Không tìm thấy giao dịch {ref}")

    gateway = get_payment_gateway()
    sig_success = ""
    sig_fail = ""
    if isinstance(gateway, MockPaymentGateway):
        sig_success = gateway.generate_signature(ref, True)
        sig_fail = gateway.generate_signature(ref, False)

    return {
        "info": info,
        "signatures": {
            "success": sig_success,
            "fail": sig_fail
        }
    }
