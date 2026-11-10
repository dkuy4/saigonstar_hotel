from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any

class PaymentGateway(ABC):
    """
    Abstract Payment Gateway Interface (NFR-25).
    Decouples payment providers (Mock, VNPay, MoMo, Stripe) from core hotel business logic.
    """

    @abstractmethod
    def create_payment(self, booking: Dict[str, Any], return_url: str) -> Tuple[str, str]:
        """
        Initiates a payment transaction with the gateway.
        Returns:
            (payment_url, reference_code)
        """
        pass

    @abstractmethod
    def verify_callback(self, data: Dict[str, Any]) -> Tuple[str, bool]:
        """
        Verifies cryptographic signature / validity of the callback payload.
        Returns:
            (reference_code, is_success)
        Raises:
            ValueError or SecurityException on signature mismatch.
        """
        pass

    @abstractmethod
    def refund(self, reference_code: str, amount: float, reason: str) -> bool:
        """
        Requests an automated refund from the payment gateway.
        """
        pass
