from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests

API_URL = "https://your-backend-url.onrender.com/search"

bot = Client("movie_bot", bot_token="7427633281:AAHRsU_1u_Pjc9Eo3dBwAVG6G1jutaSZy9I", api_id=12345, api_hash="your_api_hash")

@bot.on_message(filters.private & filters.text)
async def movie_handler(client, message):
    query = message.text.strip()
    await message.reply("🔎 Searching for: " + query)
    try:
        res = requests.post(API_URL, json={"query": query})
        data = res.json()
        if data.get("file_id"):
            await message.reply_video(data["file_id"], caption=f"🎬 {data['title']} ({data['year']})\nSize: {data['size']}")
        elif data.get("terabox_url"):
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("📥 Download from TeraBox", url=data["terabox_url"])]])
            await message.reply(f"🎬 {data['title']}\nNo Telegram file found. Download via TeraBox:", reply_markup=kb)
        else:
            await message.reply("❌ Movie not found.")
    except:
        await message.reply("⚠️ Error fetching movie.")

bot.run()