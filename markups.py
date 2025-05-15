from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import WebAppInfo, InlineKeyboardButton
from dotenv import dotenv_values

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
                    text="Add item",
                    callback_data="add_item"
                ),
                InlineKeyboardButton(
                    text="Delete item",
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