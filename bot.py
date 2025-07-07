from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

bot = Client("movie_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

@bot.on_message(filters.private & filters.text)
async def movie_handler(client, message):
    query = message.text.strip()
    await message.reply("🔎 Searching for: " + query)
    
    try:
        res = requests.post(API_URL, json={"query": query})

        # ✅ Debug logs (Termux me dekhne ke liye)
        print("URL:", API_URL)
        print("Status Code:", res.status_code)
        print("Response Text:", res.text)

        data = res.json()
        print("Parsed JSON:", data)

        # ✅ Check response
        if data.get("file_id"):
            await message.reply_video(data["file_id"], caption=f"🎬 {data['title']} ({data.get('year', '')})\nSize: {data.get('size', '')}")
        elif data.get("terabox_url"):
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("📥 Download from TeraBox", url=data["terabox_url"])]])
            await message.reply(f"🎬 {data['title']}\nNo Telegram file found. Download via TeraBox:", reply_markup=kb)
        else:
            await message.reply("❌ Movie not found.")
    
    except Exception as e:
        # ✅ Show real error on Telegram
        await message.reply(f"⚠️ Error fetching movie.\n\nError: `{str(e)}`", parse_mode="markdown")

bot.run()
