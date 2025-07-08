import os
import json
import re
import aiohttp
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# FastAPI for keep-alive
from fastapi import FastAPI
import uvicorn
import threading

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
REDIRECT_BASE = os.getenv("REDIRECT_BASE", "https://t.me/")
BOT_USERNAME = os.getenv("BOT_USERNAME").replace("@", "")
UPLOAD_CHANNEL = int(os.getenv("UPLOAD_CHANNEL"))
SOURCE_CHANNEL = int(os.getenv("SOURCE_CHANNEL"))
SEARCH_GROUP = int(os.getenv("SEARCH_GROUP"))
MOVIE_DB_FILE = "movie_db.json"

bot = Client("movie_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
app = FastAPI()

# -------------------- DB Helpers -------------------- #
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
    clean = re.sub(r'https?://\S+', '', text)
    return re.sub(r'\W+', '', clean.lower().replace(" ", ""))

def clean_caption(caption):
    # Remove unwanted bot/channel promo lines
    lines = caption.splitlines()
    allowed_lines = [line for line in lines if "@" not in line and "latest uploads" not in line.lower()]
    return "\n".join(allowed_lines).strip()

# -------------------- Self Ping -------------------- #
async def ping_self():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                await session.get(f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME') or 'movie-bot-afgg.onrender.com'}")
        except Exception:
            pass
        await asyncio.sleep(280)

# -------------------- Web API -------------------- #
@app.get("/")
def home():
    return {"status": "Bot is running!"}

def run_web():
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

# -------------------- Message Handlers -------------------- #
@bot.on_message(filters.chat(SOURCE_CHANNEL) & (filters.video | filters.document))
async def forward_and_save(client, message):
    caption = clean_caption(message.caption or "")
    if not caption:
        return

    slug = slugify(caption)
    db = load_db()

    if any(m["slug"] == slug for m in db):
        print(f"⚠️ Already exists: {caption}")
        return

    forwarded = await message.copy(chat_id=UPLOAD_CHANNEL, caption=caption)

    db.append({
        "title": caption,
        "slug": slug,
        "file_id": forwarded.id,
        "redirect": f"https://t.me/{BOT_USERNAME}?start={slug}"
    })
    save_db(db)
    print(f"✅ Saved: {caption}")

@bot.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    if len(message.command) > 1:
        slug = message.command[1]
        db = load_db()
        movie = next((m for m in db if m["slug"] == slug), None)
        if movie:
            button = InlineKeyboardMarkup([[InlineKeyboardButton("🎬 Watch / Download", url=movie["redirect"])]])
            await message.reply(f"🎬 **{movie['title']}**\nClick below to get the file:", reply_markup=button)
            return
    await message.reply("👋 Send movie name in group to search.")

@bot.on_message(filters.chat(SEARCH_GROUP) & filters.text)
async def handle_group_search(client, message):
    query = message.text.lower()
    db = load_db()
    results = [m for m in db if any(word in m["title"].lower() for word in query.split())]

    if results:
        for movie in results[:3]:  # Show top 3 matches
            await message.reply_text(
                f"🎬 **{movie['title']}**\n👉 [Click to Get File](https://t.me/{BOT_USERNAME}?start={movie['slug']})",
                disable_web_page_preview=True
            )

# -------------------- Start Everything -------------------- #
def start_all():
    threading.Thread(target=run_web).start()
    loop = asyncio.get_event_loop()
    loop.create_task(ping_self())
    bot.run()

if __name__ == "__main__":
    start_all()
