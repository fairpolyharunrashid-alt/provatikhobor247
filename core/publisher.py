"""
Blogger Publisher: Publishes styled Prothom Alo-format news articles with Schema.org markup.
Guarantees 16:9 featured image appears first for proper thumbnail generation and clean snippet excerpts.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config.settings import BLOG_ID, BLOG_NAME, BLOG_URL, TOKEN_FILE
from core.db import record_published_article

logger = logging.getLogger(__name__)


class BloggerPublisher:
    def __init__(self, token_path: Path = TOKEN_FILE, blog_id: str = BLOG_ID):
        self.token_path = token_path
        self.blog_id = blog_id
        self._service = None

    @property
    def service(self):
        if not self._service:
            import os
            env_token = os.environ.get("BLOGGER_TOKEN_JSON")
            if env_token:
                token_data = json.loads(env_token)
                creds = Credentials.from_authorized_user_info(token_data)
                self._service = build("blogger", "v3", credentials=creds)
                return self._service

            if not self.token_path.exists():
                raise FileNotFoundError(f"OAuth token file not found at: {self.token_path}. Authorization required.")
            with open(self.token_path, "r", encoding="utf-8") as f:
                token_data = json.load(f)
            creds = Credentials.from_authorized_user_info(token_data)
            self._service = build("blogger", "v3", credentials=creds)
        return self._service

    def get_recent_published_titles(self, limit: int = 50) -> List[str]:
        """Fetches the latest published post titles directly from Blogger API."""
        try:
            res = self.service.posts().list(blogId=self.blog_id, maxResults=limit, fields="items(title)").execute()
            return [it["title"].strip() for it in res.get("items", []) if "title" in it]
        except Exception as e:
            logger.warning(f"Failed to fetch recent titles from Blogger: {e}")
            return []

    def build_post_html(self, article: Dict[str, Any], image_info: Dict[str, str]) -> str:
        """Assembles rich Prothom Alo-styled post HTML.
        CRITICAL: The <img> must be at the very top for Blogger thumbnail extraction.
        The JSON-LD schema must be at the very bottom so Blogger's snippet extractor doesn't capture raw JSON!
        """
        headline = article.get("headline", "")
        kicker = article.get("kicker", "")
        category = article.get("category", "জাতীয়")
        highlights = article.get("key_highlights", [])
        body_html = article.get("content_html", "")
        img_url = image_info.get("image_url", "")
        img_caption = image_info.get("caption", headline)
        img_credit = image_info.get("credit", "ছবি: প্রভাতী খবর ২৪")

        # 1. First Element: Featured Image (16:9 aspect ratio, Blogger picks this as the Thumbnail)
        featured_image_html = ""
        if img_url:
            featured_image_html = f"""
            <div class="separator" style="clear: both; text-align: center; margin-bottom: 20px;">
                <figure class="pa-featured-figure" style="margin: 0; padding: 0;">
                    <img border="0" src="{img_url}" alt="{headline}" style="width: 100%; max-height: 550px; object-fit: cover; aspect-ratio: 16/9; border-radius: 6px; display: block;" />
                    <figcaption style="font-size: 13.5px; color: #666; margin-top: 8px; text-align: left; line-height: 1.5; font-family: 'SolaimanLipi', sans-serif;">
                        <span style="font-weight: 700; color: #333;">{img_credit}</span> — {img_caption}
                    </figcaption>
                </figure>
            </div>
            """

        # 2. Key Highlights box
        highlights_html = ""
        if highlights:
            li_tags = "".join(f"<li style='margin-bottom: 6px;'>{h}</li>" for h in highlights)
            highlights_html = f"""
            <div class="pa-highlights-box" style="background: #f8f9fa; border-left: 4px solid #d9232d; padding: 14px 18px; margin: 20px 0; border-radius: 4px;">
                <h4 style="margin: 0 0 10px 0; font-size: 16px; color: #212529; font-weight: 700;">📌 এক নজরে মূল পয়েন্ট</h4>
                <ul style="margin: 0; padding-left: 20px; font-size: 15px; line-height: 1.7; color: #444;">
                    {li_tags}
                </ul>
            </div>
            """

        # 3. Schema.org JSON-LD (Strict Google News & Discover Compliant)
        schema_dict = {
            "@context": "https://schema.org",
            "@type": "NewsArticle",
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": BLOG_URL
            },
            "headline": headline,
            "image": [img_url] if img_url else [],
            "datePublished": f"{datetime.utcnow().isoformat()}Z",
            "dateModified": f"{datetime.utcnow().isoformat()}Z",
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
            "description": article.get("meta_description", headline)
        }
        schema_jsonld = f'<script type="application/ld+json">\n{json.dumps(schema_dict, ensure_ascii=False, indent=2)}\n</script>'

        full_html = f"""{featured_image_html}
        <div class="pa-article-container" style="font-family:'SolaimanLipi','Noto Sans Bengali',sans-serif; line-height:1.85; color:#222; font-size:17.5px;">
            {highlights_html}
            <div class="pa-article-body" style="margin-top:15px;">
                {body_html}
            </div>
            <div class="pa-article-footer" style="margin-top:35px; padding-top:15px; border-top:1px solid #e9ecef; font-size:14px; color:#6c757d;">
                <p><strong>বিভাগ:</strong> {category} | <strong>প্রতিবেদন:</strong> অনলাইন ডেস্ক, {BLOG_NAME}</p>
            </div>
        </div>
        {schema_jsonld}
        """
        return full_html.strip()

    def publish_news(self, article: Dict[str, Any], image_info: Dict[str, str], source_title: str) -> Dict[str, Any]:
        """Publishes the article to Blogger API."""
        headline = article.get("headline", "")
        category = article.get("category", "জাতীয়")
        content_html = self.build_post_html(article, image_info)

        labels = [category, "সংবাদ", "বাংলাদেশ", "তাজা খবর"]
        if category in ["খেলা", "খেলাধুলা"]:
            labels.extend(["খেলা", "খেলাধুলা", "স্পোর্টস"])
        if category in ["জাতীয়", "জাতীয়"]:
            labels.extend(["জাতীয়", "জাতীয়"])
        if category in ["প্রযুক্তি", "বিজ্ঞান ও প্রযুক্তি"]:
            labels.extend(["প্রযুক্তি", "বিজ্ঞান ও প্রযুক্তি"])
        if category in ["অর্থনীতি", "বাণিজ্য", "অর্থনীতি ও বাণিজ্য"]:
            labels.extend(["অর্থনীতি", "বাণিজ্য", "অর্থনীতি ও বাণিজ্য"])
        labels = list(dict.fromkeys(labels))

        body = {
            "kind": "blogger#post",
            "blog": {"id": self.blog_id},
            "title": headline,
            "content": content_html,
            "labels": labels
        }

        result = self.service.posts().insert(
            blogId=self.blog_id,
            body=body,
            isDraft=False
        ).execute()

        post_id = result.get("id")
        post_url = result.get("url")

        logger.info(f"Published article '{headline}' -> {post_url}")
        record_published_article(
            blogger_post_id=post_id,
            title=headline,
            category=category,
            url=post_url,
            source_title=source_title
        )

        return result
