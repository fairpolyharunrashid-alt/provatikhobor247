"""
Main Orchestrator for Autonomous Bangladesh News Portal (প্রভাতী খবর ২৪).
Styled after Prothom Alo, powered by Google Gemini Multi-Key Pool.
Automated hourly roundups: 1 authentic news post per section every hour.
"""
import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from config.settings import (
    BLOG_ID,
    BLOG_NAME,
    BLOG_URL,
    HOURLY_CYCLE_MINUTES,
    LOG_DIR,
    SECTIONS,
)
from core.article_writer import ArticleWriter
from core.db import init_db, record_scraped_news
from core.image_service import ImageService
from core.llm_pool import LLMPool
from core.news_scout import NewsScout
from core.publisher import BloggerPublisher
from core.editorial_agent import EditorialAgent
from core.chief_editor import ChiefEditorAgent

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "news_portal.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("BDNewsPortal")


class BDNewsEngine:
    def __init__(self):
        logger.info(f"Initializing {BLOG_NAME} Autonomous Engine...")
        init_db()
        self.llm_pool = LLMPool()
        self.scout = NewsScout()
        self.writer = ArticleWriter(self.llm_pool)
        self.image_service = ImageService()
        self.publisher = BloggerPublisher(blog_id=BLOG_ID)
        self.chief_editor = ChiefEditorAgent(self.llm_pool)
        self.chief_editor.sync_published_images_from_blogger(self.publisher)
        self.editorial_agent = EditorialAgent(publisher=self.publisher, llm_pool=self.llm_pool)

    def publish_daily_editorial(self) -> Optional[str]:
        return self.editorial_agent.publish_daily_editorial()

    def process_section_story(self, section_name: str, excluded_titles: list = None) -> bool:
        """Finds, writes, and publishes 1 authentic news article specifically for a section."""
        logger.info(f"\n=======================================================")
        logger.info(f"[*] Scouting fresh story for section: [{section_name}]")
        logger.info(f"=======================================================")

        news_item = self.scout.get_fresh_story_for_section(section_name, excluded_titles=excluded_titles)
        if not news_item:
            logger.info(f"No fresh unprocessed stories available for [{section_name}] right now.")
            return False

        raw_title = news_item["title"]
        source = news_item.get("source", "বাংলাদেশ সংবাদ")
        logger.info(f"Discovered: '{raw_title}' (Source: {source})")

        # 1. Mark as scraped in DB to prevent duplicates
        record_scraped_news(
            title=raw_title,
            source_url=news_item.get("link", ""),
            source_name=source,
            summary=news_item.get("summary", ""),
            published_at=news_item.get("published_at", ""),
        )

        # 2. Write journalistic report with Gemini Multi-Key Pool
        logger.info(f"Generating journalistic report via Gemini Pool for [{section_name}]...")
        try:
            article = self.writer.write_news_article(news_item)
        except Exception as e:
            logger.error(f"Failed to generate article: {e}")
            return False

        # 3. Source authentic 16:9 featured image with credit
        category = article.get("category", section_name)
        headline = article.get("headline", raw_title)

        # Topic alignment sanity check: ensure generated article hasn't drifted from source story
        import re
        raw_words = set(re.findall(r'[\u0980-\u09FF\w]{3,}', raw_title.lower()))
        head_words = set(re.findall(r'[\u0980-\u09FF\w]{3,}', headline.lower()))
        if len(raw_words & head_words) == 0 and len(raw_words) >= 2:
            logger.warning(f"Topic drift detected between raw '{raw_title}' and '{headline}'. Aligning headline to raw title.")
            headline = raw_title
            article["headline"] = raw_title

        # 3. Source authentic 16:9 featured image with STRICT Chief Editor Approval Gate & Feedback Loop
        max_image_attempts = 3
        current_query = None
        approved_image_info = None

        for attempt in range(1, max_image_attempts + 1):
            candidate_image_info = self.image_service.get_authentic_news_image(
                news_item=news_item,
                article_data=article,
                override_query=current_query
            )

            # Strict Chief Editor Review Gate
            review = self.chief_editor.evaluate_article_and_image(
                headline=headline,
                category=category,
                summary=news_item.get("summary", ""),
                image_info=candidate_image_info
            )

            if review["approved"]:
                approved_image_info = candidate_image_info
                logger.info(f"[Chief Editor APPROVED] Image passed quality & zero-duplicate check: {approved_image_info['image_url'][:60]}")
                break
            else:
                logger.warning(
                    f"[Chief Editor REJECTED (Attempt {attempt}/{max_image_attempts})] "
                    f"Type: {review['rejection_type']} | Reason: {review['rejection_reason']} "
                    f"-> Bouncing back to Graphics Agent with query: '{review['suggested_query']}'"
                )
                current_query = review.get("suggested_query")

        if not approved_image_info or not approved_image_info.get("image_url"):
            logger.error(f"[Chief Editor VETO] Publishing aborted for '{headline}'. No unique, relevant image approved after {max_image_attempts} attempts.")
            return False

        # 4. Publish to Blogger only after Chief Editor's formal approval
        logger.info(f"Publishing to Blogger ({BLOG_NAME} - Blog ID: {BLOG_ID})...")
        try:
            res = self.publisher.publish_news(
                article=article,
                image_info=approved_image_info,
                source_title=raw_title
            )
            # Register in Chief Editor's live published cache
            self.chief_editor.register_published_image(approved_image_info["image_url"])
            print(f"\n[✓] সফলভাবে প্রকাশিত হয়েছে [{category}]: {headline}")
            print(f"    URL: {res.get('url')}")
            print(f"    ছবি: {approved_image_info.get('credit')}\n", flush=True)
            return True
        except Exception as e:
            logger.error(f"Failed to publish to Blogger: {e}")
            return False

    def run_cloud_cycle(self, posts_per_cycle: int = 2) -> int:
        """
        Runs one cycle optimized for Cloud Automation (GitHub Actions / Scheduled Jobs):
        - Daily Limit Friendly: 2 posts per hour * 24 hours = 48 posts/day (strictly under Blogger's 50 limit).
        - Sports Prioritized: Post 1 is ALWAYS sports (খেলা).
        - Rotating Diversity: Post 2 rotates through national, politics, economy, international, tech, entertainment.
        - Live Duplicate Protection: Fetches recent Blogger titles so fresh cloud runs never duplicate.
        """
        print(f"\n[*] Starting Cloud Cycle (Target: {posts_per_cycle} posts)...", flush=True)
        live_titles = self.publisher.get_recent_published_titles(limit=50)
        logger.info(f"Retrieved {len(live_titles)} recent titles from Blogger for live duplicate protection.")

        published = 0

        # Post 1: Always prioritize Sports (খেলা)
        print("\n[1/2] Scouting and publishing prioritized Sports story...", flush=True)
        if self.process_section_story("খেলা", excluded_titles=live_titles):
            published += 1
            time.sleep(10)

        # Post 2: Pick next non-sports section (rotating based on hour of day)
        hour = datetime.utcnow().hour
        other_sections = [s for s in SECTIONS if s != "খেলা"]
        target_section = other_sections[hour % len(other_sections)]
        print(f"\n[2/2] Scouting and publishing section story: [{target_section}]...", flush=True)
        if self.process_section_story(target_section, excluded_titles=live_titles):
            published += 1

        print(f"\n[✓] Cloud Cycle complete. Published {published}/{posts_per_cycle} posts.", flush=True)

        # Evening Editorial (15:00 UTC = 21:00 / 9 PM Bangladesh Time)
        if datetime.utcnow().hour == 15:
            print("\n[*] Evening Flagship Editorial Hour -> Crafting Op-Ed (মতামত)...", flush=True)
            try:
                self.editorial_agent.publish_daily_editorial()
                published += 1
            except Exception as e:
                logger.error(f"Error publishing daily editorial in cloud cycle: {e}")

        return published

    def run_hourly_multi_section_cycle(self):
        """Publishes 1 article for each major section in the portal."""
        print("\n" + "#" * 65, flush=True)
        print(f"  [HOURLY CYCLE STARTED] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        print(f"  Target: 1 Post Per Section ({len(SECTIONS)} Sections)", flush=True)
        print("#" * 65 + "\n", flush=True)

        published_count = 0
        for idx, section in enumerate(SECTIONS, 1):
            print(f"[{idx}/{len(SECTIONS)}] Processing Section: {section}...", flush=True)
            success = self.process_section_story(section)
            if success:
                published_count += 1
            # 10-second politeness gap between section publications
            time.sleep(10)

        print(f"\n[✓] Hourly Cycle Finished. Published {published_count}/{len(SECTIONS)} sections.", flush=True)
        return published_count

    def run_schedule(self, interval_minutes: int = HOURLY_CYCLE_MINUTES):
        """Runs continuous 24/7 scheduler: 1 post per section every hour."""
        print("\n" + "=" * 70, flush=True)
        print(f"  {BLOG_NAME} -- 24/7 AUTONOMOUS NEWS ENGINE ACTIVE", flush=True)
        print(f"  Mode: 1 Post Per Section Every {interval_minutes} Minutes", flush=True)
        print(f"  Target Blog: {BLOG_NAME} ({BLOG_URL})", flush=True)
        print("=" * 70 + "\n", flush=True)

        while True:
            try:
                self.run_hourly_multi_section_cycle()
                # Evening Editorial Check (between 21:00 and 22:00 local time)
                if datetime.now().hour == 21:
                    print("\n[*] Evening Hour (21:00) -> Publishing Daily Editorial Opinion...", flush=True)
                    self.editorial_agent.publish_daily_editorial()
            except Exception as e:
                logger.error(f"Error during hourly cycle: {e}")

            print(f"\n[*] Cycle complete. Next hourly cycle in {interval_minutes} minutes...", flush=True)
            time.sleep(interval_minutes * 60)


def main():
    parser = argparse.ArgumentParser(description="Autonomous Bangladesh News Engine")
    parser.add_argument("--single-section", type=str, default="", help="Publish 1 story for a specific section")
    parser.add_argument("--daily-editorial", action="store_true", help="Synthesize all stories today and publish flagship Editorial Op-Ed (মতামত)")
    parser.add_argument("--cloud-cycle", action="store_true", help="Run 1 Cloud Cycle (2 posts: 1 Sports + 1 Rotating section)")
    parser.add_argument("--run-cycle", action="store_true", help="Run 1 full multi-section cycle right now")
    parser.add_argument("--schedule", action="store_true", help="Run 24/7 continuous hourly scheduler")
    parser.add_argument("--interval", type=int, default=HOURLY_CYCLE_MINUTES, help="Interval in minutes (default 60)")
    args = parser.parse_args()

    engine = BDNewsEngine()

    if args.single_section:
        engine.process_section_story(args.single_section)
    elif args.daily_editorial:
        engine.publish_daily_editorial()
    elif args.cloud_cycle:
        engine.run_cloud_cycle()
    elif args.run_cycle:
        engine.run_hourly_multi_section_cycle()
    elif args.schedule:
        engine.run_schedule(args.interval)
    else:
        # Default behavior: run 1 full cycle now
        engine.run_hourly_multi_section_cycle()


if __name__ == "__main__":
    main()
