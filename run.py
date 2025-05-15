from asyncio import run as async_run

from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.bot import DefaultBotProperties

from dotenv import dotenv_values
from logging import basicConfig, INFO

from routes import start, admin

async def main():
    basicConfig(level=INFO, format="[%(asctime)s] %(message)s")

    bot = Bot(
        token=dotenv_values(".env")["BOT_TOKEN"],
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    await bot.delete_webhook(drop_pending_updates=True)

    dp = Dispatcher()
    dp.include_routers(admin.router, start.router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    async_run(main())