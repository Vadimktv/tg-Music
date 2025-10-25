import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Env var BOT_TOKEN is missing")

bot = Bot(TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я tg-Music 🎧\n"
        "Пришли ссылку на трек/альбом из Яндекс Музыки — дам ответ.\n"
        "Пока для теста просто принимаю ссылку."
    )

@dp.message(F.text.contains("music.yandex"))
async def handle_yandex(message: Message):
    await message.answer("Ссылку получил ✅. Обработку добавим позже 😉")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
