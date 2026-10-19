"""
Creates professional E-E-A-T and Trust Pages on Blogger for Google Discover and Google Search.
Required pages:
1. আমাদের সম্পর্কে (About Us)
2. সম্পাদকীয় ও তথ্য যাচাই নীতিমালা (Editorial & Fact-Checking Policy)
3. যোগাযোগ ও সম্পাদকীয় কার্যালয় (Contact Us)
4. গোপনীয়তা নীতি ও ব্যবহারের শর্তাবলী (Privacy Policy)
"""
import json
import logging
import sys
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import BLOG_ID, BLOG_NAME, BLOG_URL, TOKEN_FILE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("TrustPages")

PAGES = [
    {
        "title": "আমাদের সম্পর্কে",
        "content": f"""
        <div class="pa-trust-page" style="font-family: 'SolaimanLipi', 'Noto Sans Bengali', sans-serif; line-height: 1.85; color: #222; font-size: 17px; max-width: 820px; margin: 0 auto; padding: 20px 0;">
            <h1 style="color: #b71c1c; font-size: 2.2rem; font-weight: 800; border-bottom: 3px solid #d32f2f; padding-bottom: 12px; margin-bottom: 24px;">আমাদের সম্পর্কে — {BLOG_NAME}</h1>
            
            <p><strong>{BLOG_NAME}</strong> বাংলাদেশের একটি অগ্রণী, স্বাধীন ও ২৪ ঘণ্টা লাইভ ডিজিটাল জাতীয় সংবাদমাধ্যম। আমাদের মূল লক্ষ্য হলো গণমানুষের কাছে বস্তুনিষ্ঠ, নির্মোহ ও দ্রুততম সময়ে তথ্য পৌঁছে দেওয়া। কোনো রাজনৈতিক বা করপোরেট প্রভাব ছাড়াই নির্ভীক সাংবাদিকতা পরিচালনা করাই আমাদের প্রধান ব্রত।</p>
            
            <h2 style="color: #1e293b; font-size: 1.45rem; font-weight: 700; margin-top: 28px;">আমাদের মিশন ও লক্ষ্য</h2>
            <ul style="padding-left: 22px; margin-top: 10px;">
                <li><strong>সত্যের অনুসন্ধান:</strong> প্রতিটি সংবাদের সত্যতা ও নিরপেক্ষতা যাচাই করে প্রকাশ করা।</li>
                <li><strong>সার্বক্ষণিক লাইভ আপডেট:</strong> জাতীয়, আন্তর্জাতিক, অর্থনীতি, রাজনীতি, প্রযুক্তি ও খেলাধুলার সর্বশেষ তথ্য সবার আগে পাঠকদের সামনে তুলে ধরা।</li>
                <li><strong>বাংলাদেশি ক্রীড়াঙ্গনের প্রসার:</strong> বিশেষ করে বাংলাদেশ ক্রিকেট, ফুটবল ও আন্তর্জাতিক ক্রীড়াঙ্গনের খবরকে সর্বোচ্চ অগ্রাধিকার প্রদান।</li>
                <li><strong>প্রমিত বাংলা ও আধুনিক সাংবাদিকতা:</strong> প্রাতিষ্ঠানিক সাংবাদিকতার মানদণ্ডে দৃষ্টিনন্দন ও তথ্যবহুল প্রতিবেদন পরিবেশন।</li>
            </ul>

            <h2 style="color: #1e293b; font-size: 1.45rem; font-weight: 700; margin-top: 28px;">সম্পাদকীয় কাঠামো</h2>
            <p>{BLOG_NAME}-এর সংবাদকক্ষ পরিচালিত হয় অভিজ্ঞ সাংবাদিক, তথ্য বিশ্লেষক এবং অনলাইন বার্তা সম্পাদকের সমন্বয়ে গঠিত একটি নিষ্ঠাবান দলের মাধ্যমে। প্রতিটি প্রতিবেদন প্রকাশের পূর্বে অন্তত দুটি নির্ভরযোগ্য সরকারি বা প্রাতিষ্ঠানিক সূত্রের মাধ্যমে যাচাই করা হয়।</p>
            
            <div style="background: #f1f5f9; padding: 18px 24px; border-radius: 8px; border-left: 4px solid #0284c7; margin-top: 30px;">
                <h3 style="margin: 0 0 8px; color: #0f172a; font-size: 1.15rem;">প্রকাশনা তথ্য</h3>
                <p style="margin: 0; font-size: 0.95rem; color: #475569;">
                    <strong>প্রধান কার্যালয়:</strong> কারওয়ান বাজার, ঢাকা-১২১৫, বাংলাদেশ<br/>
                    <strong>ইমেইল:</strong> fairpolyharunrashid@gmail.com<br/>
                    <strong>অনলাইন সংস্করণ:</strong> <a href="{BLOG_URL}">{BLOG_URL}</a>
                </p>
            </div>
        </div>
        """
    },
    {
        "title": "সম্পাদকীয় ও তথ্য যাচাই নীতিমালা",
        "content": f"""
        <div class="pa-trust-page" style="font-family: 'SolaimanLipi', 'Noto Sans Bengali', sans-serif; line-height: 1.85; color: #222; font-size: 17px; max-width: 820px; margin: 0 auto; padding: 20px 0;">
            <h1 style="color: #b71c1c; font-size: 2.2rem; font-weight: 800; border-bottom: 3px solid #d32f2f; padding-bottom: 12px; margin-bottom: 24px;">সম্পাদকীয় ও তথ্য যাচাই (Fact-Checking) নীতিমালা</h1>
            
            <p><strong>{BLOG_NAME}</strong> বস্তুনিষ্ঠ, স্বচ্ছ ও দায়বদ্ধ সাংবাদিকতায় অঙ্গীকারবদ্ধ। আমরা বিশ্বাস করি সংবাদের সঠিকতা ও নির্ভুলতাই গণমাধ্যমের প্রধান শক্তি।</p>
            
            <h2 style="color: #1e293b; font-size: 1.45rem; font-weight: 700; margin-top: 28px;">১. তথ্য যাচাইকরণ প্রক্রিয়া (Fact-Checking Standard)</h2>
            <ul style="padding-left: 22px;">
                <li>যেকোনো সংবেদনশীল খবর বা জাতীয় ইস্যুর ক্ষেত্রে প্রত্যক্ষদর্শী, সরকারি প্রেস বিজ্ঞপ্তি বা দায়িত্বশীল প্রতিনিধির সরাসরি বক্তব্যের ওপর ভিত্তি করে সংবাদ লেখা হয়।</li>
                <li>সামাজিক যোগাযোগমাধ্যমের কোনো খবর যাচাই ব্যতীত সরাসরি প্রকাশ করা সম্পূর্ণ নিষিদ্ধ।</li>
                <li>সংবাদের ক্ষেত্রে ক্লাসিক্যাল <strong>5W1H (Who, What, Where, When, Why, How)</strong> কাঠামো কঠোরভাবে অনুসরণ করা হয়।</li>
            </ul>

            <h2 style="color: #1e293b; font-size: 1.45rem; font-weight: 700; margin-top: 28px;">২. উৎস ও ছবির সত্যতা (Source & Image Credit)</h2>
            <ul style="padding-left: 22px;">
                <li>প্রতিটি প্রকাশিত ছবির সাথে যথাযথ আলোকচিত্রী, আন্তর্জাতিক বা জাতীয় সংবাদ সংস্থার স্পষ্ট ক্রেডিট (যেমন: প্রথম আলো, রয়টার্স, বিসিবি বা নিজস্ব প্রতিনিধি) উল্লেখ করা বাধ্যতামূলক।</li>
                <li>ভ্রান্ত বা বিকৃত কোনো ছবি দিয়ে ক্লিকবেট সংবাদ পরিবেশন করা আমাদের নীতিমালার পরিপন্থী।</li>
            </ul>

            <h2 style="color: #1e293b; font-size: 1.45rem; font-weight: 700; margin-top: 28px;">৩. ভুল সংশোধন নীতিমালা (Corrections Policy)</h2>
            <p>অনিচ্ছাকৃত কোনো ভুল তথ্য বা ত্রুটি দৃষ্টিগোচর হলে আমরা দ্রুততম সময়ে সংশোধনী (Correction Note) সহ সংবাদটি পরিমার্জন করি এবং পাঠকদের কাছে স্বচ্ছতা বজায় রাখি। কোনো সংবাদের তথ্যে ভুল থাকলে সরাসরি আমাদের বার্তা বিভাগে যোগাযোগ করার অনুরোধ রইল।</p>
        </div>
        """
    },
    {
        "title": "যোগাযোগ ও সম্পাদকীয় কার্যালয়",
        "content": f"""
        <div class="pa-trust-page" style="font-family: 'SolaimanLipi', 'Noto Sans Bengali', sans-serif; line-height: 1.85; color: #222; font-size: 17px; max-width: 820px; margin: 0 auto; padding: 20px 0;">
            <h1 style="color: #b71c1c; font-size: 2.2rem; font-weight: 800; border-bottom: 3px solid #d32f2f; padding-bottom: 12px; margin-bottom: 24px;">যোগাযোগ ও সম্পাদকীয় কার্যালয়</h1>
            
            <p>যে কোনো তথ্য, সংবাদ প্রেরন, মতামত বা অনুসন্ধানী প্রতিবেদনের তথ্যের জন্য আমাদের সম্পাদকীয় টিমের সাথে নির্দ্বিধায় যোগাযোগ করুন।</p>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 20px; margin: 30px 0;">
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 20px; border-radius: 8px;">
                    <h3 style="margin-top: 0; color: #d32f2f;">📍 প্রধান কার্যালয়</h3>
                    <p style="color: #475569; font-size: 0.95rem;">
                        <strong>{BLOG_NAME}</strong><br/>
                        লেভেল ৪, মিডিয়া প্লাজা, কারওয়ান বাজার<br/>
                        ঢাকা-১২১৫, বাংলাদেশ
                    </p>
                </div>
                
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 20px; border-radius: 8px;">
                    <h3 style="margin-top: 0; color: #d32f2f;">✉️ বার্তা বিভাগ (ইমেইল)</h3>
                    <p style="color: #475569; font-size: 0.95rem;">
                        সাধারণ যোগাযোগ ও সম্পাদকীয়:<br/>
                        <a href="mailto:fairpolyharunrashid@gmail.com" style="color: #0284c7; font-weight: 600;">fairpolyharunrashid@gmail.com</a><br/>
                        বিজ্ঞাপন ও বাণিজ্যিক তথ্য: info@provatikhobor24.com
                    </p>
                </div>
            </div>

            <h2 style="color: #1e293b; font-size: 1.45rem; font-weight: 700; margin-top: 28px;">সংবাদ বা তথ্য জানাতে</h2>
            <p>আপনার এলাকার কোনো অনিয়ম, ব্রেকিং নিউজ বা বিশেষ প্রতিবেদন পাঠাতে তথ্য ও প্রামাণ্য ছবি সহ আমাদের ইমেইল ঠিকানায় পাঠান। আমাদের বার্তা বিভাগ অবিলম্বে তা যাচাই করে প্রয়োজনীয় ব্যবস্থা গ্রহণ করবে।</p>
        </div>
        """
    },
    {
        "title": "গোপনীয়তা নীতি",
        "content": f"""
        <div class="pa-trust-page" style="font-family: 'SolaimanLipi', 'Noto Sans Bengali', sans-serif; line-height: 1.85; color: #222; font-size: 17px; max-width: 820px; margin: 0 auto; padding: 20px 0;">
            <h1 style="color: #b71c1c; font-size: 2.2rem; font-weight: 800; border-bottom: 3px solid #d32f2f; padding-bottom: 12px; margin-bottom: 24px;">গোপনীয়তা নীতি ও ব্যবহারের শর্তাবলী (Privacy Policy)</h1>
            
            <p><strong>{BLOG_NAME}</strong> ({BLOG_URL}) পাঠকদের ব্যক্তিগত তথ্যের গোপনীয়তাকে সর্বোচ্চ গুরুত্ব দেয়। এই নীতিমালায় ব্যাখ্যা করা হয়েছে আমরা কীভাবে পাঠকদের তথ্য সংগ্রহ ও ব্যবহার করি।</p>
            
            <h2 style="color: #1e293b; font-size: 1.45rem; font-weight: 700; margin-top: 28px;">১. তথ্য সংগ্রহ ও কুকিজ</h2>
            <p>আমাদের ওয়েবসাইট ব্রাউজ করার সময় পাঠকদের ব্যক্তিগত কোনো তথ্য (নাম, পাসওয়ার্ড, ব্যাংক তথ্য) আমরা সংগ্রহ করি না। পাঠকদের পাঠাভ্যাস বিশ্লেষণ ও সাইটের মানোন্নয়নের জন্য গুগল অ্যানালিটিক্স ও স্ট্যান্ডার্ড কুকিজ (Cookies) প্রযুক্তি ব্যবহার করা হতে পারে।</p>

            <h2 style="color: #1e293b; font-size: 1.45rem; font-weight: 700; margin-top: 28px;">২. তৃতীয় পক্ষের লিংক</h2>
            <p>আমাদের সাইটের প্রতিবেদনে পাঠকদের রেফারেন্সের সুবিধার্থে বাহ্যিক কোনো ওয়েবসাইটের লিংক থাকতে পারে। তৃতীয় পক্ষের ওয়েবসাইটের গোপনীয়তা নীতির জন্য {BLOG_NAME} দায়বদ্ধ নয়।</p>

            <h2 style="color: #1e293b; font-size: 1.45rem; font-weight: 700; margin-top: 28px;">৩. কপিরাইট ও সর্বস্বত্ব</h2>
            <p>{BLOG_NAME}-এ প্রকাশিত কোনো লেখা বা সংবাদ অনুমতি ব্যতিরেকে হুবহু নকল বা অন্য কোনো মাধ্যমে বাণিজ্যিক উদ্দেশ্যে প্রকাশ করা আইনত দণ্ডনীয়। তবে যথাযথ ক্রেডিট ও মূল হাইপারলিংক যুক্ত করে সামাজিক মাধ্যমে শেয়ার করা যাবে।</p>
        </div>
        """
    }
]


def main():
    logger.info("Connecting to Blogger API to publish E-E-A-T Trust Pages...")
    with open(TOKEN_FILE, "r", encoding="utf-8") as f:
        creds_data = json.load(f)
    creds = Credentials.from_authorized_user_info(creds_data)
    service = build("blogger", "v3", credentials=creds)

    # Check existing pages to prevent duplicates
    existing_pages = service.pages().list(blogId=BLOG_ID).execute().get("items", [])
    existing_titles = {p["title"].strip(): p for p in existing_pages}

    page_urls = {}

    for p in PAGES:
        title = p["title"]
        content = p["content"].strip()
        
        if title in existing_titles:
            p_id = existing_titles[title]["id"]
            logger.info(f"Page '{title}' already exists (ID: {p_id}). Updating content...")
            res = service.pages().patch(
                blogId=BLOG_ID,
                pageId=p_id,
                body={"content": content}
            ).execute()
        else:
            logger.info(f"Creating new page '{title}'...")
            res = service.pages().insert(
                blogId=BLOG_ID,
                body={
                    "kind": "blogger#page",
                    "blog": {"id": BLOG_ID},
                    "title": title,
                    "content": content
                },
                isDraft=False
            ).execute()
        
        page_urls[title] = res.get("url")
        logger.info(f"  [✓] Page '{title}' active at: {res.get('url')}")

    print("\nAll Trust Pages active:\n" + json.dumps(page_urls, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
