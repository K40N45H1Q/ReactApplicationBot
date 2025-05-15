from aiogram.fsm.state import StatesGroup, State

class ItemForm(StatesGroup):
    category = State()
    title = State()
    price_in_eur = State()
