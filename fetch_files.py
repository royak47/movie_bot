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

# ✅ Added your link:
SHARE_IDS = [
    ("1liFTNgdtX64k3BjKVhmd2Q", ""),  # Your real TeraBox link, no password
]

BASE_FILE_LIST_URL = "https://www.terabox.com/share/list"

def get_files_from_folder(surl, pwd=""):
    params = {
        "app_id": "250528",
        "shorturl": surl,
        "root": "1",
        "desc": "1",
        "order": "time",
        "page": "1",
        "num": "100",
        "pwd": pwd
    }
    res = requests.get(BASE_FILE_LIST_URL, headers=HEADERS, params=params)
    data = res.json()
    result = []
    for item in data.get("list", []):
        if item["isdir"] == 0:  # file only
            filename = item["server_filename"]
            dlink = f"https://www.terabox.com/s/{surl}?pwd={pwd}" if pwd else f"https://www.terabox.com/s/{surl}"
            result.append({
                "title": filename,
                "terabox_url": dlink
            })
    return result

def main():
    all_movies = []
    for surl, pwd in SHARE_IDS:
        try:
            files = get_files_from_folder(surl, pwd)
            print(f"✅ Fetched from {surl}: {len(files)} files")
            all_movies.extend(files)
        except Exception as e:
            print(f"❌ Error from {surl}: {str(e)}")

    with open("movie_db.json", "w", encoding="utf-8") as f:
        json.dump(all_movies, f, indent=2, ensure_ascii=False)
    print("🎉 movie_db.json created with real TeraBox movies.")

if __name__ == "__main__":
    main()
