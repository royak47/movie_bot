import os
import json
import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# ✅ Optional FastAPI for Render's port binding
from fastapi import FastAPI
import uvicorn
import threading

# ⏬ Load .env variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
REDIRECT_BASE = os.getenv("REDIRECT_BASE")
BOT_USERNAME = os.getenv("BOT_USERNAME")
UPLOAD_CHANNEL = int(os.getenv("UPLOAD_CHANNEL"))
SEARCH_CHANNEL = int(os.getenv("SEARCH_CHANNEL"))
MOVIE_DB_FILE = "movie_db.json"

# ✅ Bot + Web API setup
app = FastAPI()

@app.get("/")
def home():
    return {"status": "Bot is running!"}

def run_fastapi():
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

bot = Client("movie_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# 📁 Helpers for DB
def load_db():
    if not os.path.exists(MOVIE_DB_FILE):
        return []
    try:
        with open(MOVIE_DB_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_db(data):
    with open(MOVIE_DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

def slugify(text):
    clean = re.sub(r'https?://\S+', '', text)  # remove links
    return re.sub(r'\W+', '', clean.lower().replace(" ", ""))

# 🎬 Forward movie to private channel — auto save to DB
@bot.on_message(filters.channel & (filters.video | filters.document))
async def channel_add_movie(client, message):
    if message.chat.id != UPLOAD_CHANNEL:
        return

    title = message.caption or "Untitled Movie"
    file_id = message.video.file_id if message.video else message.document.file_id
    slug = slugify(title)

    db = load_db()
    if any(m.get("slug") == slug for m in db):
        print(f"⚠️ Already exists: {title}")
        return

    db.append({
        "title": title.strip(),
        "slug": slug,
        "file_id": file_id,
        "redirect": f"{REDIRECT_BASE}{slug}"
    })
    save_db(db)
    print(f"✅ Added: {title} | slug: {slug}")

# 👥 Detect messages in public channel and send user to bot
@bot.on_message(filters.channel & filters.text)
async def search_from_channel(client, message):
    if message.chat.id != SEARCH_CHANNEL:
        return

    query = message.text.lower().strip()
    db = load_db()
    matched = next((m for m in db if query in m["title"].lower()), None)

    if matched:
        slug = matched["slug"]
        redirect_link = f"https://t.me/{BOT_USERNAME}?start={slug}"
        await message.reply_text(
            f"🎬 **{matched['title']}**\n👉 Click to Activate: [Link]({redirect_link})",
            disable_web_page_preview=True
        )

# 🟢 Handle /start=slug in private
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
    await message.reply("👋 Welcome! Just forward movies in upload channel to activate.")

# 🔃 Run both
def run_bot():
    bot.run()

if __name__ == "__main__":
    threading.Thread(target=run_fastapi).start()
    run_bot()
