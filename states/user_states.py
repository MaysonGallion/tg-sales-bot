# tg_sales_bot/states/user_states.py
from aiogram.fsm.state import State, StatesGroup

class OrderStates(StatesGroup):
    choosing_city = State()
    choosing_category = State()
    choosing_product = State()
    waiting_for_payment = State()
    entering_address = State()

class PaymentStates(StatesGroup):
    waiting_for_cash_address = State()
    waiting_for_confirmation = State()

class PromoStates(StatesGroup):
    waiting_for_code = State()