"""
Blogger OAuth 2.0 Authorization for Bangladesh News Portal (প্রভাতী খবর ২৪).
Dedicated login configured for: fairpolyharunrashid@gmail.com
Target Blog ID: 2941397978971258684
"""
import json
import os
import sys
import wsgiref.simple_server
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from google_auth_oauthlib.flow import InstalledAppFlow, _RedirectWSGIApp, _WSGIRequestHandler, _ExclusiveWSGIServer
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

    port = 8088
    print(f"\n[*] Starting local redirect server on port {port}...", flush=True)

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CLIENT_SECRETS_FILE),
        scopes=SCOPES
    )

    wsgi_app = _RedirectWSGIApp("Authorization Successful! You may now close this browser tab.")
    local_server = wsgiref.simple_server.make_server(
        "localhost",
        port,
        wsgi_app,
        server_class=_ExclusiveWSGIServer,
        handler_class=_WSGIRequestHandler,
    )

    try:
        flow.redirect_uri = f"http://localhost:{port}/"
        auth_url, _ = flow.authorization_url(
            prompt="consent",
            login_hint=TARGET_EMAIL,
            access_type="offline"
        )

        # Write to desktop link file
        desktop_link = Path("C:/Users/Harun/Desktop/GOOGLE_LOGIN_LINK.txt")
        desktop_link.write_text(f"{auth_url}\n", encoding="utf-8")

        # Open in browser on desktop
        try:
            os.startfile(auth_url)
            print("[✓] Default browser launched with Google Authorization link!", flush=True)
        except Exception as e:
            print(f"[!] Could not launch browser automatically: {e}", flush=True)

        print("\n" + "=" * 75, flush=True)
        print("AUTH_URL_START", flush=True)
        print(auth_url, flush=True)
        print("AUTH_URL_END", flush=True)
        print("=" * 75 + "\n", flush=True)
        print("[*] Waiting for user authorization in browser...", flush=True)

        local_server.handle_request()

        authorization_response = wsgi_app.last_request_uri.replace("http:", "https:")
        flow.fetch_token(authorization_response=authorization_response)

        TOKEN_FILE.write_text(flow.credentials.to_json(), encoding="utf-8")
        print(f"\n[SUCCESS] নতুন টোকেন সফলভাবে সেভ হয়েছে: {TOKEN_FILE.name}", flush=True)

        service = build("blogger", "v3", credentials=flow.credentials)
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
    finally:
        local_server.server_close()


if __name__ == "__main__":
    main()
