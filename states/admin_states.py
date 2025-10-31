# states/admin_states.py
from aiogram.fsm.state import State, StatesGroup


class AdminAccessState(StatesGroup):
    waiting_for_password = State()


class AddProductState(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_photo = State()
    waiting_for_price = State()
    waiting_for_city = State()
    waiting_for_category = State()
    confirmation = State()


class EditProductState(StatesGroup):
    choosing_product = State()
    edit_menu = State()
    editing_name = State()
    editing_description = State()
    editing_price = State()
    editing_city = State()
    editing_category = State()
    replacing_photo = State()
    confirm_delete = State()


class AddPromoState(StatesGroup):
    waiting_for_code = State()
    waiting_for_type = State()
    waiting_for_value = State()
    waiting_for_scope = State()
    waiting_for_city = State()
    waiting_for_category = State()
    confirmation = State()


class EditPromoState(StatesGroup):
    waiting_for_code = State()
    waiting_for_value = State()
    waiting_for_category = State()
    waiting_for_scope = State()
    waiting_for_city = State()
    waiting_for_type = State()


class DictsState(StatesGroup):
    entry = State()

    cities_list = State()
    waiting_for_city_name = State()
    waiting_for_city_rename = State()
    confirm_city_delete = State()

    # категории
    categories_list = State()
    waiting_for_category_name = State()
    waiting_for_category_rename = State()
    confirm_category_delete = State()


class EditPagesState(StatesGroup):
    choosing_page = State()
    waiting_for_regulamin = State()
    waiting_for_support = State()
