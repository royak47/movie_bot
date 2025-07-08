import os
import json
import re
import shutil
import threading
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from fastapi import FastAPI
import uvicorn

# 🔒 Load .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_USERNAME = os.getenv("BOT_USERNAME")
UPLOAD_CHANNEL = int(os.getenv("UPLOAD_CHANNEL"))
SEARCH_GROUP = int(os.getenv("SEARCH_GROUP"))  # ✅ group id with users
REDIRECT_BASE = os.getenv("REDIRECT_BASE")

MOVIE_DB_FILE = "movie_db.json"
BACKUP_FILE = "backup_movie_db.json"

# ✅ Pyrogram Bot
bot = Client("movie_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# ✅ FastAPI for Render PORT binding
app = FastAPI()

@app.get("/")
def home():
    return {"status": "Bot is running!"}

def run_fastapi():
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

# 🔁 DB Helpers with backup/restore
def load_db():
    if not os.path.exists(MOVIE_DB_FILE):
        if os.path.exists(BACKUP_FILE):
            shutil.copy(BACKUP_FILE, MOVIE_DB_FILE)
            print("♻️ Restored movie_db.json from backup.")
        else:
            return []
    try:
        with open(MOVIE_DB_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_db(data):
    with open(MOVIE_DB_FILE, "w") as f:
        json.dump(data, f, indent=2)
    with open(BACKUP_FILE, "w") as b:
        json.dump(data, b, indent=2)
    print("💾 DB saved & backup created.")

def slugify(text):
    clean = re.sub(r'https?://\S+', '', text)
    return re.sub(r'\W+', '', clean.lower().replace(" ", ""))

# ✅ Auto add when forwarded to private channel
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

# ✅ Group search by users (text matching)
@bot.on_message(filters.group & filters.text)
async def group_search_handler(client, message):
    if message.chat.id != SEARCH_GROUP:
        return

    query = message.text.lower().strip()
    db = load_db()
    matches = [m for m in db if query in m["title"].lower()]

    if not matches:
        return

    for movie in matches[:3]:  # limit to 3 matches
        slug = movie["slug"]
        redirect_link = f"https://t.me/{BOT_USERNAME}?start={slug}"
        await message.reply_text(
            f"🎬 **{movie['title']}**\n👉 [Activate Link]({redirect_link})",
            disable_web_page_preview=True
        )

# ✅ /start=slug for DM
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
    await message.reply("👋 Send a movie name in group or forward file to upload channel.")

# ▶️ Start bot + FastAPI
def run_bot():
    bot.run()

if __name__ == "__main__":
    threading.Thread(target=run_fastapi).start()
    run_bot()
