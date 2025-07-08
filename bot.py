import os
import json
import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# 🟢 Optional FastAPI for Render hosting
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
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
REDIRECT_BASE = os.getenv("REDIRECT_BASE")
MOVIE_DB_FILE = "movie_db.json"

bot = Client("movie_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

def load_db():
    if not os.path.exists(MOVIE_DB_FILE):
        return []
    try:
        with open(MOVIE_DB_FILE, "r") as f:
            data = json.load(f)
            # Ensure all required keys exist
            return [d for d in data if "slug" in d and "file_id" in d and "title" in d]
    except Exception as e:
        print("⚠️ Error loading movie_db.json:", e)
        return []

def save_db(data):
    try:
        with open(MOVIE_DB_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("❌ Failed to save DB:", e)

def slugify(text):
    return re.sub(r'\W+', '', text.lower().replace(" ", ""))

@bot.on_message(filters.channel & (filters.video | filters.document))
async def channel_add_movie(client, message):
    title = message.caption or "Untitled Movie"
    file_id = message.video.file_id if message.video else message.document.file_id
    slug = slugify(title)

    db = load_db()
    if any(m.get("slug") == slug for m in db):
        print(f"⚠️ Already exists: {title}")
        return

    movie_data = {
        "title": title.strip(),
        "slug": slug,
        "file_id": file_id,
        "redirect": f"{REDIRECT_BASE}{slug}"
    }
    db.append(movie_data)
    save_db(db)
    print(f"✅ Added: {title} | slug: {slug}")

@bot.on_message(filters.private & filters.command("start"))
async def start_handler(client, message):
    if len(message.command) > 1:
        slug = message.command[1]
        db = load_db()
        movie = next((m for m in db if m["slug"] == slug), None)
        if movie:
            button = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎬 Activate Now", url=movie["redirect"])]
            ])
            await message.reply(
                f"🎬 {movie['title']}\nClick below to activate & get movie:",
                reply_markup=button
            )
            return
    await message.reply("👋 Welcome! Forward movies in the channel to auto-activate.")

def run_bot():
    print("🚀 Starting Telegram Bot...")
    bot.run()

if __name__ == "__main__":
    threading.Thread(target=run_fastapi).start()
    run_bot()
