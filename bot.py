import os, json, re, aiohttp, asyncio, threading
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from fastapi import FastAPI
import uvicorn
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_USERNAME = os.getenv("BOT_USERNAME")
REDIRECT_BASE = os.getenv("REDIRECT_BASE")

UPLOAD_CHANNEL = int(os.getenv("UPLOAD_CHANNEL"))
SEARCH_GROUP = int(os.getenv("SEARCH_GROUP"))
MOVIE_DB_FILE = "movie_db.json"

# FastAPI setup
app = FastAPI()

@app.get("/")
def home():
    return {"status": "Movie Bot Running"}

def run_api():
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

bot = Client("movie_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# DB Functions
def load_db():
    if not os.path.exists(MOVIE_DB_FILE): return []
    with open(MOVIE_DB_FILE, "r") as f:
        try: return json.load(f)
        except: return []

def save_db(data):
    with open(MOVIE_DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

def slugify(text):
    text = re.sub(r'https?://\S+', '', text)
    return re.sub(r'\W+', '', text.lower())

# Save forwarded movie
@bot.on_message(filters.channel & (filters.video | filters.document))
async def save_movie(client, message):
    if message.chat.id != UPLOAD_CHANNEL:
        return

    title = message.caption or "Untitled"
    file_id = message.video.file_id if message.video else message.document.file_id
    slug = slugify(title)

    db = load_db()
    if any(m["slug"] == slug for m in db):
        print(f"⚠️ Already exists: {title}")
        return

    db.append({
        "title": title.strip(),
        "slug": slug,
        "file_id": file_id,
        "redirect": f"https://t.me/{BOT_USERNAME}?start={slug}"
    })
    save_db(db)
    print(f"✅ Added: {title} | slug: {slug}")

# Group search handler
@bot.on_message(filters.group & filters.text)
async def handle_group_search(client, message):
    query = message.text.lower().strip()
    db = load_db()

    matches = [m for m in db if query in m['title'].lower()]
    if not matches:
        return

    buttons = [[InlineKeyboardButton(m['title'][:50], url=m['redirect'])] for m in matches[:5]]
    await message.reply_text("🎬 Matching Movies:", reply_markup=InlineKeyboardMarkup(buttons))

# /start handler
@bot.on_message(filters.private & filters.command("start"))
async def start_handler(client, message):
    if len(message.command) > 1:
        slug = message.command[1]
        db = load_db()
        movie = next((m for m in db if m["slug"] == slug), None)
        if movie:
            await message.reply(
                f"🎬 {movie['title']}\nClick below to get it:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📥 Get Movie", url=movie['redirect'])]])
            )
            return
    await message.reply("👋 Send me movie name in group to get started!")

def run_bot():
    bot.run()

if __name__ == "__main__":
    threading.Thread(target=run_api).start()
    run_bot()
