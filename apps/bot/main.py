import asyncio
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from django.conf import settings
from apps.bot.handlers import router


async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
