from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.catalog import router as catalog_router
from app.routers.bookings import router as bookings_router
from app.routers.payments import router as payments_router
from app.routers.rooms import router as rooms_router
from app.routers.prices import router as prices_router
from app.routers.settings import router as settings_router
from app.routers.translations import router as translations_router
from app.routers.users import router as users_router
from app.routers.reports import router as reports_router
from app.routers.audit import router as audit_router
from app.routers.housekeeping import router as housekeeping_router
from app.routers.refunds import router as refunds_router
from app.routers.reconciliation import router as reconciliation_router
from app.routers.system import router as system_router
from app.routers.guest_auth import router as guest_auth_router

__all__ = ["health_router", "auth_router", "catalog_router", "bookings_router", "payments_router", "rooms_router", "prices_router", "settings_router", "translations_router", "users_router", "reports_router", "audit_router", "housekeeping_router", "refunds_router", "reconciliation_router", "system_router", "guest_auth_router"]
