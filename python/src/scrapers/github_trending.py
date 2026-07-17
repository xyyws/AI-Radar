"""GitHub Trending 爬虫"""

from __future__ import annotations

from datetime import datetime, timezone

from bs4 import BeautifulSoup

from python.src.models.raw_intelligence import Language, RawIntelligence, Source
from python.src.scrapers.base import ScraperInterface

TRENDING_URL = "https://github.com/trending?since=daily"


class GitHubTrendingScraper(ScraperInterface):
    source = Source.GITHUB

    async def scrape(self) -> list[RawIntelligence]:
        resp = await self._client.get(TRENDING_URL)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        items: list[RawIntelligence] = []
        for row in soup.select("article.Box-row"):
            title_tag = row.select_one("h2 a")
            if not title_tag:
                continue

            repo_path = title_tag.get("href", "").strip("/")
            title = repo_path.replace("/", " / ")
            url = f"https://github.com/{repo_path}"

            desc_tag = row.select_one("p")
            description = desc_tag.get_text(strip=True) if desc_tag else ""

            lang_tag = row.select_one("[itemprop='programmingLanguage']")
            stars_tag = row.select_one("span.d-inline-block.float-sm-right")
            today_stars = ""
            if stars_tag:
                today_stars = stars_tag.get_text(strip=True)

            raw_content = f"Repository: {repo_path}\n"
            if description:
                raw_content += f"Description: {description}\n"
            if lang_tag:
                raw_content += f"Language: {lang_tag.get_text(strip=True)}\n"
            if today_stars:
                raw_content += f"Today: {today_stars}\n"

            evidence = []
            if today_stars:
                evidence.append(f"今日 star: {today_stars}")
            if description:
                evidence.append(f"简介: {description[:100]}")
            if lang_tag:
                evidence.append(f"语言: {lang_tag.get_text(strip=True)}")

            items.append(RawIntelligence(
                source=self.source,
                title=f"GitHub Trending: {title}",
                url=url,
                rawContent=raw_content,
                publishedAt=datetime.now(timezone.utc).isoformat(),
                language=Language.EN,
                metadata={"repo": repo_path, "today_stars": today_stars},
                evidence=evidence,
            ))

        return items
