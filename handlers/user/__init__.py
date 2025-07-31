# handlers/user/__init__.py
from .start import router as start_router
from .menu import router as menu_router
from .catalog import router as catalog_router
from .payment import router as payment_router
from .navigation import router as navigation_router


__all__ = \
    [
    "start_router",
    "menu_router",
    "catalog_router",
    "payment_router",
    "navigation_router"
    ]