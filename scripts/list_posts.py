import json
import sys
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

with open(r"C:\Users\Harun\.gemini\antigravity\scratch\bd-news-portal\config\blogger_token.json", "r", encoding="utf-8") as f:
    creds = Credentials.from_authorized_user_info(json.load(f))

service = build("blogger", "v3", credentials=creds)
posts = service.posts().list(blogId="2941397978971258684").execute()

items = posts.get("items", [])
print(f"Total posts on blog: {len(items)}")
for p in items:
    print(f"ID: {p.get('id')} | Title: {p.get('title')}")
