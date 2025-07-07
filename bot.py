from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_URL = os.getenv("API_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

# Initialize the bot
bot = Client("movie_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

@bot.on_message(filters.private & filters.text)
async def movie_handler(client, message):
    query = message.text.strip()
    await message.reply(f"🔎 Searching for: {query}")
    
    try:
        # Send POST request to backend
        res = requests.post(API_URL, json={"query": query})
        print("Status Code:", res.status_code)
        print("Response:", res.text)

        data = res.json()

        # Safe check for valid file_id (only if not empty or None)
        file_id = data.get("file_id")
        if file_id and file_id.startswith("BQAC"):  # Basic validation
            try:
                await message.reply_document(
                    file_id,
                    caption=f"🎬 {data['title']} ({data.get('year', '')})\nSize: {data.get('size', '')}"
                )
                return
            except Exception as e:
                print("❌ file_id error:", e)

        # Fallback to TeraBox link
        if data.get("terabox_url"):
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("📥 Download from TeraBox", url=data["terabox_url"])]])
            await message.reply(
                f"🎬 {data['title']}\nDownload via TeraBox:",
                reply_markup=kb
            )
        else:
            await message.reply("❌ Movie not found.")

    except Exception as e:
        print("❌ Exception:", e)
        await message.reply(f"⚠️ Error fetching movie.\n\nError: {str(e)}")

bot.run()
