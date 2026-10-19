import json
import sys
from bs4 import BeautifulSoup
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
posts = service.posts().list(blogId="2941397978971258684", maxResults=50).execute()

items = posts.get("items", [])
print(f"Total posts found: {len(items)}\n")

for p in items:
    content = p.get("content", "")
    soup = BeautifulSoup(content, "html.parser")
    imgs = soup.find_all("img")
    print(f"ID: {p['id']}")
    print(f"Title: {p['title']}")
    print(f"Labels: {p.get('labels')}")
    print(f"Image count: {len(imgs)}")
    for img in imgs:
        print(f"  Image src: {img.get('src')}")
    fig = soup.find("figcaption")
    if fig:
        print(f"  Figcaption: {fig.get_text().strip()}")
    print("-" * 60)
