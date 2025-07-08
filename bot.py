import os
import json
import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
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

# 🔐 Load Environment
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
REDIRECT_BASE = os.getenv("REDIRECT_BASE", "https://downloadterabox.com/go/")
FORCE_JOIN = os.getenv("FORCE_JOIN", "zzmovie100")
MOVIE_DB_FILE = "movie_db.json"
UPLOAD_CHANNEL = int(os.getenv("UPLOAD_CHANNEL_ID"))  # Channel A (Movie Upload)
SEARCH_CHANNEL = int(os.getenv("SEARCH_CHANNEL_ID"))  # Channel B (Public users)

bot = Client("movie_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

def load_db():
    if not os.path.exists(MOVIE_DB_FILE):
        return []
    with open(MOVIE_DB_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return []

def save_db(data):
    with open(MOVIE_DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

def slugify(text):
    return re.sub(r'\W+', '', text.lower().replace(" ", ""))

def clean_title(text):
    junk = ["Backup Grup Must join", "🔥", "👉", "👈"]
    for j in junk:
        text = text.replace(j, "")
    return text.strip()

# ✅ Auto Save from Upload Channel
@bot.on_message(filters.channel & (filters.video | filters.document))
async def save_movie(client, message):
    if message.chat.id != UPLOAD_CHANNEL:
        return

    title = clean_title(message.caption or "Untitled")
    file_id = message.video.file_id if message.video else message.document.file_id
    slug = slugify(title)

    db = load_db()
    if any(m.get("slug") == slug for m in db):
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

# ✅ Listen in Search Channel
@bot.on_message(filters.channel & filters.text)
async def handle_public_channel(client, message):
    if message.chat.id != SEARCH_CHANNEL:
        return

    query = message.text.lower()
    db = load_db()
    results = [m for m in db if query in m['title'].lower()]
    if not results:
        return

    slug = results[0]['slug']
    reply_markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("🎬 Get Download Link", url=f"https://t.me/{bot.me.username}?start={slug}")
    ]])
    await message.reply("🔗 Movie link found! Tap below to open bot in DM.", reply_markup=reply_markup)

# ✅ DM Handler with /start=<slug>
@bot.on_message(filters.private & filters.command("start"))
async def dm_start(client, message):
    if len(message.command) == 2:
        slug = message.command[1]
        db = load_db()
        movie = next((m for m in db if m['slug'] == slug), None)
        if not movie:
            return await message.reply("❌ Movie not found.")

        member = await bot.get_chat_member(f"@{FORCE_JOIN}", message.from_user.id)
        if member.status not in ("member", "administrator", "creator"):
            join_btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{FORCE_JOIN}")
            ]])
            return await message.reply("⚠️ Please join our channel to unlock the movie.", reply_markup=join_btn)

        btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("🎬 Download Now", url=movie['redirect'])
        ]])
        return await message.reply(f"🎬 {movie['title']}\nClick below to download:", reply_markup=btn)

    await message.reply("👋 Welcome! Send /start=<slug> or use the search channel.")

# Start All
def run_bot():
    print("🚀 Bot is running...")
    bot.run()

if __name__ == "__main__":
    threading.Thread(target=run_fastapi).start()
    run_bot()
