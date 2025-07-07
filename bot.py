from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os, json
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

bot = Client("movie_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

with open("movie_db.json", "r", encoding="utf-8") as f:
    movie_db = json.load(f)

@bot.on_message(filters.private & filters.text)
async def search_movie(client, message):
    query = message.text.strip().lower()
    for movie in movie_db:
        if query in movie["title"].lower():
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("📥 Download from TeraBox", url=movie["terabox_url"])]])
            await message.reply(f"🎬 {movie['title']}\n📁 File: {movie['terabox_url']}", reply_markup=kb)
            return
    await message.reply("❌ Movie not found.")

bot.run()
