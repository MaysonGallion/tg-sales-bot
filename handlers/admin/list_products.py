# tg-sales-bot/handlers/admin/list_products.py
from aiogram import Router, types, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from database.crud.products import get_all_products
from keyboards.inline.admin import back_to_admin_menu_kb

router = Router()

async def _safe_edit_text(
    msg: types.Message,
    text: str,
    reply_markup=None,
    parse_mode: str | None = "HTML",
    disable_web_page_preview: bool = True,
):
    try:
        await msg.edit_text(
            text,
            parse_mode=parse_mode,
            reply_markup=reply_markup,
            disable_web_page_preview=disable_web_page_preview,
        )
    except TelegramBadRequest as e:
        s = str(e).lower()
        if "message is not modified" in s:
            try:
                await msg.edit_reply_markup(reply_markup=reply_markup)
                return
            except Exception:
                pass
        await msg.answer(text, parse_mode=parse_mode, reply_markup=reply_markup, disable_web_page_preview=disable_web_page_preview)

@router.callback_query(F.data == "admin_list_products")
async def list_products(callback: CallbackQuery):
    products = await get_all_products()

    if not products:
        return await _safe_edit_text(
            callback.message,
            "❌ Brak produktów w bazie danych.",
            reply_markup=back_to_admin_menu_kb(),
            parse_mode="HTML",
        )

    lines = ["<b>📋 Lista produktów:</b>\n"]
    for p in products[:50]:  # показываем до 50, без спама сообщениями
        status = "✅ aktywny" if p["active"] else "❌ ukryty"
        lines.append(f"{p['id']}. {p['name']} | {p['city']} | {p['category']} | {p['price']} zł | {status}")

    await _safe_edit_text(
        callback.message,
        "\n".join(lines),
        reply_markup=back_to_admin_menu_kb(),
        parse_mode="HTML",
    )
    await callback.answer()
