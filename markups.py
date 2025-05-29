from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import dotenv_values
from httpx import AsyncClient
from api import async_session as session

config = dotenv_values(".env")
API_URL = config["API_URL"]
WEB_APP_URL = "https://k40n45h1q.github.io/ReactApplication"
BOT_ADMIN_IDS = config.get("ADMIN_CHAT_ID", "0").split(",")

async def gender_choice() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="♂️ Male", callback_data="male"),
            InlineKeyboardButton(text="♀️ Female", callback_data="female")
        ],
    ])

async def get_categories_from_api(gender="unisex"):
    async with AsyncClient() as client:
        response = await client.get(f"{API_URL}/get_categories/", params={"gender": gender})
        response.raise_for_status()
        return response.json()

async def get_products_from_api(gender):
    async with AsyncClient() as client:
        response = await client.get(f"{API_URL}/get_products/")
        response.raise_for_status()
        return [product for product in response.json() if product["gender"] == gender]

async def category_choice(gender="unisex") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    categories = await get_categories_from_api(gender)
    for category in categories:
        builder.add(
            InlineKeyboardButton(
                text=category,
                callback_data=category
            )
        )
    builder.adjust(2)
    return builder.as_markup()

async def product_choice(gender: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    products = await get_products_from_api(gender)
    for product in products:
        builder.add(
            InlineKeyboardButton(
                text=product["name"],
                callback_data=str(product["id"])
            )
        )
    builder.adjust(2)
    return builder.as_markup()

async def menu(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder().row(
        InlineKeyboardButton(
            text="Open ✨",
            web_app=WebAppInfo(url=WEB_APP_URL)
        )
    )
    if str(user_id) in BOT_ADMIN_IDS:
        builder.row(
            InlineKeyboardButton(
                text="Add item 🔋",
                callback_data="add_item"
            ),
            InlineKeyboardButton(
                text="Delete item 🪫",
                callback_data="delete_item"
            ),
        )
    return builder.as_markup()

async def confirmation(action: str) -> InlineKeyboardMarkup:
    return InlineKeyboardBuilder().row(
        InlineKeyboardButton(text="Allow", callback_data="allow"),
        InlineKeyboardButton(text="Deny", callback_data="deny")
    ).as_markup()
