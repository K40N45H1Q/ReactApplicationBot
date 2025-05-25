from aiogram.fsm.state import StatesGroup, State

class ItemForm(StatesGroup):
    category = State()
    title = State()
    photo = State()
    price_in_eur = State()
    gender = State()

class DeleteItemForm(StatesGroup):
    product_id = State()