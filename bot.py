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

# 🔐 Load secrets
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
REDIRECT_BASE = os.getenv("REDIRECT_BASE")
MOVIE_DB_FILE = "movie_db.json"

bot = Client("movie_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# 🧠 Load & Save DB
def load_db():
    if not os.path.exists(MOVIE_DB_FILE):
        return []
    with open(MOVIE_DB_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_db(data):
    with open(MOVIE_DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

# 🧹 Caption Cleaner
def clean_caption(title):
    title = re.sub(r'@\w+', '', title)                   # remove @channel
    title = re.sub(r'https?://\S+', '', title)           # remove links
    title = re.sub(r'#\w+', '', title)                   # remove hashtags
    title = re.sub(r'\[.*?\]', '', title)                # remove [text]
    title = re.sub(r'[^\w\s\(\)&-]', '', title)          # remove emojis/symbols
    title = re.sub(r'\s+', ' ', title).strip()           # remove extra spaces
    return title

# 🔗 Slug Generator
def slugify(text):
    return re.sub(r'\W+', '', text.lower().replace(" ", ""))

# 🎬 Auto Add Movie from Channel
@bot.on_message(filters.channel & (filters.video | filters.document))
async def channel_add_movie(client, message):
    raw_title = message.caption or "Untitled Movie"
    title = clean_caption(raw_title)
    slug = slugify(title)
    file_id = message.video.file_id if message.video else message.document.file_id

    db = load_db()
    if any(m.get('slug') == slug for m in db):
        print(f"⚠️ Already exists: {title}")
        return

    db.append({
        "title": title,
        "slug": slug,
        "file_id": file_id,
        "redirect": f"{REDIRECT_BASE}{slug}"
    })
    save_db(db)
    print(f"✅ Added: {title} | slug: {slug}")

# 🔘 /start=slug handler
@bot.on_message(filters.private & filters.command("start"))
async def start_handler(client, message):
    if len(message.command) > 1:
        slug = message.command[1]
        db = load_db()
        movie = next((m for m in db if m.get('slug') == slug), None)
        if movie:
            button = InlineKeyboardMarkup([
                [InlineKeyboardButton("🎬 Activate Now", url=movie['redirect'])]
            ])
            await message.reply(
                f"🎬 {movie['title']}\nClick below to activate & get movie:",
                reply_markup=button
            )
            return
    await message.reply("👋 Welcome! Forward movies in the channel to auto-activate.")

# 🚀 Start Both FastAPI & Bot
def run_bot():
    bot.run()

if __name__ == "__main__":
    threading.Thread(target=run_fastapi).start()
    run_bot()
