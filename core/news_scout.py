"""
Bangladesh News Scout: Scrapes and aggregates trending Bangladesh news from RSS feeds.
Includes dedicated per-section discovery, rotation, and smart topic deduplication.
"""
import base64
import logging
import random
import re
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup

from config.settings import GENERAL_FEEDS, SECTION_FEEDS
from core.db import is_news_scraped

logger = logging.getLogger(__name__)


def decode_google_news_url(url: str) -> str:
    """Decodes Google News redirected URL to original publisher URL."""
    if "news.google.com" in url:
        try:
            from googlenewsdecoder import gnewsdecoder
            res = gnewsdecoder(url)
            if res.get("success") and res.get("decoded_url"):
                return res["decoded_url"]
        except Exception as e:
            logger.debug(f"gnewsdecoder failed for {url}: {e}")

        # Fallback legacy token decode
        if "/articles/" in url:
            token = url.split("/articles/")[-1].split("?")[0]
            try:
                raw = base64.urlsafe_b64decode(token + "==")
                match = re.search(rb"https?://[^\x00-\x20\x7f-\xff]+", raw)
                if match:
                    return match.group(0).decode("utf-8", errors="ignore")
            except Exception:
                pass
    return url


def is_topic_duplicate(new_title: str, excluded_titles: List[str]) -> bool:
    """Checks if new_title covers the same core event as any excluded title based on keyword overlap."""
    if not excluded_titles or not new_title:
        return False

    def extract_keywords(text: str) -> set:
        words = re.findall(r'[\u0980-\u09FF\w]{3,}', text.lower())
        stop_words = {
            "জন্য", "করল", "হলে", "নিয়ে", "করে", "থেকে", "সাথে", "হতে", "আছে", "হলো",
            "কাছে", "পর", "বড়", "এই", "সেই", "নতুন", "আজ", "গতকাল", "জানা", "গেছে",
            "দিল", "হবে", "হচ্ছে", "কথা", "দল", "ম্যাচ", "খবর", "সংবাদ", "প্রথম", "আলো",
            "বাংলাদেশ", "জাতীয়"
        }
        return {w for w in words if w not in stop_words}

    new_kw = extract_keywords(new_title)
    if len(new_kw) < 2:
        return False

    for ex in excluded_titles:
        ex_kw = extract_keywords(ex)
        overlap = new_kw & ex_kw
        # If 2 or more distinct core keywords match (e.g. 'জিম্বাবুয়ে' and '৯৯')
        if len(overlap) >= 2:
            return True
        # If exact substring
        if len(ex) > 10 and (ex.lower() in new_title.lower() or new_title.lower() in ex.lower()):
            return True

    return False


class NewsScout:
    """Discovers and parses breaking news across all editorial sections."""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

    def fetch_feed(self, url: str) -> List[Dict[str, Any]]:
        items = []
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=12) as resp:
                xml_data = resp.read()
            root = ET.fromstring(xml_data)

            for item in root.findall(".//item"):
                title_elem = item.find("title")
                link_elem = item.find("link")
                desc_elem = item.find("description")
                pub_elem = item.find("pubDate")

                if title_elem is not None and title_elem.text:
                    title = title_elem.text.strip()
                    link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                    raw_desc = desc_elem.text.strip() if desc_elem is not None and desc_elem.text else ""

                    clean_desc = BeautifulSoup(raw_desc, "html.parser").get_text() if raw_desc else ""
                    pub_date = pub_elem.text.strip() if pub_elem is not None and pub_elem.text else ""

                    feed_image = ""
                    for child in item:
                        tag_lower = child.tag.lower()
                        if ("content" in tag_lower or "thumbnail" in tag_lower or "enclosure" in tag_lower) and "url" in child.attrib:
                            candidate = child.attrib["url"]
                            if candidate and not any(bad in candidate.lower() for bad in ["google", "logo", "icon", "1x1"]):
                                feed_image = candidate
                                break

                    source = "বাংলাদেশ সংবাদ"
                    if " - " in title:
                        parts = title.rsplit(" - ", 1)
                        title = parts[0].strip()
                        source = parts[1].strip()

                    items.append({
                        "title": title,
                        "link": link,
                        "summary": clean_desc,
                        "source": source,
                        "published_at": pub_date,
                        "feed_image": feed_image
                    })
        except Exception as e:
            logger.error(f"Error fetching feed {url}: {e}")
        return items

    def get_fresh_story_for_section(self, section_name: str, excluded_titles: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Returns the top fresh, unprocessed news item specifically for the given section.
        Enforces strict topic deduplication and feed diversity.
        """
        excluded = excluded_titles or []
        feed_config = SECTION_FEEDS.get(section_name)
        urls = list(feed_config) if isinstance(feed_config, list) else ([feed_config] if feed_config else [])

        # Shuffle/rotate feed sources so sports doesn't just hit the same match over and over
        if len(urls) > 1:
            random.shuffle(urls)

        for url in urls:
            items = self.fetch_feed(url)
            for it in items:
                title_clean = it["title"].strip()
                if not is_news_scraped(title_clean):
                    if not is_topic_duplicate(title_clean, excluded):
                        it["link"] = decode_google_news_url(it["link"])
                        it["target_section"] = section_name
                        return it

        # Fallback to general feeds if specific feed has no fresh items
        for gen_url in GENERAL_FEEDS:
            items = self.fetch_feed(gen_url)
            for it in items:
                title_clean = it["title"].strip()
                if not is_news_scraped(title_clean):
                    if not is_topic_duplicate(title_clean, excluded):
                        it["link"] = decode_google_news_url(it["link"])
                        it["target_section"] = section_name
                        return it

        return None
