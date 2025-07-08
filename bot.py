import os
import json
import re
import unicodedata
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn
import threading

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
REDIRECT_BASE = os.getenv("REDIRECT_BASE")
BOT_USERNAME = os.getenv("BOT_USERNAME")
UPLOAD_CHANNEL = int(os.getenv("UPLOAD_CHANNEL"))
SEARCH_GROUP = int(os.getenv("SEARCH_GROUP"))  # ✅ Not channel — GROUP now
MOVIE_DB_FILE = "movie_db.json"

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Movie Bot is Live!"}

def run_fastapi():
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

bot = Client("movie_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def load_db():
    if not os.path.exists(MOVIE_DB_FILE):
        return []
    try:
        with open(MOVIE_DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_db(data):
    with open(MOVIE_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def slugify(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode()
    clean = re.sub(r'https?://\S+', '', text)
    return re.sub(r'\W+', '', clean.lower().replace(" ", ""))

def clean_text(text):
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower()

# ✅ Save any movie from UPLOAD_CHANNEL to DB
@bot.on_message(filters.channel & (filters.video | filters.document))
async def save_movie(client, message):
    if message.chat.id != UPLOAD_CHANNEL:
        return

    title = message.caption or "Untitled"
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

# ✅ Group me keyword detect kar ke match de
@bot.on_message(filters.group & filters.text)
async def handle_group_search(client, message):
    if message.chat.id != SEARCH_GROUP:
        return

    query = clean_text(message.text)
    db = load_db()
    results = [m for m in db if all(word in clean_text(m["title"]) for word in query.split())]

    if not results:
        await message.reply_text("❌ No matching movie found.")
        return

    reply = "🎬 **Movies Found:**\n\n"
    for m in results[:5]:
        slug = m["slug"]
        title = clean_text(m["title"]).title()
        link = f"https://t.me/{BOT_USERNAME}?start={slug}"
        reply += f"👉 [{title}]({link})\n"

    await message.reply_text(reply, disable_web_page_preview=True)

# ✅ Private DM /start handler
@bot.on_message(filters.private & filters.command("start"))
async def start_handler(client, message):
    if len(message.command) == 1:
        await message.reply("👋 Welcome! Send a movie name or click a link from the group.")
        return

    slug = message.command[1]
    db = load_db()
    movie = next((m for m in db if m["slug"] == slug), None)

    if movie:
        title = clean_text(movie["title"]).title()
        button = InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 Activate Now", url=movie["redirect"])]
        ])
        await message.reply(
            f"🎬 {title}\nClick below to activate & get movie:",
            reply_markup=button
        )
    else:
        await message.reply("❌ Movie not found.")

# 🔁 Run both
def run_bot():
    bot.run()

if __name__ == "__main__":
    threading.Thread(target=run_fastapi).start()
    run_bot()
