import os
import json
import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# 🟢 Optional FastAPI for Render port requirement
from fastapi import FastAPI
import uvicorn
import threading

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Bot is running!"}

def run_fastapi():
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

# 🔒 Load secrets
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
REDIRECT_BASE = os.getenv("REDIRECT_BASE")
MOVIE_DB_FILE = "movie_db.json"

# 🧪 Print debug info
print("🔐 Loaded .env:")
print(f"BOT_TOKEN: {BOT_TOKEN[:10]}...")
print(f"API_ID: {API_ID}")
print(f"API_HASH: {API_HASH[:10]}...")
print(f"REDIRECT_BASE: {REDIRECT_BASE}")

# 🧤 Check if .env values are missing
if not all([BOT_TOKEN, API_ID, API_HASH, REDIRECT_BASE]):
    raise ValueError("❌ One or more environment variables are missing!")

# 🔧 Typecast
API_ID = int(API_ID)

# 🚀 Init bot
bot = Client("movie_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# 📂 DB Functions
def load_db():
    if not os.path.exists(MOVIE_DB_FILE):
        return []
    with open(MOVIE_DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(MOVIE_DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

def slugify(text):
    return re.sub(r'\W+', '', text.lower().replace(" ", ""))

# 📨 Auto Movie Capture from Channel
@bot.on_message(filters.channel & (filters.video | filters.document))
async def channel_add_movie(client, message):
    title = message.caption or "Untitled Movie"
    file_id = message.video.file_id if message.video else message.document.file_id
    slug = slugify(title)

    db = load_db()
    if any(m['slug'] == slug for m in db):
        print(f"⚠️ Duplicate: {title}")
        return

    db.append({
        "title": title.strip(),
        "slug": slug,
        "file_id": file_id,
        "redirect": f"{REDIRECT_BASE}{slug}"
    })
    save_db(db)
    print(f"✅ Added: {title} | slug: {slug}")

# 🎬 Handle /start=slug
@bot.on_message(filters.private & filters.command("start"))
async def start_handler(client, message):
    if len(message.command) > 1:
        slug = message.command[1]
        db = load_db()
        movie = next((m for m in db if m['slug'] == slug), None)
        if movie:
            button = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎬 Activate Now", url=movie['redirect'])]
            ])
            await message.reply(
                f"🎬 {movie['title']}\nClick below to activate & get movie:",
                reply_markup=button
            )
            print(f"➡️ Served movie: {movie['title']}")
            return
        else:
            await message.reply("❌ Movie not found.")
            print(f"❌ Slug not found: {slug}")
    else:
        await message.reply("👋 Welcome! Forward movies in the channel to auto-activate.")

# 🎯 Bot Runner
def run_bot():
    print("🚀 Starting Telegram Bot...")
    bot.run()

# 🔁 Start both FastAPI & Pyrogram bot
if __name__ == "__main__":
    threading.Thread(target=run_fastapi).start()
    run_bot()
