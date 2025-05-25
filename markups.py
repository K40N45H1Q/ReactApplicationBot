from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import WebAppInfo, InlineKeyboardButton
from dotenv import dotenv_values
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from api.crud import get_categories, get_products
from api.database import session

async def gender_choice():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="♂️ Male", callback_data="male"),
            InlineKeyboardButton(text="♀️ Female", callback_data="female")
        ],
    ])

async def category_choice():
    builder = InlineKeyboardBuilder()
    async with session() as async_session:
        for category in (await get_categories(async_session)):
            builder.add(
                InlineKeyboardButton(
                    text=category.name, 
                    callback_data=str(category.id)
                )
            )
    builder.adjust(2)
    return builder.as_markup()

async def product_choice(gender):
    builder = InlineKeyboardBuilder()
    async with session() as async_session:
        for product in (await get_products(async_session, gender)):
            builder.add(
                InlineKeyboardButton(
                    text=product.name, 
                    callback_data=str(product.id)
                )
            )
    builder.adjust(2)
    return builder.as_markup()


async def menu(user_id):
        WEB_APP_URL = "https://k40n45h1q.github.io/ReactApplication"
        menu = InlineKeyboardBuilder().row(
            InlineKeyboardButton(
                text="Open ✨",
                web_app=WebAppInfo(url=WEB_APP_URL)
            )
        )
        if str(user_id) in dotenv_values(".env")["ADMIN_IDS"]:
            menu.row(
                InlineKeyboardButton(
                    text="Add item 🔋",
                    callback_data="add_item"
                ),
                InlineKeyboardButton(
                    text="Delete item 🪫",
                    callback_data="delete_item"
                ),
            )
        return menu.as_markup()

async def confirmation(action: str):
    builder = InlineKeyboardBuilder().row(
        InlineKeyboardButton(text="Allow", callback_data="allow"),
        InlineKeyboardButton(text="Deny", callback_data="deny")
    )
    return builder.as_markup()