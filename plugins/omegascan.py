from typing import List, AsyncIterable
from urllib.parse import urljoin, quote_plus
import re
import aiohttp
from bs4 import BeautifulSoup
from plugins.client import MangaClient, MangaCard, MangaChapter, LastChapter


class OmegaScansClient(MangaClient):

    base_url = "https://omegascans.org/"
    search_url = f"{base_url}?s="
    updates_url = base_url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0"
    }

    def __init__(self, *args, name="OmegaScans", **kwargs):
        super().__init__(*args, name=name, headers=self.headers, **kwargs)

    async def fetch_page(self, url: str) -> bytes:
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(url) as response:
                return await response.read()

    def mangas_from_page(self, page: bytes):
        soup = BeautifulSoup(page, "html.parser")
        container = soup.find_all("div", class_="bsx")

        mangas = []
        for item in container:
            link_tag = item.find("a")
            if not link_tag:
                continue
            name = link_tag.get("title")
            url = link_tag.get("href")
            image = item.find("img").get("src")

            mangas.append(MangaCard(self, name, url, image))

        return mangas

    def chapters_from_page(self, page: bytes, manga: MangaCard = None):
        soup = BeautifulSoup(page, "html.parser")
        container = soup.find("div", class_="eplister")

        if not container:
            return []

        items = container.find_all("a")
        links = [item.get("href") for item in items]
        titles = [item.text.strip() for item in items]

        return [MangaChapter(self, title, link, manga, []) for title, link in zip(titles, links)]

    async def search(self, query: str = "", page: int = 1) -> List[MangaCard]:
        search_query = quote_plus(query)
        request_url = f"{self.search_url}{search_query}&post_type=wp-manga"

        content = await self.fetch_page(request_url)
        return self.mangas_from_page(content)

    async def get_chapters(self, manga_card: MangaCard, page: int = 1) -> List[MangaChapter]:
        request_url = manga_card.url
        content = await self.fetch_page(request_url)

        return self.chapters_from_page(content, manga_card)

    async def iter_chapters(self, manga_url: str, manga_name) -> AsyncIterable[MangaChapter]:
        manga_card = MangaCard(self, manga_name, manga_url, "")
        content = await self.fetch_page(manga_card.url)

        for chapter in self.chapters_from_page(content, manga_card):
            yield chapter

    async def pictures_from_chapters(self, content: bytes, response=None):
        soup = BeautifulSoup(content, "html.parser")
        images = soup.find_all("img", class_="wp-manga-chapter-img")

        return [img.get("src") for img in images]

    async def check_updated_urls(self, last_chapters: List[LastChapter]):
        page = await self.fetch_page(self.updates_url)
        soup = BeautifulSoup(page, "html.parser")
        manga_items = soup.find_all("div", class_="bsx")

        updated = []
        not_updated = []
        urls = {}

        for item in manga_items:
            manga_url = item.find("a").get("href")
            chapter_url = item.find("a", class_="chapter").get("href") if item.find("a", class_="chapter") else None

            if manga_url and chapter_url:
                urls[manga_url] = chapter_url

        for lc in last_chapters:
            if lc.url in urls and urls[lc.url] != lc.chapter_url:
                updated.append(lc.url)
            elif urls.get(lc.url) == lc.chapter_url:
                not_updated.append(lc.url)

        return updated, not_updated
