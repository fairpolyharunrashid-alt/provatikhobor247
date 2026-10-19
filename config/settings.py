"""
Configuration settings for Autonomous Bangladesh News Portal (প্রভাতী খবর ২৪).
Styled after Prothom Alo, powered by Google Gemini Multi-Key Pool.
"""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Blogger Configurations
BLOG_ID = os.environ.get("BLOG_ID", "2941397978971258684")  # প্রভাতী খবর ২৪
BLOG_NAME = "প্রভাতী খবর ২৪"
BLOG_URL = "https://provatikhobor24.blogspot.com/"

CLIENT_SECRETS_FILE = CONFIG_DIR / "client_secrets.json"
TOKEN_FILE = CONFIG_DIR / "blogger_token.json"

# Google Gemini API Keys Pool (Auto-rotating across active accounts)
env_keys = os.environ.get("GEMINI_API_KEYS")
if env_keys:
    GEMINI_API_KEYS = [k.strip() for k in env_keys.split(",") if k.strip()]
else:
    GEMINI_API_KEYS = [
        "AQ.Ab8RN6Igdxpuh7jleUmDRo5Z2otYThlUAimsOcloBxLpqUiwMw",
        "AQ.Ab8RN6LPKiE3RVQUsqoY0ywB5uTP0eJnTGPP1XnxANSlxMH9yw",
        "AQ.Ab8RN6JTV2Hg6WaaTbmME66gbOoOQFUbSAttecVYC4DMhFv-BA"
    ]

GEMINI_MODEL = "gemini-flash-latest"

# Editorial News Sections (খেলাধুলা prioritized with high frequency)
SECTIONS = [
    "খেলা",        # Prioritized at the top
    "জাতীয়",
    "রাজনীতি",
    "অর্থনীতি",
    "আন্তর্জাতিক",
    "প্রযুক্তি",
    "বিনোদন"
]

# Dedicated Live News Feeds for Each Editorial Section
SECTION_FEEDS = {
    "খেলা": [
        "https://news.google.com/rss/search?q=%E0%A6%95%E0%A7%8D%E0%A6%B0%E0%A6%BF%E0%A6%95%E0%A7%87%E0%A6%9F%20%E0%A6%AC%E0%A6%BE%E0%A6%82%E0%A6%B2%E0%A6%BE%E0%A6%A6%E0%A7%87%E0%A6%B6&hl=bn&gl=BD&ceid=BD:bn",  # ক্রিকেট বাংলাদেশ
        "https://news.google.com/rss/headlines/section/topic/SPORTS?hl=bn&gl=BD&ceid=BD:bn",  # খেলার শীর্ষ সংবাদ
        "https://news.google.com/rss/search?q=%E0%A6%AB%E0%A7%81%E0%A6%9F%E0%A6%AC%E0%A6%B2&hl=bn&gl=BD&ceid=BD:bn",  # ফুটবল সংবাদ
        "https://news.google.com/rss/search?q=%E0%A6%96%E0%A7%87%E0%A6%B2%E0%A6%BE%E0%A6%A7%E0%A7%81%E0%A6%B2%E0%A6%BE&hl=bn&gl=BD&ceid=BD:bn",  # খেলাধুলা
    ],
    "জাতীয়": "https://news.google.com/rss/headlines/section/topic/NATION?hl=bn&gl=BD&ceid=BD:bn",
    "রাজনীতি": "https://news.google.com/rss/search?q=%E0%A6%B0%E0%A6%BE%E0%A6%9C%E0%A6%A8%E0%A7%80%E0%A6%A4%E0%A6%BF&hl=bn&gl=BD&ceid=BD:bn",
    "অর্থনীতি": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=bn&gl=BD&ceid=BD:bn",
    "আন্তর্জাতিক": "https://news.google.com/rss/headlines/section/topic/WORLD?hl=bn&gl=BD&ceid=BD:bn",
    "প্রযুক্তি": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=bn&gl=BD&ceid=BD:bn",
    "বিনোদন": "https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=bn&gl=BD&ceid=BD:bn",
}

# General breaking news fallback feeds
GENERAL_FEEDS = [
    "https://www.prothomalo.com/feed",
    "https://news.google.com/rss?hl=bn&gl=BD&ceid=BD:bn"
]

# Scheduler Interval (Hourly cycle: 60 minutes)
HOURLY_CYCLE_MINUTES = 60
