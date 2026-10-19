import sqlite3
import sys
from googlenewsdecoder import gnewsdecoder
from core.image_service import ImageService

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

svc = ImageService()
conn = sqlite3.connect(r"C:\Users\Harun\.gemini\antigravity\scratch\bd-news-portal\data\news_portal.db")
conn.row_factory = sqlite3.Row
rows = conn.execute("SELECT * FROM published_articles ORDER BY id DESC").fetchall()

print(f"Total published articles in DB: {len(rows)}\n")

for r in rows:
    post_id = r["blogger_post_id"]
    title = r["title"]
    source_title = r["source_title"]
    print(f"[{post_id}] {title}")
    
    sn = conn.execute("SELECT source_url, source_name FROM scraped_news WHERE title LIKE ?", ("%" + source_title[:20] + "%",)).fetchone()
    if sn and sn["source_url"]:
        print(f"  Source: {sn['source_name']}")
        try:
            dec = gnewsdecoder(sn["source_url"])
            if dec.get("success"):
                real_url = dec["decoded_url"]
                print(f"  Decoded: {real_url}")
                og = svc.scrape_article_og_image(real_url)
                print(f"  OG Image: {og}")
            else:
                print(f"  Decoder fail: {dec}")
        except Exception as e:
            print(f"  Decoder error: {e}")
    else:
        print("  Not found in scraped_news")
    print("-" * 50)
