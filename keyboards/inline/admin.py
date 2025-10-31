# tg-sales-bot/keyboards/inline/admin.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Главное меню админа
def admin_main_kb() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="➕ Dodac towar", callback_data="admin_add_product")],
        [InlineKeyboardButton(text="✏️ Edycja towarów", callback_data="admin_edit_open")],
        [InlineKeyboardButton(text="📋 Lista Towarów", callback_data="admin_list_products")],
        [InlineKeyboardButton(text="🧾 Zamówienia", callback_data="admin_orders_open")],
        [InlineKeyboardButton(text="🎟️ Promokody", callback_data="admin_promos_open")],
        [InlineKeyboardButton(text="🏙📂 Miasta i Kategorie", callback_data="admin_dicts_open")],
        [InlineKeyboardButton(text="📜 Zgody", callback_data="admin_consents_open")],
        [InlineKeyboardButton(text="🏠 Menu admina", callback_data="admin_menu_admin")],
        [InlineKeyboardButton(text="👤 Menu użytkownika", callback_data="admin_menu_user")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_nav_kb(include_back: bool = True) -> InlineKeyboardMarkup:
    rows = []
    if include_back:
        rows.append([InlineKeyboardButton(text="🔙 Wstecz", callback_data="admin_back")])
    rows.append([InlineKeyboardButton(text="❌ Anuluj", callback_data="admin_cancel")])
    rows.append([InlineKeyboardButton(text="🏠 Admin", callback_data="admin_menu_admin")])
    rows.append([InlineKeyboardButton(text="👤 User", callback_data="admin_menu_user")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def choose_city_kb() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📍 Gdańsk", callback_data="admin_city_gdansk")],
        [InlineKeyboardButton(text="📍 Gdynia", callback_data="admin_city_gdynia")],
        [InlineKeyboardButton(text="📍 Sopot", callback_data="admin_city_sopot")],
        [InlineKeyboardButton(text="🌍 Wszystkie miasta", callback_data="admin_city_all")],
    ]
    nav = admin_nav_kb(include_back=True).inline_keyboard
    return InlineKeyboardMarkup(inline_keyboard=buttons + nav)

def choose_category_kb() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="🍵 Herbaty", callback_data="admin_cat_herbata")],
        [InlineKeyboardButton(text="🍬 Słodycze", callback_data="admin_cat_slodycze")],
    ]
    nav = admin_nav_kb(include_back=True).inline_keyboard
    return InlineKeyboardMarkup(inline_keyboard=buttons + nav)

def cancel_kb() -> InlineKeyboardMarkup:
    return admin_nav_kb(include_back=True)

def back_to_admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Wróć", callback_data="admin_menu_admin")]
    ])

def edit_list_kb(products, page: int, has_prev: bool, has_next: bool) -> InlineKeyboardMarkup:
    rows = []
    for p in products:
        rows.append([InlineKeyboardButton(
            text=f"✅ Wybierz #{p['id']} — {p['name'][:24]}",
            callback_data=f"admin_edit_select_{p['id']}"
        )])
    pager = []
    if has_prev:
        pager.append(InlineKeyboardButton(text="⬅️ Poprzednia", callback_data=f"admin_edit_page_{page-1}"))
    pager.append(InlineKeyboardButton(text=f"Strona {page}", callback_data="admin_nop"))
    if has_next:
        pager.append(InlineKeyboardButton(text="➡️ Następna", callback_data=f"admin_edit_page_{page+1}"))
    if pager:
        rows.append(pager)
    rows += admin_nav_kb(include_back=True).inline_keyboard
    return InlineKeyboardMarkup(inline_keyboard=rows)

def edit_product_menu_kb(product_id: int, is_active: bool) -> InlineKeyboardMarkup:
    toggle_text = "👁 Ukryj" if is_active else "✅ Pokaż"
    rows = [
        [InlineKeyboardButton(text="📝 Nazwa", callback_data="admin_edit_name")],
        [InlineKeyboardButton(text="🧾 Opis", callback_data="admin_edit_desc")],
        [InlineKeyboardButton(text="💰 Cena", callback_data="admin_edit_price")],
        [InlineKeyboardButton(text="🏙 Miasto", callback_data="admin_edit_city")],
        [InlineKeyboardButton(text="📂 Kategoria", callback_data="admin_edit_category")],
        [InlineKeyboardButton(text="🖼 Zmień zdjęcie", callback_data="admin_edit_photo")],
        [InlineKeyboardButton(text=toggle_text, callback_data="admin_edit_toggle")],
        [InlineKeyboardButton(text="🗑 Usuń", callback_data="admin_edit_delete")],
    ]
    rows += admin_nav_kb(include_back=True).inline_keyboard
    return InlineKeyboardMarkup(inline_keyboard=rows)

def confirm_delete_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🗑 Potwierdź usunięcie", callback_data="admin_edit_delete_confirm")],
    ]
    rows += admin_nav_kb(include_back=True).inline_keyboard
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ---------- Заказы ----------
def orders_filters_kb(current: str) -> InlineKeyboardMarkup:
    row1 = [
        InlineKeyboardButton(text=("🆕 Nowe ✅" if current == "new" else "🆕 Nowe"),
                             callback_data="admin_orders_filter_new"),
        InlineKeyboardButton(text=("🔧 W trakcie ✅" if current == "in_progress" else "🔧 W trakcie"),
                             callback_data="admin_orders_filter_in_progress"),
    ]
    row2 = [
        InlineKeyboardButton(text=("✅ Zrealizowane ✅" if current == "done" else "✅ Zrealizowane"),
                             callback_data="admin_orders_filter_done"),
        InlineKeyboardButton(text=("❌ Anulowane ✅" if current == "cancelled" else "❌ Anulowane"),
                             callback_data="admin_orders_filter_cancelled"),
    ]
    row3 = [
        InlineKeyboardButton(text=("📋 Wszystkie ✅" if current == "all" else "📋 Wszystkie"),
                             callback_data="admin_orders_filter_all"),
    ]
    return InlineKeyboardMarkup(inline_keyboard=[row1, row2, row3])

def orders_list_kb(orders, page: int, has_prev: bool, has_next: bool, current_status: str) -> InlineKeyboardMarkup:
    rows = []
    for o in orders:
        rows.append([InlineKeyboardButton(
            text=f"#{o['id']} • {o['price']} zł • {o['city']} • {o['status']}",
            callback_data=f"admin_orders_view_{o['id']}"
        )])
    pager = []
    if has_prev:
        pager.append(InlineKeyboardButton(text="⬅️", callback_data=f"admin_orders_page_{page-1}"))
    pager.append(InlineKeyboardButton(text=f"Strona {page}", callback_data="admin_nop"))
    if has_next:
        pager.append(InlineKeyboardButton(text="➡️", callback_data=f"admin_orders_page_{page+1}"))
    if pager:
        rows.append(pager)
    rows.append([InlineKeyboardButton(text="🔁 Zmień filtr", callback_data="admin_orders_filters")])
    rows.append([InlineKeyboardButton(text="🏠 Admin", callback_data="admin_menu_admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def orders_empty_list_kb() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🔁 Zmień filtr", callback_data="admin_orders_filters")],
        [InlineKeyboardButton(text="🏠 Admin", callback_data="admin_menu_admin")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

def order_card_kb(current_status: str) -> InlineKeyboardMarkup:
    rows = []
    if current_status != "in_progress":
        rows.append([InlineKeyboardButton(text="🔧 W trakcie", callback_data="admin_orders_set_in_progress")])
    if current_status != "done":
        rows.append([InlineKeyboardButton(text="✅ Zrealizowane", callback_data="admin_orders_set_done")])
    if current_status != "cancelled":
        rows.append([InlineKeyboardButton(text="❌ Anulować", callback_data="admin_orders_set_cancelled")])
    rows.append([InlineKeyboardButton(text="🔙 Wróć do listy", callback_data="admin_orders_back_to_list")])
    rows.append([InlineKeyboardButton(text="🏠 Admin", callback_data="admin_menu_admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def admin_legal_accept_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Akceptuję", callback_data="admin_legal_accept")],
            [InlineKeyboardButton(text="❌ Odrzucam", callback_data="admin_legal_decline")],
        ]
    )

# --- Promocodes ---
def promos_list_kb(rows, page: int, has_prev: bool, has_next: bool) -> InlineKeyboardMarkup:
    kb = []
    for r in rows:
        title = f"{r['code']} • {r['type']} {r['value']} • {r['scope']}"
        if r['scope'] == 'city' and r.get('city'):
            title += f" [{r['city']}]"
        if r['scope'] == 'category' and r.get('category'):
            title += f" [{r['category']}]"
        status = "ON" if r['is_active'] else "OFF"
        kb.append([InlineKeyboardButton(text=f"{title} • {status}", callback_data=f"admin_promos_view_{r['id']}")])
    nav = []
    if has_prev:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"admin_promos_page_{page-1}"))
    nav.append(InlineKeyboardButton(text=f"Strona {page}", callback_data="admin_nop"))
    if has_next:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"admin_promos_page_{page+1}"))
    if nav:
        kb.append(nav)
    kb.append([InlineKeyboardButton(text="➕ Nowy kod", callback_data="admin_promos_create")])
    kb.append([InlineKeyboardButton(text="🔙 Wróć", callback_data="admin_menu_admin")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def promo_create_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Procent (%)", callback_data="admin_promo_type_percent")],
        [InlineKeyboardButton(text="Kwota (zł)", callback_data="admin_promo_type_fixed")],
        [InlineKeyboardButton(text="❌ Anuluj", callback_data="admin_cancel")]
    ])

def promo_create_scope_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Globalny", callback_data="admin_promo_scope_global")],
        [InlineKeyboardButton(text="Miasto", callback_data="admin_promo_scope_city")],
        [InlineKeyboardButton(text="Kategoria", callback_data="admin_promo_scope_category")],
        [InlineKeyboardButton(text="❌ Anuluj", callback_data="admin_cancel")]
    ])

def promo_choose_city_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📍 Gdańsk", callback_data="admin_promo_city_gdansk")],
        [InlineKeyboardButton(text="📍 Gdynia", callback_data="admin_promo_city_gdynia")],
        [InlineKeyboardButton(text="📍 Sopot", callback_data="admin_promo_city_sopot")],
        [InlineKeyboardButton(text="❌ Anuluj", callback_data="admin_cancel")]
    ])

def promo_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Zapisz kod", callback_data="admin_promo_save")],
        [InlineKeyboardButton(text="❌ Anuluj", callback_data="admin_cancel")]
    ])

def promo_card_kb(promo) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=("🔴 Wyłącz" if promo['is_active'] else "🟢 Włącz"),
                              callback_data=f"admin_promo_toggle_{promo['id']}")],
        [InlineKeyboardButton(text="✏️ Zmień kod", callback_data=f"admin_promo_edit_code_{promo['id']}")],
        [InlineKeyboardButton(text="🧮 Zmień typ", callback_data=f"admin_promo_edit_type_{promo['id']}")],
        [InlineKeyboardButton(text="💰 Zmień wartość", callback_data=f"admin_promo_edit_value_{promo['id']}")],
        [InlineKeyboardButton(text="🗺 Zakres (global/miasto/kategoria)", callback_data=f"admin_promo_edit_scope_{promo['id']}")],
    ]
    if promo['scope'] == 'city':
        rows.append([InlineKeyboardButton(text=f"🏙 Miasto: {promo.get('city') or '-'}",
                                          callback_data=f"admin_promo_edit_city_{promo['id']}")])
    if promo['scope'] == 'category':
        rows.append([InlineKeyboardButton(text=f"📂 Kategoria: {promo.get('category') or '-'}",
                                          callback_data=f"admin_promo_edit_category_{promo['id']}")])
    rows.append([InlineKeyboardButton(text="🗑 Usuń kod", callback_data=f"admin_promo_delete_{promo['id']}")])
    rows.append([InlineKeyboardButton(text="🔙 Wróć do listy", callback_data="admin_promos_open")])
    rows.append([InlineKeyboardButton(text="🏠 Admin", callback_data="admin_menu_admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def promo_edit_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Procent (%)", callback_data="admin_promo_type_percent")],
        [InlineKeyboardButton(text="Kwota (zł)", callback_data="admin_promo_type_fixed")],
        [InlineKeyboardButton(text="❌ Anuluj", callback_data="admin_cancel")]
    ])

def promo_edit_scope_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Globalny", callback_data="admin_promo_scope_global")],
        [InlineKeyboardButton(text="Miasto", callback_data="admin_promo_scope_city")],
        [InlineKeyboardButton(text="Kategoria", callback_data="admin_promo_scope_category")],
        [InlineKeyboardButton(text="❌ Anuluj", callback_data="admin_cancel")]
    ])

def promo_choose_category_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍵 Herbaty",   callback_data="admin_promo_cat_herbata")],
        [InlineKeyboardButton(text="🍬 Słodycze",  callback_data="admin_promo_cat_slodycze")],
        [InlineKeyboardButton(text="❌ Anuluj",    callback_data="admin_cancel")],
    ])

# --- Consents ---
def consents_list_kb(rows, page: int, has_prev: bool, has_next: bool) -> InlineKeyboardMarkup:
    kb = []
    for r in rows:
        uname = r.get("accepted_username") or "-"
        full = r.get("accepted_full_name") or "-"
        title = f"#{r['id']} • {r['version']} • @{uname} • {full}"
        kb.append([InlineKeyboardButton(text=title, callback_data=f"admin_consents_view_{r['id']}")])
    nav = []
    if has_prev:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"admin_consents_page_{page-1}"))
    nav.append(InlineKeyboardButton(text=f"Strona {page}", callback_data="admin_nop"))
    if has_next:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"admin_consents_page_{page+1}"))
    if nav:
        kb.append(nav)
    kb.append([InlineKeyboardButton(text="🔙 Wróć", callback_data="admin_menu_admin")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def consent_card_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Wróć", callback_data="admin_consents_open")],
        [InlineKeyboardButton(text="🏠 Admin", callback_data="admin_menu_admin")],
    ])

# --- Pages editor ---
def pages_edit_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Edytuj treść", callback_data="admin_pages_edit")],
        [InlineKeyboardButton(text="🔙 Wróć", callback_data="admin_menu_admin")],
    ])

def pages_back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Wróć", callback_data="admin_menu_admin")],
    ])

def dicts_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏙 Miasta", callback_data="admin_cities_open")],
        [InlineKeyboardButton(text="📂 Kategorie", callback_data="admin_categories_open")],
        [InlineKeyboardButton(text="🔙 Wróć", callback_data="admin_menu_admin")],
    ])

def cities_list_kb(rows, page: int, has_prev: bool, has_next: bool) -> InlineKeyboardMarkup:
    kb = []
    for r in rows:
        status = "🟢" if r["is_active"] else "🔴"
        kb.append([InlineKeyboardButton(text=f"{status} {r['name']}", callback_data=f"admin_city_view_{r['id']}")])
    nav = []
    if has_prev:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"admin_cities_page_{page-1}"))
    nav.append(InlineKeyboardButton(text=f"Strona {page}", callback_data="admin_nop"))
    if has_next:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"admin_cities_page_{page+1}"))
    if nav:
        kb.append(nav)
    kb.append([InlineKeyboardButton(text="➕ Dodaj miasto", callback_data="admin_city_add")])
    kb.append([InlineKeyboardButton(text="🔙 Wróć", callback_data="admin_dicts_open")])
    kb.append([InlineKeyboardButton(text="🏠 Admin", callback_data="admin_menu_admin")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def city_card_kb(row) -> InlineKeyboardMarkup:
    # ДОБАВЛЕНО: «📂 Kategorie miasta»
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=("🟢 Włącz" if not row["is_active"] else "🔴 Wyłącz"), callback_data=f"admin_city_toggle_{row['id']}")],
        [InlineKeyboardButton(text="📂 Kategorie miasta", callback_data=f"admin_city_cats_open_{row['id']}")],
        [InlineKeyboardButton(text="✏️ Zmień nazwę", callback_data=f"admin_city_rename_{row['id']}")],
        [InlineKeyboardButton(text="🗑 Usuń", callback_data=f"admin_city_delete_{row['id']}")],
        [InlineKeyboardButton(text="🔙 Wróć", callback_data="admin_cities_open")],
        [InlineKeyboardButton(text="🏠 Admin", callback_data="admin_menu_admin")],
    ])

def categories_list_kb(rows, page: int, has_prev: bool, has_next: bool) -> InlineKeyboardMarkup:
    kb = []
    for r in rows:
        status = "🟢" if r["is_active"] else "🔴"
        kb.append([InlineKeyboardButton(
            text=f"{status} {r['name']} ({r['code']})",
            callback_data=f"admin_category_view_{r['id']}"
        )])
    nav = []
    if has_prev:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"admin_categories_page_{page-1}"))
    nav.append(InlineKeyboardButton(text=f"Strona {page}", callback_data="admin_nop"))
    if has_next:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"admin_categories_page_{page+1}"))
    if nav:
        kb.append(nav)
    kb.append([InlineKeyboardButton(text="➕ Dodaj kategorię", callback_data="admin_category_add")])
    kb.append([InlineKeyboardButton(text="🔙 Wróć", callback_data="admin_dicts_open")])
    kb.append([InlineKeyboardButton(text="🏠 Admin", callback_data="admin_menu_admin")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def category_card_kb(row) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=("🟢 Włącz" if not row["is_active"] else "🔴 Wyłącz"), callback_data=f"admin_category_toggle_{row['id']}")],
        [InlineKeyboardButton(text="✏️ Zmień nazwę", callback_data=f"admin_category_rename_{row['id']}")],
        [InlineKeyboardButton(text="🧮 Zmień kod", callback_data=f"admin_category_recode_{row['id']}")],
        [InlineKeyboardButton(text="🗑 Usuń", callback_data=f"admin_category_delete_{row['id']}")],
        [InlineKeyboardButton(text="🔙 Wróć", callback_data="admin_categories_open")],
        [InlineKeyboardButton(text="🏠 Admin", callback_data="admin_menu_admin")],
    ])
