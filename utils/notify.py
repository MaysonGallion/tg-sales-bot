# tg-sales-bot/utils/notify.py
from typing import Iterable
from messages.pl import LEGAL_CONSENT_VERSION
from database.crud.admin_consents import get_consented_admin_ids
from utils.logger import logger
from config import ADMIN_ID

async def _consented_admins() -> list[int]:
    try:
        ids = await get_consented_admin_ids(LEGAL_CONSENT_VERSION)
        if not ids:
            logger.warning(
                "notify_admins: нет админов, принявших версию согласия %s. "
                "Отправлю бэкап-уведомление главному админу (ADMIN_ID=%s).",
                LEGAL_CONSENT_VERSION, ADMIN_ID
            )
            return [ADMIN_ID] if ADMIN_ID else []
        return ids
    except Exception as e:
        logger.error("notify_admins: ошибка получения списка согласий: %s", e)
        return [ADMIN_ID] if ADMIN_ID else []

async def notify_admins(bot, text: str, parse_mode: str | None = "HTML"):
    admin_ids = await _consented_admins()
    for admin_id in admin_ids:
        try:
            await bot.send_message(admin_id, text, parse_mode=parse_mode)
        except Exception as e:
            logger.warning("notify_admins: не смог отправить %s: %s", admin_id, e)

async def forward_to_admins(bot, message):
    admin_ids = await _consented_admins()
    for admin_id in admin_ids:
        try:
            await message.forward(admin_id)
        except Exception as e:
            logger.warning("forward_to_admins: не смог переслать %s: %s", admin_id, e)
