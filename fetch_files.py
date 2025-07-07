import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

ndus = os.getenv("NDUS")
ua = os.getenv("USER_AGENT")

headers = {
    "Cookie": f"ndus={ndus}",
    "User-Agent": ua
}

# Example public folder links (replace with real ones if needed)
TERABOX_LINKS = [
    "https://www.terabox.com/s/1abcXYZ?pwd=1234",
    "https://www.terabox.com/s/1defXYZ?pwd=5678"
]

movie_data = []

for link in TERABOX_LINKS:
    try:
        surl = link.split("/s/")[1].split("?")[0]
        resp = requests.get(
            f"https://www.terabox.com/share/list?app_id=250528&shorturl={surl}&root=1",
            headers=headers
        )
        files = resp.json().get("list", [])
        for f in files:
            title = f.get("server_filename", "Unknown")
            movie_data.append({
                "title": title,
                "terabox_url": link
            })
    except Exception as e:
        print("Error for link:", link, str(e))

with open("movie_db.json", "w", encoding="utf-8") as f:
    json.dump(movie_data, f, indent=2, ensure_ascii=False)

print("✅ movie_db.json generated successfully.")
