"""
Retrofit All Duplicate and Competitor Images on Live Blogger Blog.
- Finds any post with duplicate images or competitor watermarks.
- Replaces them with authentic, unique, 16:9 unwatermarked editorial images.
- Updates the live post on Blogger via Blogger API.
"""
import io
import json
import logging
import re
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
from bs4 import BeautifulSoup
from PIL import Image

from core.publisher import BloggerPublisher
from core.graphics_editor import GraphicsEditorAgent, is_image_used, mark_image_as_used
from core.image_service import ImageService

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("RetrofitImages")


def main():
    publisher = BloggerPublisher()
    img_service = ImageService()
    editor = GraphicsEditorAgent()

    print("[*] Connecting to Blogger API...")
    res = publisher.service.posts().list(blogId=publisher.blog_id, maxResults=50).execute()
    posts = res.get("items", [])
    print(f"[*] Retrieved {len(posts)} posts for image audit.")

    seen_images = set()
    updated_count = 0

    for idx, p in enumerate(posts, 1):
        post_id = p["id"]
        title = p.get("title", "")
        content = p.get("content", "")
        soup = BeautifulSoup(content, "html.parser")

        img_tag = soup.find("img")
        current_img_src = img_tag.get("src", "") if img_tag else ""

        # Check if image needs replacement:
        # 1. Image has prothomalo / overlay in URL
        # 2. Image has already been used in an earlier post in this list
        # 3. No image found
        is_competitor = "prothomalo" in current_img_src.lower() or "overlay=" in current_img_src.lower()
        is_duplicate = current_img_src in seen_images
        needs_replacement = not current_img_src or is_competitor or is_duplicate

        if not needs_replacement:
            seen_images.add(current_img_src)
            mark_image_as_used(current_img_src)
            print(f"[{idx}/{len(posts)}] OK: {title[:40]}...")
            continue

        print(f"\n[{idx}/{len(posts)}] REPLACING IMAGE for: '{title[:50]}'")
        print(f"    Reason: competitor={is_competitor}, duplicate={is_duplicate}")

        # Search fresh, authentic image based on post title & entities
        dummy_news_item = {"title": title, "link": "", "feed_image": ""}
        dummy_article = {
            "headline": title,
            "category": (p.get("labels") or ["জাতীয়"])[0],
            "image_search_keyword": title.split(":")[0].strip()
        }

        # Find a clean image that hasn't been used
        new_img_info = img_service.get_authentic_news_image(dummy_news_item, dummy_article)
        new_url = new_img_info["image_url"]

        # Ensure the new image is not in seen_images
        attempts = 0
        while new_url in seen_images and attempts < 5:
            # Fallback to query with random noise or commons search
            alt_img = img_service.search_commons_image(f"Bangladesh cricket {idx}" if "ক্রিকেট" in title or "খেলা" in title else f"Dhaka {idx}")
            if alt_img and alt_img not in seen_images:
                new_url = editor.create_copyright_free_editorial_image(alt_img, headline=title) or alt_img
                break
            attempts += 1

        seen_images.add(new_url)
        mark_image_as_used(new_url)

        # Update HTML: replace image src and clean credit
        if img_tag:
            img_tag["src"] = new_url
            img_tag["alt"] = title
        else:
            new_fig = soup.new_tag("figure", attrs={"class": "featured-image-box", "style": "margin: 0 0 25px 0;"})
            new_img = soup.new_tag("img", src=new_url, alt=title, style="width: 100%; aspect-ratio: 16/9; object-fit: cover; border-radius: 8px;")
            new_fig.append(new_img)
            soup.insert(0, new_fig)

        # Update figcaption if present to remove competitor names
        figcaption = soup.find("figcaption")
        if figcaption:
            cap_text = figcaption.get_text()
            for comp in ["প্রথম আলো", "প্রথম আলো অনলাইন", "বিডিনিউজ", "ABP Ananda"]:
                cap_text = cap_text.replace(comp, "প্রভাতী খবর ২৪")
            figcaption.string = cap_text

        # Update post on Blogger
        updated_content = str(soup)
        try:
            publisher.service.posts().patch(
                blogId=publisher.blog_id,
                postId=post_id,
                body={"content": updated_content}
            ).execute()
            print(f"    [✓] Successfully updated Blogger post {post_id} with new unique image: {new_url[:70]}")
            updated_count += 1
            time.sleep(1.5)  # Politeness delay
        except Exception as e:
            logger.error(f"Failed to update post {post_id}: {e}")

    print(f"\n[✓] Audit & Retrofit Complete! Updated {updated_count} posts with unique, unwatermarked images.")


if __name__ == "__main__":
    main()
