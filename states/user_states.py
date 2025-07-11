# tg_sales_bot/states/user_states.py
from aiogram.fsm.state import State, StatesGroup

class OrderStates(StatesGroup):
    choosing_city = State()       # Wybór miasta
    choosing_category = State()   # Wybór kategorii (Herbata / Słodycze)
    choosing_product = State()    # Wybór konkretnego produktu
    waiting_for_payment = State() # Инструкция и подтверждение BLIK
    entering_address = State()    # Ввод адреса
