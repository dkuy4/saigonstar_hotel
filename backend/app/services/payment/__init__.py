from app.services.payment.base import PaymentGateway
from app.services.payment.mock import MockPaymentGateway

_default_gateway = MockPaymentGateway()

def get_payment_gateway() -> PaymentGateway:
    """Returns the configured payment gateway instance."""
    return _default_gateway

__all__ = ["PaymentGateway", "MockPaymentGateway", "get_payment_gateway"]
