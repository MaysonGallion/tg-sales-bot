# tg-sales-bot/handlers/admin/__init__.py
from .access import router as access_router
from .add_product import router as add_product_router
from .list_products import router as list_products_router
from .edit_product import router as edit_product_router
from .orders import router as orders_router
from .promos import router as promos_router
from .menu import router as admin_menu_router
from .pages import router as pages_router
from .consents import router as consents_router
from .dicts import router as dicts_router  # NEW

__all__ = [
    "access_router",
    "add_product_router",
    "list_products_router",
    "edit_product_router",
    "orders_router",
    "promos_router",
    "admin_menu_router",
    "pages_router",
    "consents_router",
    "dicts_router",   # NEW
]
