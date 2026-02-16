import time
import random
import logging
from typing import Iterable

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from .base import BaseScraper
from domain.job import Job


logger = logging.getLogger(__name__)


BASE_URL = "https://mostaql.com"

CATEGORY_URLS = [
    "https://mostaql.com/projects/ai-machine-learning",
    "https://mostaql.com/projects/design",
    "https://mostaql.com/projects/writing-translation",
    "https://mostaql.com/projects/support",
    "https://mostaql.com/projects/development",
]

MAX_PAGES = 15
MAX_RETRIES = 5

KEYWORDS = [
    "تحويل pdf", "تحويل PDF", "pdf لنصوص",
    "ترجمة", "مترجم",
    "تعليق صوتى", "تعليق صوتي",
    "لغة عربية", "لغة انجليزية", "لغة إنجليزية",
    "ocr", "معالجة الصور",
    "ذكاء اصطناعي", "تعلم الآلة",
    "python", "بايثون",
    "web scraping", "scraping", "جمع البيانات",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "ar,en;q=0.9",
}


class MostaqlScraper(BaseScraper):
    """Scraper for mostaql.com projects pages."""

    def __init__(self, proposal_service, telegram_client):
        super().__init__(proposal_service, telegram_client)

        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    # =====================================================
    # public
    # =====================================================

    def scrape(self) -> list[Job]:

        jobs: list[Job] = []

        for category_url in CATEGORY_URLS:

            logger.info("Scraping category %s", category_url)

            for page in range(1, MAX_PAGES + 1):

                html = self._fetch_projects_page(category_url, page)

                if not html:
                    break

                projects = self._parse_projects(html)

                logger.info(
                    "Found %s projects on page %s",
                    len(projects),
                    page,
                )

                if not projects:
                    break

                for proj in projects:

                    if not self._matches_keywords(proj["title"]):
                        continue

                    description = self._fetch_project_description(
                        proj["project_url"]
                    )

                    jobs.append(
                        Job(
                            title=proj["title"],
                            url=proj["project_url"],
                            description=description,
                        )
                    )

                    self._sleep(2, 4)

                self._sleep(4, 7)

        return jobs

    # =====================================================
    # networking
    # =====================================================

    def _fetch_projects_page(
        self,
        base_url: str,
        page: int,
    ) -> str | None:

        params = {"page": page} if page > 1 else {}

        for attempt in range(1, MAX_RETRIES + 1):

            try:

                resp = self.session.get(
                    base_url,
                    params=params,
                    timeout=25,
                )

                if resp.status_code >= 500:
                    raise requests.HTTPError(
                        f"server error {resp.status_code}",
                        response=resp,
                    )

                resp.raise_for_status()
                return resp.text

            except Exception as exc:

                wait = self._backoff(attempt)

                logger.warning(
                    "Fetch failed (%s page=%s attempt=%s): %s",
                    base_url,
                    page,
                    attempt,
                    exc,
                )

                time.sleep(wait)

        return None

    def _fetch_project_description(
        self,
        project_url: str,
    ) -> str:

        for attempt in range(1, MAX_RETRIES + 1):

            try:

                resp = self.session.get(
                    project_url,
                    timeout=25,
                )

                resp.raise_for_status()

                soup = BeautifulSoup(resp.text, "html.parser")

                brief = soup.find("div", id="project-brief")
                if not brief:
                    return ""

                body = brief.find("div", class_="carda__body") or brief
                content = (
                    body.find("div", class_="text-wrapper-div")
                    or body
                )

                return content.get_text(
                    separator=" ",
                    strip=True,
                )

            except Exception as exc:

                wait = self._backoff(attempt)

                logger.warning(
                    "Project fetch failed (%s attempt=%s): %s",
                    project_url,
                    attempt,
                    exc,
                )

                time.sleep(wait)

        return ""

    # =====================================================
    # parsing
    # =====================================================

    def _parse_projects(self, html: str) -> list[dict]:

        soup = BeautifulSoup(html, "html.parser")

        cards = soup.find_all("div", class_="project-card")

        if not cards:
            cards = soup.select("h3 a, h2 a")

        projects: list[dict] = []

        for card in cards:

            link = card if card.name == "a" else card.find("a")
            if not link:
                continue

            title = (
                link.get("title")
                or link.get_text(strip=True)
                or ""
            ).strip()

            href = link.get("href", "").strip()

            if not title or not href:
                continue

            if not href.startswith("http"):
                href = urljoin(BASE_URL, href)

            if "/project/" not in href:
                continue

            projects.append(
                {
                    "title": title,
                    "project_url": href,
                }
            )

        return projects

    # =====================================================
    # helpers
    # =====================================================

    def _matches_keywords(self, text: str) -> bool:

        lowered = text.lower()
        return any(k.lower() in lowered for k in KEYWORDS)

    def _sleep(self, a: float, b: float):

        time.sleep(random.uniform(a, b))

    @staticmethod
    def _backoff(attempt: int) -> float:

        return (2 ** attempt) + random.uniform(0, 2)
