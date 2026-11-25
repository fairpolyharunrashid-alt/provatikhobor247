"""
Chief Editor Agent (প্রধান সম্পাদক ও কোয়ালিটি কন্ট্রোল গেটওয়ে).
Acts as the final strict gatekeeper before any article is published to Blogger.
Enforces:
1. STRICT ZERO-DUPLICATE POLICY: No image may ever be used more than once across the entire site.
2. STRICT TOPIC RELEVANCE: Image must be genuinely relevant to the news topic, person, or event.
3. FEEDBACK LOOP: If rejected, sends actionable rejection feedback back to Graphics/Image Agent for retries.
"""
import json
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import requests

from core.llm_pool import LLMPool
from core.graphics_editor import is_image_used, mark_image_as_used

logger = logging.getLogger(__name__)

CHIEF_EDITOR_SYSTEM_PROMPT = """
আপনি 'প্রভাতী খবর ২৪'-এর প্রধান সম্পাদক (Chief Executive Editor) ও কোয়ালিটি কন্ট্রোল ডিরেক্টর।
আপনার কাজ হলো কোনো সংবাদ ব্লগারে প্রকাশের পূর্বে তার শিরোনাম এবং নির্বাচিত ছবির প্রাসঙ্গিকতা কঠোরভাবে যাচাই করা।

কঠোর সম্পাদকীয় নীতিমালা:
১. ছবির বিষয়বস্তুর প্রাসঙ্গিকতা (STRICT TOPIC RELEVANCE):
   - সংবাদ যদি কোনো নির্দিষ্ট ব্যক্তি (যেমন: সোহেল খান, সালমান খান, পরীমনি, সাকিব আল হাসান), সিনেমা বা সুনির্দিষ্ট ঘটনা নিয়ে হয়, তবে কোনো জেনেরিক ছবি (যেমন: ডিজে কনসার্ট, ফাঁকা সিনেমা হলের সিট, অপ্রাসঙ্গিক পটভূমি) কঠোরভাবে বাতিল (REJECT) করতে হবে।
   - ছবির ক্যাপশন বা উৎসের বিবরণ পড়ে নিশ্চিত হোন যে ছবিটি উক্ত সংবাদের সাথে সরাসরি সম্পর্কিত।
২. অনুমোদনের সিদ্ধান্ত:
   - ছবি প্রাসঙ্গিক হলে: approved = true
   - ছবি অপ্রাসঙ্গিক, অমিল বা জেনেরিক হলে: approved = false এবং কেন বাতিল করা হলো তার কারণ (rejection_reason) ও গ্রাফিক্স এজেন্টের জন্য সঠিক সার্চ কি-ওয়ার্ড (suggested_search_query) প্রদান করতে হবে।
"""


class ChiefEditorAgent:
    def __init__(self, llm_pool: LLMPool, published_images_cache: Optional[Set[str]] = None):
        self.llm = llm_pool
        self.published_images: Set[str] = published_images_cache or set()

    def sync_published_images_from_blogger(self, publisher) -> None:
        """Fetches all image URLs from the last 150 Blogger posts to guarantee live zero-duplicate state."""
        try:
            res = publisher.service.posts().list(
                blogId=publisher.blog_id,
                maxResults=150,
                fields="items(id,content)"
            ).execute()
            for p in res.get("items", []):
                content = p.get("content", "")
                urls = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content)
                for u in urls:
                    clean = u.split("?")[0].strip().lower()
                    self.published_images.add(clean)
                    self.published_images.add(u.strip().lower())
                    mark_image_as_used(u)
            logger.info(f"Chief Editor synced {len(self.published_images)} published image signatures from Blogger.")
        except Exception as e:
            logger.warning(f"Chief Editor sync error: {e}")

    def is_image_duplicate(self, image_url: str) -> bool:
        """Checks if image URL has ever been used across DB, cache, or live site."""
        if not image_url:
            return True
        clean = image_url.split("?")[0].strip().lower()
        if clean in self.published_images or image_url.strip().lower() in self.published_images:
            return True
        if is_image_used(clean) or is_image_used(image_url):
            return True
        return False

    def evaluate_article_and_image(
        self,
        headline: str,
        category: str,
        summary: str,
        image_info: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Chief Editor's strict review before publishing approval.
        Returns:
            {
                "approved": bool,
                "rejection_type": "DUPLICATE" | "IRRELEVANT" | "BROKEN" | None,
                "rejection_reason": str,
                "suggested_query": str
            }
        """
        img_url = image_info.get("image_url", "").strip()
        img_caption = image_info.get("caption", "")
        img_credit = image_info.get("credit", "")

        # 1. Check for empty or broken image URL
        if not img_url or not img_url.startswith("http"):
            return {
                "approved": False,
                "rejection_type": "BROKEN",
                "rejection_reason": "ছবির কোনো বৈধ ইউআরএল পাওয়া যায়নি।",
                "suggested_query": headline.split(":")[0].strip()
            }

        # 2. Check for duplicate image across site
        if self.is_image_duplicate(img_url):
            logger.warning(f"Chief Editor REJECTED image as DUPLICATE: {img_url[:60]}")
            return {
                "approved": False,
                "rejection_type": "DUPLICATE",
                "rejection_reason": f"এই ছবিটি পূর্বে অন্য একটি আর্টিকেলে ব্যবহৃত হয়েছে। কোনো ছবি দ্বিতীয়বার ব্যবহার সম্পূর্ণ নিষিদ্ধ।",
                "suggested_query": headline.split(":")[0].strip()
            }

        # 3. Check for obvious blacklisted generic placeholders (e.g. repeated concert/cinema photos)
        known_generic = [
            "photo-1514525253161-7a46d19cd819",  # DJ / Concert
            "photo-1489599849927-2ee91cede3ba",  # Cinema seats
            "photo-1470225620780-dba8ba36b745",  # Concert lights
        ]
        if any(g in img_url for g in known_generic):
            return {
                "approved": False,
                "rejection_type": "IRRELEVANT",
                "rejection_reason": "জেনেরিক কনসার্ট বা সিনেমা হলের সিটের ছবি নির্দিষ্ট সংবাদের সাথে অপ্রাসঙ্গিক। সংবাদের মূল ব্যক্তি বা বিষয়ের আসল ছবি প্রয়োজন।",
                "suggested_query": headline.split(":")[0].strip()
            }

        # 4. LLM Visual/Semantic Relevance Evaluation
        prompt = f"""
নিচের সংবাদের শিরোনাম ও নির্বাচিত ছবির বিবরণ পর্যালোচনা করে সিদ্ধান্ত দিন ছবিটি সংবাদের সাথে সম্পর্কিত কি না:

শিরোনাম: {headline}
বিভাগ: {category}
সংবাদের সারসংক্ষেপ: {summary}
ছবির ক্যাপশন/বিবরণ: {img_caption}
ছবির ক্রেডিট: {img_credit}
ছবির ইউআরএল: {img_url}

JSON স্কিমা অনুযায়ী ফলাফল দিন:
{{
    "approved": true বা false,
    "rejection_reason": "বাতিল হলে নির্দিষ্ট কারণ (সংক্ষেপে বাংলা)",
    "suggested_search_query": "নতুন ছবি অনুসন্ধানের জন্য উপযুক্ত সঠিক সার্চ কি-ওয়ার্ড (যেমন: ব্যক্তির নাম বা আসল ঘটনার নাম)"
}}
"""
        try:
            decision = self.llm.generate_json(
                prompt=prompt,
                system_instruction=CHIEF_EDITOR_SYSTEM_PROMPT,
                temperature=0.1
            )
            approved = decision.get("approved", True)
            if not approved:
                logger.warning(f"Chief Editor REJECTED image for '{headline}': {decision.get('rejection_reason')}")
                return {
                    "approved": False,
                    "rejection_type": "IRRELEVANT",
                    "rejection_reason": decision.get("rejection_reason", "ছবির সাথে সংবাদের বিষয়বস্তু অসঙ্গতিপূর্ণ।"),
                    "suggested_query": decision.get("suggested_search_query") or headline.split(":")[0].strip()
                }
        except Exception as e:
            logger.warning(f"LLM relevance check error (defaulting to safe pass if not duplicate): {e}")

        # If all checks pass
        return {
            "approved": True,
            "rejection_type": None,
            "rejection_reason": "",
            "suggested_query": ""
        }

    def register_published_image(self, image_url: str):
        """Registers image as permanently used once approved and published."""
        clean = image_url.split("?")[0].strip().lower()
        self.published_images.add(clean)
        self.published_images.add(image_url.strip().lower())
        mark_image_as_used(image_url)
