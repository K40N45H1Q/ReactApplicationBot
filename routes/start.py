from aiogram import Router, Bot
from aiogram.types import Message, FSInputFile
from aiogram.filters import CommandStart

from markups import menu

router = Router()

@router.message(CommandStart())
async def start_command(message: Message):
    await message.answer_photo(
        photo=FSInputFile("logo.jpg"),
        caption=(
            "✨ <b>Welcome to our store!</b>\n\n"
            "Here you will find your favorite brands at a price 4-5 times lower than on official websites.\n\n"
        ),
        reply_markup=await menu(message.from_user.id)
    )