import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

NDUS = os.getenv("NDUS")
USER_AGENT = os.getenv("USER_AGENT")

HEADERS = {
    "Cookie": f"ndus={NDUS}",
    "User-Agent": USER_AGENT,
    "Referer": "https://www.terabox.com/",
}

BASE_URL = "https://www.terabox.com"

def get_subscribed_share_links():
    url = "https://www.terabox.com/share/rec_list?order=share_time&desc=true&start=0&limit=100"
    resp = requests.get(url, headers=HEADERS)
    result = resp.json()

    share_links = []
    for item in result.get("list", []):
        surl = item.get("shorturl")
        if surl:
            link = f"{BASE_URL}/s/{surl}"
            if "pwd" in item:
                link += f"?pwd={item['pwd']}"
            share_links.append({
                "title": item.get("title", "Untitled"),
                "terabox_url": link
            })

    return share_links

def main():
    movies = get_subscribed_share_links()

    if not movies:
        print("❌ No subscribed movies found.")
        return

    with open("movie_db.json", "w", encoding="utf-8") as f:
        json.dump(movies, f, indent=2, ensure_ascii=False)

    print(f"✅ Fetched {len(movies)} movie links from subscribed channels.")

if __name__ == "__main__":
    main()
