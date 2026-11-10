import hmac
import hashlib
import uuid
import logging
from typing import Tuple, Dict, Any
from app.config import settings
from app.services.payment.base import PaymentGateway

logger = logging.getLogger(__name__)

class MockPaymentGateway(PaymentGateway):
    """
    In-app Mock Payment Gateway for local development, demo, and automated testing (D-36).
    Uses HMAC-SHA256 signatures to simulate banking/fintech gateway security.
    """

    def __init__(self, secret_key: str = None):
        self.secret_key = (secret_key or settings.JWT_SECRET).encode("utf-8")

    def generate_signature(self, reference_code: str, is_success: bool) -> str:
        data_str = f"{reference_code}:{1 if is_success else 0}"
        return hmac.new(self.secret_key, data_str.encode("utf-8"), hashlib.sha256).hexdigest()

    def create_payment(self, booking: Dict[str, Any], return_url: str = "") -> Tuple[str, str]:
        reference_code = f"MOCK_{uuid.uuid4().hex[:12].upper()}"
        amount = booking.get("total_amount", 0)
        code = booking.get("booking_code", "")

        # Generates payment redirect URL to the Mock Gateway interface
        payment_url = f"/mock-pay/{reference_code}?amount={amount}&code={code}"
        logger.info(f"Created mock payment {reference_code} for booking {code}, amount {amount}")
        return payment_url, reference_code

    def verify_callback(self, data: Dict[str, Any]) -> Tuple[str, bool]:
        reference_code = data.get("reference_code") or data.get("maThamChieu")
        if not reference_code:
            raise ValueError("Missing reference_code in callback")

        raw_success = data.get("is_success")
        if raw_success is None:
            raw_success = data.get("thanhCong")
        if raw_success is None:
            raise ValueError("Missing success status in callback")

        is_success = bool(raw_success)
        signature = data.get("signature") or data.get("chuKy")

        expected_sig = self.generate_signature(reference_code, is_success)
        if not signature or not hmac.compare_digest(signature, expected_sig):
            logger.warning(f"Signature mismatch for mock payment {reference_code}")
            raise ValueError("Invalid callback signature")

        return reference_code, is_success

    def refund(self, reference_code: str, amount: float, reason: str) -> bool:
        logger.info(f"Mock gateway refunded {amount} VND for {reference_code}. Reason: {reason}")
        return True
