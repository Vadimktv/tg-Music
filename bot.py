import os
import re
import asyncio
from contextlib import suppress

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

import httpx
from bs4 import BeautifulSoup

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Put it into .env or environment variables.")

bot = Bot(BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

YANDEX_URL_RE = re.compile(r'(https?://(?:music\.)?yandex\.(?:ru|by|kz|ua|uz|com)/[^\s]+)', re.IGNORECASE)

async def fetch_og(url: str) -> dict:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; Bot/1.0)"}
    async with httpx.AsyncClient(timeout=10, headers=headers, follow_redirects=True) as client:
        r = await client.get(url)
        r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    def get(prop: str):
        tag = soup.find("meta", property=prop)
        return tag.get("content") if tag else None
    title = get("og:title") or "Трек в Яндекс Музыке"
    image = get("og:image")
    final_url = get("og:url") or url
    return {"title": title, "image": image, "url": final_url}

@dp.message(F.text.startswith("/start"))
async def start(message: Message):
    await message.answer(
        "Привет! Пришли ссылку на трек/альбом Яндекс Музыки — пришлю карточку с названием, обложкой и кнопкой ‘Открыть’.\n"
        "Можешь также прислать свой MP3 (легальный) — верну файл, чтобы поставить в профиль Telegram вручную."
    )

@dp.message(F.text.regexp(YANDEX_URL_RE))
async def handle_yandex_link(message: Message):
    url_match = YANDEX_URL_RE.search(message.text or "")
    if not url_match:
        await message.answer("Пришли прямую ссылку на Яндекс Музыку.")
        return
    url = url_match.group(1)
    try:
        og = await fetch_og(url)
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Открыть в Яндекс Музыке", url=og["url"])]]
        )
        if og["image"]:
            await message.answer_photo(
                photo=og["image"],
                caption=f"🎵 <b>{og['title']}</b>\nИсточник: Яндекс Музыка",
                reply_markup=kb
            )
        else:
            await message.answer(f"🎵 <b>{og['title']}</b>\n{og['url']}", reply_markup=kb)
    except Exception:
        await message.answer("Не удалось получить метаданные. Пришли прямую ссылку на трек/альбом ещё раз.")

@dp.message(F.audio | F.document)
async def handle_audio(message: Message):
    file_id = None
    if message.audio:
        file_id = message.audio.file_id
    elif message.document and (message.document.mime_type or "").startswith("audio/"):
        file_id = message.document.file_id

    if not file_id:
        await message.answer("Пришли MP3 как аудио или документ с типом audio/*")
        return

    await message.answer_audio(
        audio=file_id,
        caption="Готово! Сохрани этот файл и поставь его в профиле Telegram вручную: Профиль → Изменить → Музыка."
    )

@dp.message()
async def fallback(message: Message):
    await message.answer("Пришли ссылку на Яндекс Музыку или MP3-файл. Команда: /start")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    with suppress(KeyboardInterrupt, SystemExit):
        asyncio.run(main())
