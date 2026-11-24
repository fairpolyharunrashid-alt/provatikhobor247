"""
Editorial Opinion Agent: Acts as the Editor-in-Chief (প্রধান সম্পাদক / সম্পাদকীয় পরিষদ).
At the end of the day, reviews all major news stories published across categories
and crafts an insightful, objective, and engaging editorial analysis for the 'মতামত' section.
"""
import logging
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.llm_pool import LLMPool
from core.publisher import BloggerPublisher
from core.graphics_editor import GraphicsEditorAgent, is_image_used, mark_image_as_used

logger = logging.getLogger(__name__)

EDITORIAL_PROMPT = """
আপনি 'প্রভাতী খবর ২৪'-এর প্রধান সম্পাদক এবং অভিজ্ঞ প্রবীণ কলামিস্ট।
আপনার দায়িত্ব হলো সারাদিনের গুরুত্বপূর্ণ ঘটনাবলী (রাজনীতি, অর্থনীতি, আন্তর্জাতিক, ক্রীড়া ও জনজীবন) গভীরভাবে পর্যালোচনা করে দিনশেষে একটি অত্যন্ত সমৃদ্ধ, মননশীল, দায়িত্বশীল ও পাঠযোগ্য 'সম্পাদকীয় কলাম / মতামত' (Daily Editorial Opinion Essay) রচনা করা।

লেখার বিশেষ সম্পাদকীয় নির্দেশনা:
১. নিরপেক্ষ, ভারসাম্যপূর্ণ, যুক্তিভিত্তিক ও নাগরিক দৃষ্টিভঙ্গি বজায় রাখবেন। কোনো বিশেষ দল বা গোষ্ঠীর পক্ষপাতিত্ব করবেন না।
২. সারাদিনের বিভিন্ন খবরের সংযোগ স্থাপন করবেন (যেমন: অর্থনৈতিক চাপ, বৈশ্বিক ভূরাজনীতি, তরুণদের সম্ভাবনা ও খেলাধুলা, নাগরিক জীবনের নিরাপত্তা ইত্যাদি)।
৩. গঠনমূলক সমাধান ও নীতি-নির্ধারকদের প্রতি ইতিবাচক প্রত্যাশা তুলে ধরবেন।
৪. প্রথম আলো, ডেইলি স্টার বা নিউইয়র্ক টাইমসের সম্পাদকীয় নিবন্ধের মতো সাবলীল, প্রাঞ্জল ও গভীর বাংলা ভাষা ব্যবহার করবেন।
৫. শব্দসংখ্যা: ৫০০ থেকে ৭৫০ শব্দ। পর্যাপ্ত প্যারাগ্রাফ এবং আকর্ষণীয় সাব-হেডিং (<h2>) ব্যবহার করবেন।

আউটপুট অবশ্যই নিচের JSON ফরম্যাটে হতে হবে:
{
    "headline": "আকর্ষণীয় ও ভাবগম্ভীর সম্পাদকীয় শিরোনাম (যেমন: 'দিনের ফিরে দেখা: অর্থনৈতিক বাস্তবতা ও জনজীবনের স্বস্তি খোঁজার দায়')",
    "kicker": "সম্পাদকীয় অভিমত",
    "category": "মতামত",
    "meta_description": "১৩০-১৬০ অক্ষরের শক্তিশালী এসইও মেটা ডেসক্রিপশন",
    "key_highlights": [
        "মূল সম্পাদকীয় দৃষ্টিভঙ্গি ১",
        "মূল সম্পাদকীয় দৃষ্টিভঙ্গি ২",
        "মূল সম্পাদকীয় দৃষ্টিভঙ্গি ৩"
    ],
    "content_html": "পুরো সম্পাদকীয় নিবন্ধের বডি HTML ফরম্যাটে (প্যারাগ্রাফ <p>, সাব-হেড <h2> সহ ৫০০-৭৫০ শব্দ)।",
    "photo_caption": "ছবির বিবরণ (যেমন: ফাইল ছবি: প্রতীকী সম্পাদকীয় প্রতিফলন)",
    "photo_credit": "ছবি: প্রভাতী খবর ২৪"
}
"""

OPINION_IMAGES_POOL = [
    "https://images.unsplash.com/photo-1455390582262-044cdead277a?auto=format&fit=crop&w=1200&h=675&q=85",  # Fountain pen & writing
    "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?auto=format&fit=crop&w=1200&h=675&q=85",  # Newspapers & coffee
    "https://images.unsplash.com/photo-1505664194779-8beaceb93744?auto=format&fit=crop&w=1200&h=675&q=85",  # Library / books / thoughtful
    "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&h=675&q=85",  # Earth / Global perspective
    "https://images.unsplash.com/photo-1541872703-74c5e44368f9?auto=format&fit=crop&w=1200&h=675&q=85",  # Parliament / Governance
    "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&h=675&q=85",  # Tech & Future
]


class EditorialAgent:
    """Produces the daily flagship editorial analysis."""

    def __init__(self, publisher: Optional[BloggerPublisher] = None, llm_pool: Optional[LLMPool] = None):
        self.publisher = publisher or BloggerPublisher()
        self.llm = llm_pool or LLMPool()
        self.editor = GraphicsEditorAgent()

    def get_todays_stories_summary(self, max_posts: int = 20) -> List[Dict[str, str]]:
        """Gathers latest published post titles and categories from Blogger."""
        try:
            res = self.publisher.service.posts().list(
                blogId=self.publisher.blog_id,
                maxResults=max_posts
            ).execute()
            items = res.get("items", [])
            summaries = []
            for it in items:
                title = it.get("title", "")
                labels = it.get("labels", [])
                category = labels[0] if labels else "সাধারণ"
                # Exclude previous opinion posts from the news list
                if "মতামত" not in labels:
                    summaries.append({
                        "title": title,
                        "category": category
                    })
            return summaries
        except Exception as e:
            logger.warning(f"Failed to fetch today's stories for editorial: {e}")
            return []

    def generate_editorial_opinion(self, stories: List[Dict[str, str]]) -> Dict[str, Any]:
        """Synthesizes the day's stories into an in-depth editorial opinion essay."""
        stories_text = "\n".join([f"- [{s.get('category', 'সংবাদ')}] {s.get('title')}" for s in stories[:15]])
        now_str = datetime.now().strftime("%d %B %Y")

        prompt = f"""
তারিখ: {now_str}
আজকের দিনে 'প্রভাতী খবর ২৪'-এ প্রকাশিত প্রধান সংবাদের শিরোনাম ও বিষয়সমূহ:

{stories_text}

উপরের সার্বিক খবরের গতিপ্রকৃতি, অর্থনৈতিক অবস্থা, রাজনৈতিক বাস্তবতা এবং জাতীয় জনজীবনের প্রেক্ষাপট পর্যালোচনা করে আজকের একটি পূর্ণাঙ্গ, ভাবগম্ভীর ও প্রাঞ্জল 'সম্পাদকীয় কলাম / মতামত' রচনা করুন।
"""

        result = self.llm.generate_json(
            prompt=prompt,
            system_instruction=EDITORIAL_PROMPT,
            temperature=0.4
        )

        result["category"] = "মতামত"
        return result

    def publish_daily_editorial(self) -> Optional[str]:
        """End-to-end: gathers stories, crafts editorial opinion, cleans image, and publishes."""
        print("\n" + "=" * 70, flush=True)
        print("  [EDITORIAL AGENT] প্রধান সম্পাদকীয় কলাম প্রস্তুত করা হচ্ছে...", flush=True)
        print("=" * 70, flush=True)

        stories = self.get_todays_stories_summary(max_posts=20)
        if not stories:
            print("[!] সম্পাদকীয় রচনার জন্য কোনো পূর্ববর্তী খবর পাওয়া যায়নি।", flush=True)
            return None

        print(f"[*] সারাদিনের {len(stories)}টি শীর্ষ সংবাদের ওপর ভিত্তি করে সম্পাদকীয় মতামত তৈরি হচ্ছে...", flush=True)
        editorial_data = self.generate_editorial_opinion(stories)
        headline = editorial_data.get("headline", "দিনের ফিরে দেখা ও সম্পাদকীয় অভিমত")

        print(f"[✓] সম্পাদকীয় রচিত হয়েছে: '{headline}'", flush=True)

        # Select unique image from opinion photography pool
        unused = [img for img in OPINION_IMAGES_POOL if not is_image_used(img)]
        raw_img = random.choice(unused) if unused else random.choice(OPINION_IMAGES_POOL)

        # Crop to 16:9, clean, and upload to CDN
        cdn_img_url = self.editor.create_copyright_free_editorial_image(raw_img, headline=headline) or raw_img
        mark_image_as_used(cdn_img_url)

        image_info = {
            "image_url": cdn_img_url,
            "caption": editorial_data.get("photo_caption", f"প্রতীকী ছবি: {headline}"),
            "credit": "ছবি: প্রভাতী খবর ২৪"
        }

        # Build and publish HTML
        post_html = self.publisher.build_post_html(editorial_data, image_info)
        labels = ["মতামত", "সম্পাদকীয়", "প্রভাতী খবর ২৪", "তাজা খবর"]

        print(f"[*] ব্লগারে 'মতামত' বিভাগে প্রকাশিত হচ্ছে...", flush=True)
        res = self.publisher.publish_news(
            article=editorial_data,
            image_info=image_info,
            source_title="দৈনিক সম্পাদকীয় বিশ্লেষণ ও মতামত"
        )
        post_url = res.get("url")

        print(f"\n[✓] দৈনিক সম্পাদকীয় মতামত সফলভাবে প্রকাশিত হয়েছে!", flush=True)
        print(f"    URL: {post_url}\n", flush=True)
        return post_url
