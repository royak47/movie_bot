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

BASE_URL = "https://www.terabox.com/share/list"

# 👇 Paste all shared links here
SHARE_IDS = [
    ("1liFTNgdtX64k3BjKVhmd2Q", ""),
]

def fetch_recursive(surl, pwd, parent_path="/", page=1):
    results = []
    params = {
        "app_id": "250528",
        "shorturl": surl,
        "root": "1",
        "desc": "1",
        "order": "time",
        "page": str(page),
        "num": "100",
        "dir": parent_path,
        "pwd": pwd
    }
    try:
        res = requests.get(BASE_URL, headers=HEADERS, params=params)
        data = res.json()
        for item in data.get("list", []):
            if item["isdir"] == 0:
                results.append({
                    "title": item["server_filename"],
                    "terabox_url": f"https://www.terabox.com/s/{surl}?pwd={pwd}" if pwd else f"https://www.terabox.com/s/{surl}"
                })
            else:
                sub_path = item["path"]
                results += fetch_recursive(surl, pwd, sub_path, 1)
    except Exception as e:
        print(f"❌ Error fetching {parent_path}: {str(e)}")
    return results

def main():
    all_files = []
    for surl, pwd in SHARE_IDS:
        print(f"🔍 Crawling: {surl}")
        files = fetch_recursive(surl, pwd)
        print(f"✅ Found {len(files)} files in {surl}")
        all_files.extend(files)

    with open("movie_db.json", "w", encoding="utf-8") as f:
        json.dump(all_files, f, indent=2, ensure_ascii=False)
    print("🎉 Done. movie_db.json created.")

if __name__ == "__main__":
    main()
