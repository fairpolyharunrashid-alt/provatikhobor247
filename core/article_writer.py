"""
Article Writer: Transforms raw trending news into Prothom Alo-standard Bengali news reports.
Includes kickers, bold lead paragraphs, subheadings, key takeaways, and search queries for authentic images.
"""
import logging
from typing import Any, Dict, Optional

from core.llm_pool import LLMPool

logger = logging.getLogger(__name__)

PROTHOM_ALO_SYSTEM_PROMPT = """
আপনি বাংলাদেশের শীর্ষ জাতীয় দৈনিক (যেমন 'প্রথম আলো')-এর একজন সিনিয়র চিফ রিপোর্টার ও হেড অব নিউজ।
আপনার কাজ হলো প্রাপ্ত সংবাদের তথ্যের ভিত্তিতে ১০০% নিরপেক্ষ, বস্তুনিষ্ঠ, সাবলীল ও উচ্চমানের বাংলা সাংবাদিকতার নিয়মে একটি পূর্ণাঙ্গ নিউজ রিপোর্ট তৈরি করা।

নীতিমালা:
১. ভাষা হবে প্রমিত বাংলা, ব্যাকরণগতভাবে নিখুঁত ও প্রাতিষ্ঠানিক (যেমন প্রথম আলোর প্রথম পাতা বা জাতীয় পাতার রিপোর্ট)।
২. কোনো পক্ষপাতিত্ব থাকবে না।
৩. হেডলাইন হবে আকর্ষণীয় কিন্তু সত্য ও বস্তুনিষ্ঠ।
৪. লিড প্যারাগ্রাফে সংবাদের মূল ৫W১H (কে, কী, কোথায়, কখন, কেন, কীভাবে) থাকবে।
৫. রিপোর্টে উপযুক্ত সাব-হেডিং (<h2>, <h3>) ব্যবহার করবেন।
৬. পাঠকদের দ্রুত ধারণার জন্য সংবাদের শুরুতে একটি "এক নজরে মূল তথ্য" (Key Highlights) বুলেট পয়েন্ট থাকবে।
৭. সংবাদের জন্য উপযুক্ত ছবির সার্চ কি-ওয়ার্ড (image_search_keyword) প্রদান করবেন যাতে ঘটনার মূল ব্যক্তি বা প্রতিষ্ঠানের আসল ছবি খুঁজে পাওয়া যায়।
৮. ছবির জন্য বস্তুনিষ্ঠ ক্যাপশন (photo_caption) ও ক্রেডিট (photo_credit) উল্লেখ করবেন।
"""


class ArticleWriter:
    def __init__(self, llm_pool: LLMPool):
        self.llm = llm_pool

    def write_news_article(self, news_item: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a complete journalistic news article in Bengali."""
        target_sec = news_item.get('target_section', '')
        category_instruction = f'ক্যাটাগরি হিসেবে অবশ্যই "{target_sec}" নির্বাচন করুন।' if target_sec else 'ক্যাটাগরি নির্বাচন করুন (জাতীয়, রাজনীতি, অর্থনীতি, খেলা, প্রযুক্তি, আন্তর্জাতিক, বিনোদন)'

        prompt = f"""
নিচের সংবাদের সারসংক্ষেপ ও তথ্যের ওপর ভিত্তি করে 'প্রথম আলো'-র স্ট্যান্ডার্ডে একটি সমৃদ্ধ বাংলা নিউজ আর্টিকেল লিখুন:

মূল শিরোনাম: {news_item.get('title')}
সংবাদের উৎস: {news_item.get('source')}
প্রাপ্ত বিবরণ: {news_item.get('summary')}
লিংক: {news_item.get('link')}
{f"উদ্দিষ্ট সেকশন: {target_sec}" if target_sec else ""}

আপনাকে নিচের JSON স্কিমায় সম্পূর্ণ ফলাফল প্রদান করতে হবে:
{{
    "headline": "প্রধান শিরোনাম (প্রথম আলোর স্টাইলে দৃষ্টিনন্দন বাংলা শিরোনাম)",
    "kicker": "উপ-শিরোনাম বা প্রেক্ষাপট (যেমন: রাজনীতি / আদালত / অর্থনীতি / খেলা)",
    "category": "{target_sec if target_sec else category_instruction}",
    "meta_description": "১৩০-১৬০ অক্ষরের শক্তিশালী এসইও মেটা ডেসক্রিপশন",
    "image_search_keyword": "ছবি অনুসন্ধানের জন্য মূল ব্যক্তি/প্রতিষ্ঠান/বিষয়ের নাম (যেমন: 'ইশরাক হোসেন' বা 'সৌদি আরব আদালত')",
    "photo_caption": "ছবির প্রাসঙ্গিক বিবরণ/ক্যাপশন (যেমন: ইশরাক হোসেনের ফাইল ছবি)",
    "photo_credit": "ছবির ক্রেডিট (যেমন: ছবি: প্রথম আলো / ফাইল ছবি: রয়টার্স / ছবি: সংগৃহীত)",
    "key_highlights": [
        "মূল পয়েন্ট ১",
        "মূল পয়েন্ট ২",
        "মূল পয়েন্ট ৩"
    ],
    "content_html": "পুরো নিউজ রিপোর্টের বডি HTML ফরম্যাটে (প্যারাগ্রাফ <p>, সাব-হেড <h2> সহ অন্তত ৩৫০-৬০০ শব্দ)। প্রথম প্যারাগ্রাফে সংবাদের সম্পূর্ণ সারসংক্ষেপ থাকবে।"
}}
"""
        result = self.llm.generate_json(
            prompt=prompt,
            system_instruction=PROTHOM_ALO_SYSTEM_PROMPT,
            temperature=0.3
        )
        if target_sec:
            result["category"] = target_sec
        return result
