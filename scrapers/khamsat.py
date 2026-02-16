import os
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from scrapers.base import BaseScraper
from domain.job import Job

BASE_URL = "https://khamsat.com"
REQUESTS_URL = "https://khamsat.com/community/requests"

MAX_PAGES = int(os.getenv("KHAMSAT_MAX_PAGES", 15))
MAX_ITEMS_PER_RUN = int(os.getenv("MAX_ITEMS_PER_RUN", 20))

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "ar,en;q=0.9",
}

KEYWORDS = [
    "ترجمة", "مترجم", "translate", "translation",
    "تفريغ", "transcription", "نسخ صوت", "تحويل صوت", "ملفات صوتية", "تفريغ فيديو",
    "تعليق صوتي", "voice over", "voice-over", "vo", "بودكاست", "podcast", "ناراتور",
    "python", "بايثون", "java", "جافا", "c++", "سكربت", "script", "بوت", "automation", "أتمتة", "api",
    "pdf", "word", "تحويل ملفات", "إعادة كتابة", "إعادة تنسيق", "تفريغ ملفات pdf",
    "ذكاء اصطناعي", "الذكاء الاصطناعي", "ai", "machine learning", "ml",
    "chatgpt", "gpt", "llm", "روبوت محادثة", "شات بوت", "chatbot",
    "توليد صور", "توليد محتوى", "prompt", "برمجة بوت", "openai"
]


class KhamsatScraper(BaseScraper):
    def __init__(self, proposal_service, telegram_client):
        super().__init__(proposal_service, telegram_client)

        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def scrape(self):
        """
        يرجّع قائمة domain.job.Job بدون Telegram ولا CSV.
        """
        jobs: list[Job] = []
        seen_links = set()

        for page_num in range(1, MAX_PAGES + 1):
            if len(jobs) >= MAX_ITEMS_PER_RUN:
                break

            url = REQUESTS_URL if page_num == 1 else f"{REQUESTS_URL}?page={page_num}"
            print(f"\n🌐 Fetching list page {page_num}: {url}")

            try:
                html = self._fetch(url)
            except Exception as e:
                print(f"❌ Error fetching list page {url}: {e}")
                break

            if not html:
                break

            parsed_jobs = self._parse_list(html)
            print(f"📋 Found {len(parsed_jobs)} jobs on this page")

            if not parsed_jobs:
                break

            for title, link in parsed_jobs:
                if len(jobs) >= MAX_ITEMS_PER_RUN:
                    break

                if link in seen_links:
                    continue
                seen_links.add(link)

                if not self._matches(title):
                    continue

                print(f"🔍 NEW relevant job: {title[:60]}...")
                self._sleep(1.5, 3.0)

                desc = self._fetch_description(link)
                jobs.append(Job(title, link, desc))

        if not jobs:
            print("ℹ️ No new jobs from Khamsat today.")

        return jobs

    def _fetch(self, url, max_retries=5):
        backoff = 3
        for attempt in range(1, max_retries + 1):
            try:
                print(f"[GET] {url} (attempt {attempt})")
                r = self.session.get(url, timeout=20)
                # تعامل مع 5xx بباك أوف بسيط
                if 500 <= r.status_code < 600:
                    if attempt < max_retries:
                        wait = backoff + random.uniform(0, 2)
                        print(f"[!] {r.status_code} from server, retry after {wait:.1f}s...")
                        time.sleep(wait)
                        backoff *= 2
                        continue
                    else:
                        print(f"[!] Server error {r.status_code} after {max_retries} attempts for {url}")
                        r.raise_for_status()

                r.raise_for_status()
                return r.text

            except requests.RequestException as e:
                if attempt < max_retries:
                    wait = backoff + random.uniform(0, 2)
                    print(f"[!] Network/HTTP error {e}, retry after {wait:.1f}s...")
                    time.sleep(wait)
                    backoff *= 2
                    continue
                print(f"[!] Failed after {max_retries} attempts for {url}: {e}")
                return ""

    def _parse_list(self, html):
        """
        يرجّع قائمة tuples (title, link) من صفحة الطلبات.
        """
        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select("tr.forum_post[id^='forum_post-']")
        jobs = []

        for row in rows:
            link_el = row.select_one("td.details-td h3.details-head a")
            if not link_el:
                continue

            title = (link_el.get_text(strip=True) or "").strip()
            href = link_el.get("href") or ""
            if not href:
                continue

            if href.startswith("/"):
                href = urljoin(BASE_URL, href)

            jobs.append((title, href))

        return jobs

    def _fetch_description(self, url):
        try:
            html = self._fetch(url)
            if not html:
                return ""
        except Exception as e:
            print(f"[!] Error fetching description from {url}: {e}")
            return ""

        soup = BeautifulSoup(html, "html.parser")

        # article.replace_urls
        article = soup.select_one("article.replace_urls")
        if article:
            text = article.get_text(" ", strip=True)
            if text:
                return text

        # fallbacks
        for sel in (".post-content", ".topic-content", ".description"):
            el = soup.select_one(sel)
            if el:
                text = el.get_text(" ", strip=True)
                if text:
                    return text

        return ""

    def _matches(self, text):
        t = text.lower()
        return any(kw.lower() in t for kw in KEYWORDS)

    def _sleep(self, min_s=2.0, max_s=4.0):
        time.sleep(random.uniform(min_s, max_s))
