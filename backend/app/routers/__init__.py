from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.catalog import router as catalog_router
from app.routers.bookings import router as bookings_router
from app.routers.payments import router as payments_router
from app.routers.rooms import router as rooms_router

__all__ = ["health_router", "auth_router", "catalog_router", "bookings_router", "payments_router", "rooms_router"]
