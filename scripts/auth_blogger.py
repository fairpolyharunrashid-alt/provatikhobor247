"""
Blogger OAuth 2.0 Authorization for Bangladesh News Portal (প্রভাতী খবর ২৪).
Dedicated login configured for: fairpolyharunrashid@gmail.com
Target Blog ID: 2941397978971258684
"""
import json
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
CLIENT_SECRETS_FILE = CONFIG_DIR / "client_secrets.json"
TOKEN_FILE = CONFIG_DIR / "blogger_token.json"
TARGET_BLOG_ID = "2941397978971258684"
TARGET_EMAIL = "fairpolyharunrashid@gmail.com"

SCOPES = ["https://www.googleapis.com/auth/blogger"]


def main():
    print("=" * 75, flush=True)
    print("  প্রভাতী খবর ২৪ (PROVATI KHOBOR 24) -- BLOGGER AUTHORIZATION", flush=True)
    print(f"  Target Account: {TARGET_EMAIL}", flush=True)
    print(f"  Target Blog ID: {TARGET_BLOG_ID}", flush=True)
    print("=" * 75, flush=True)

    if not CLIENT_SECRETS_FILE.exists():
        print(f"[Error] Client secrets file not found: {CLIENT_SECRETS_FILE}", flush=True)
        return

    print(f"\n[*] {TARGET_EMAIL} অ্যাকাউন্টের জন্য গুগল সাইন-ইন প্রস্তুত করা হচ্ছে...", flush=True)

    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CLIENT_SECRETS_FILE),
            scopes=SCOPES
        )

        creds = flow.run_local_server(
            port=0,
            prompt="consent",
            login_hint=TARGET_EMAIL,
            authorization_prompt_message="[AUTH_URL_START]\n{url}\n[AUTH_URL_END]\n\nব্রাউজারে লিঙ্কটি ওপেন না হলে উপরের লিংকে ক্লিক করুন।\n",
            success_message="Authorization Successful! You may now close this window."
        )

        TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
        print(f"\n[SUCCESS] নতুন টোকেন সফলভাবে সেভ হয়েছে: {TOKEN_FILE.name}", flush=True)

        service = build("blogger", "v3", credentials=creds)
        user = service.users().get(userId="self").execute()
        print(f"[✓] লগইন কৃত অ্যাকাউন্ট: {user.get('displayName')} ({user.get('id')})", flush=True)

        # Verify target blog
        blogs = service.blogs().listByUser(userId="self").execute()
        found = False
        print("\n[+] অ্যাক্সেসযোগ্য ব্লগসমূহ:", flush=True)
        for b in blogs.get("items", []):
            print(f" - {b.get('name')} (ID: {b.get('id')}) -> {b.get('url')}", flush=True)
            if str(b.get("id")) == TARGET_BLOG_ID:
                found = True

        if found:
            print(f"\n[SUCCESS] টার্গেট ব্লগ ID {TARGET_BLOG_ID} (প্রভাতী খবর ২৪) সফলভাবে সংযুক্ত ও অনুমোদিত হয়েছে!", flush=True)
        else:
            print(f"\n[INFO] এই অ্যাকাউন্টে ব্লগ আইডি {TARGET_BLOG_ID} তালিকাভুক্ত পাওয়া যায়নি।", flush=True)

    except Exception as e:
        print(f"\n[Error] Authorization failed: {e}", flush=True)


if __name__ == "__main__":
    main()
