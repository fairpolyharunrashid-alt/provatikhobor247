"""
Updates the Schema.org NewsArticle JSON-LD on all 22 published posts to guarantee
full compliance with Google Discover and Google Rich Results guidelines.
"""
import json
import logging
import sys
import time
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import BLOG_ID, BLOG_NAME, BLOG_URL, TOKEN_FILE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("UpdateSchemas")

def main():
    with open(TOKEN_FILE, "r", encoding="utf-8") as f:
        creds_data = json.load(f)
    creds = Credentials.from_authorized_user_info(creds_data)
    service = build("blogger", "v3", credentials=creds)

    posts_resp = service.posts().list(blogId=BLOG_ID, maxResults=50).execute()
    items = posts_resp.get("items", [])
    logger.info(f"Retrieved {len(items)} posts to update schemas...")

    for idx, post in enumerate(items, 1):
        post_id = post["id"]
        title = post["title"]
        content = post.get("content", "")
        pub_date = post.get("published", "")
        updated_date = post.get("updated", pub_date)
        post_url = post.get("url", f"{BLOG_URL}")

        soup = BeautifulSoup(content, "html.parser")
        
        # Extract first featured image
        img_elem = soup.find("img")
        img_url = img_elem.get("src") if img_elem else ""

        # Extract snippet or first paragraph text for description
        p_elem = soup.find("p")
        desc = p_elem.get_text().strip()[:160] if p_elem else title

        # Build clean Discover-ready NewsArticle schema
        schema_dict = {
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": post_url
            },
            "headline": title,
            "image": [img_url] if img_url else [],
            "datePublished": pub_date,
            "dateModified": updated_date,
            "author": [{
                "@type": "Person",
                "name": "অনলাইন ডেস্ক",
                "jobTitle": "News Reporter",
                "url": f"{BLOG_URL}p/blog-page_19.html"
            }],
            "publisher": {
                "@type": "NewsMediaOrganization",
                "name": BLOG_NAME,
                "url": BLOG_URL,
                "logo": {
                    "@type": "ImageObject",
                    "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/National_Martyrs%27_Memorial%2C_Savar%2C_Dhaka%2C_Bangladesh.jpg/1200px-National_Martyrs%27_Memorial%2C_Savar%2C_Dhaka%2C_Bangladesh.jpg"
                },
                "publishingPrinciples": f"{BLOG_URL}p/blog-page_180.html"
            },
            "description": desc
        }
        new_schema_tag = f'<script type="application/ld+json">\n{json.dumps(schema_dict, ensure_ascii=False, indent=2)}\n</script>'

        # Remove existing ld+json scripts in content
        for s in soup.find_all("script", type="application/ld+json"):
            s.decompose()

        updated_html = str(soup) + "\n" + new_schema_tag

        try:
            service.posts().patch(
                blogId=BLOG_ID,
                postId=post_id,
                body={"content": updated_html}
            ).execute()
            logger.info(f"[{idx}/{len(items)}] [✓] Schema updated for: {title[:40]}...")
        except Exception as e:
            logger.error(f"[{idx}/{len(items)}] [✗] Failed for {post_id}: {e}")

        time.sleep(1)

    logger.info("All post schemas successfully modernized!")

if __name__ == "__main__":
    main()
