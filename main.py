from asyncio import run as async_run, create_task, gather
from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.bot import DefaultBotProperties
from dotenv import dotenv_values
from logging import basicConfig, INFO
from simple_api import app
from uvicorn import Server, Config

from routes import start, admin

bot = Bot(
    token=dotenv_values(".env")["BOT_TOKEN"],
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
dp.include_routers(admin.router, start.router)

async def main():
    basicConfig(level=INFO, format="[%(asctime)s] %(message)s")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    async_run(main())
