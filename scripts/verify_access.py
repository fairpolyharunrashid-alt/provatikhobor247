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
    token_data = json.load(f)

creds = Credentials.from_authorized_user_info(token_data)
service = build("blogger", "v3", credentials=creds)

user = service.users().get(userId="self").execute()
print(f"Logged in user: {user.get('displayName')} ({user.get('id')})")

blogs = service.blogs().listByUser(userId="self").execute()
print("Accessible blogs:")
found = False
for b in blogs.get("items", []):
    print(f" - {b.get('name')} (ID: {b.get('id')}) -> {b.get('url')}")
    if str(b.get("id")) == "2941397978971258684":
        found = True

print(f"\nTarget Blog 2941397978971258684 Found: {found}")
