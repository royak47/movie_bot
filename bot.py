import os
import json
import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# Load from .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
MOVIE_DB_FILE = "movie_db.json"
REDIRECT_BASE = os.getenv("REDIRECT_BASE")  # e.g., https://downloadterabox.com/go/

bot = Client("movie_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# Helper functions
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

# Auto add movie when forwarded in channel
@bot.on_message(filters.channel & (filters.video | filters.document))
async def channel_add_movie(client, message):
    title = message.caption or "Untitled Movie"
    file_id = message.video.file_id if message.video else message.document.file_id
    slug = slugify(title)

    db = load_db()
    if any(m['slug'] == slug for m in db):
        return  # already exists

    db.append({
        "title": title.strip(),
        "slug": slug,
        "file_id": file_id,
        "redirect": f"{REDIRECT_BASE}{slug}"
    })
    save_db(db)
    print(f"✅ Added: {title}")

# Handle /start=slug to send redirect button
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
            return
    await message.reply("👋 Welcome! Forward movies in the channel to auto-activate.")

bot.run()
