import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
import oracledb

from app.db import get_conn
from app.context import set_db_context
from app.security import require_role, AuthUser
from app.schemas.refund import (
    RefundCreateRequest,
    RefundOverrideRequest,
    RefundApproveRequest,
    RefundListResponse,
    RefundActionResponse
)
from app.repositories.payment_repo import PaymentRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/refunds", tags=["Refunds"])

@router.get(
    "",
    response_model=RefundListResponse,
    summary="Danh sách yêu cầu hoàn tiền (F12, BR-25, BR-26)"
)
def list_refunds(
    status: Optional[str] = Query(None, description="Lọc theo trạng thái: CHO_DUYET, DA_DUYET, DA_HOAN, TU_CHOI, ALL"),
    booking_id: Optional[int] = Query(None, alias="bookingId", description="Lọc theo mã đơn"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100, alias="pageSize"),
    user: AuthUser = Depends(require_role("LE_TAN", "QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="QUAY")
    res = PaymentRepository.get_refunds(
        conn=conn,
        status=status,
        booking_id=booking_id,
        page=page,
        page_size=page_size
    )
    return RefundListResponse(**res)

@router.post(
    "",
    response_model=RefundActionResponse,
    summary="Tạo yêu cầu hoàn tiền cho đơn đặt phòng (F12, BR-25)"
)
def create_refund(
    payload: RefundCreateRequest,
    user: AuthUser = Depends(require_role("LE_TAN", "QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="QUAY")
    # Lễ tân đề xuất -> CHO_DUYET; Quản lý đề xuất -> có thể duyệt luôn hoặc tạo
    approver_id = user.user_id if user.role == "QUAN_LY" else None
    PaymentRepository.create_refund(
        conn=conn,
        booking_id=payload.booking_id,
        amount=payload.amount,
        reason=payload.reason,
        requester_id=user.user_id,
        approver_id=approver_id
    )
    return {
        "success": True,
        "message": "Đã tạo yêu cầu hoàn tiền thành công",
        "refund_id": 0,
        "status": "DA_DUYET" if approver_id else "CHO_DUYET"
    }

@router.post(
    "/{refund_id}/approve",
    response_model=RefundActionResponse,
    summary="Quản lý phê duyệt hoặc từ chối yêu cầu hoàn tiền (F12, BR-25, BR-26)"
)
def approve_refund(
    refund_id: int,
    payload: RefundApproveRequest,
    user: AuthUser = Depends(require_role("QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="QUAY")
    PaymentRepository.approve_refund(
        conn=conn,
        refund_id=refund_id,
        approver_id=user.user_id,
        approved=payload.approved
    )
    new_status = "DA_DUYET" if payload.approved else "TU_CHOI"
    msg = "Đã phê duyệt yêu cầu hoàn tiền" if payload.approved else "Đã từ chối yêu cầu hoàn tiền"
    return {
        "success": True,
        "message": msg,
        "refund_id": refund_id,
        "status": new_status
    }

@router.post(
    "/{refund_id}/complete",
    response_model=RefundActionResponse,
    summary="Xác nhận đã chi tiền hoàn cho khách (F12, FR-37)"
)
def complete_refund(
    refund_id: int,
    user: AuthUser = Depends(require_role("LE_TAN", "QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="QUAY")
    PaymentRepository.complete_refund(conn=conn, refund_id=refund_id)
    return {
        "success": True,
        "message": "Đã xác nhận hoàn tiền thành công, trạng thái chuyển sang DA_HOAN",
        "refund_id": refund_id,
        "status": "DA_HOAN"
    }

@router.post(
    "/override",
    response_model=RefundActionResponse,
    summary="Quản lý hoàn tiền ngoại lệ ngoài chính sách (F12, BR-26)"
)
def override_refund(
    payload: RefundOverrideRequest,
    user: AuthUser = Depends(require_role("QUAN_LY")),
    conn: oracledb.Connection = Depends(get_conn)
):
    set_db_context(conn, nguoi_id=user.user_id, vai_tro=user.role, kenh="QUAY")
    PaymentRepository.override_refund(
        conn=conn,
        booking_id=payload.booking_id,
        amount=payload.amount,
        reason=payload.reason,
        manager_id=user.user_id
    )
    return {
        "success": True,
        "message": "Đã ghi nhận hoàn tiền ngoại lệ thành công",
        "refund_id": 0,
        "status": "DA_DUYET"
    }
