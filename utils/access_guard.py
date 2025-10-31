# utils/access_guard.py
from typing import Any
from config import ADMIN_IDS

def is_admin(event: Any) -> bool:
    user = getattr(event, "from_user", None)
    if user is None:
        message = getattr(event, "message", None)
        if message is not None:
            user = getattr(message, "from_user", None)
    return bool(user and user.id in ADMIN_IDS)
