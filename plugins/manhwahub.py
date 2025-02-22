from typing import List, AsyncIterable
from urllib.parse import urlparse, urljoin, quote, quote_plus
import re

from bs4 import BeautifulSoup
from bs4.element import PageElement

from plugins.client import MangaClient, MangaCard, MangaChapter, LastChapter


class ManhwahubClient(MangaClient):

    base_url = urlparse("https://manhwahub.net/")
    search_url = base_url.geturl()
    search_param = 'searchword'
    updates_url = base_url.geturl()

    pre_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0'
    }

    def __init__(self, *args, name="Manhwahub", **kwargs):
        super().__init__(*args, name=name, headers=self.pre_headers, **kwargs)

    def mangas_from_page(self, page: bytes):
        bs = BeautifulSoup(page, "html.parser")
        
        # Check if the container exists
        container = bs.find('div', {'class': 'listupd'})
        
        if container is None:
            print("No container found with class 'listupd'. Check if the page structure has changed.")
            return []  # Return an empty list if no container is found

        cards = container.find_all("div", {"class": "thumb-manga"})

        mangas = [card.findNext('a') for card in cards]
        names = [manga.get('title') for manga in mangas]
        url = [self.search_url + manga.get("href") for manga in mangas]
        images = [manga.findNext("img").get("src") for manga in mangas]

        return [MangaCard(self, *tup) for tup in zip(names, url, images)]
    
    def chapters_from_page(self, page: bytes, manga: MangaCard = None):
        bs = BeautifulSoup(page, "html.parser")
        
        container = bs.find("ul", {"class": "row-content-chapter"})
        
        if container is None:
            print("No container found for chapters. Check if the page structure has changed.")
            return []

        lis = container.find_all("li", {"class": "a-h"})
        
        items = [li.findNext('a') for li in lis]
        
        url = "https://manhwahub.net/"
        links = [url + item.get("href") for item in items]

        ch = [item.string.strip() for item in items]
        texts = ["C•" + re.search(r'Chapter (\d+)', title).group(1) for title in ch]

        return list(map(lambda x: MangaChapter(self, x[0], x[1], manga, []), zip(texts, links)))

    async def updates_from_page(self):
        page = await self.get_url(self.updates_url)
        
        bs = BeautifulSoup(page, "html.parser")

        manga_items = bs.find_all("h3", {"class": "tt mycover"})

        if not manga_items:
            print("No recent updates found. Check if the page structure has changed.")
            return {}

        urls = dict()

        for manga_item in manga_items:

            manga_url = urljoin(self.base_url.geturl(), manga_item.findNext("a").get("href"))

            if manga_url in urls:
                continue
        
            chapter_url = urljoin(self.base_url.geturl(), manga_item.findNext("a").findNext("a").get("href"))

            urls[manga_url] = chapter_url

        return urls

    async def pictures_from_chapters(self, content: bytes, response=None):
        bs = BeautifulSoup(content, "html.parser")
        
        cards = bs.findAll("div", {"class": "page-break"})
        
        if not cards:
            print("No pages found for pictures. Check if the page structure has changed.")
            return []

        images_url = [quote(containers.findNext("img").get("src"), safe=':/%') for containers in cards]
        
        return images_url

    async def search(self, query: str = "", page: int = 1) -> List[MangaCard]:
        query = quote_plus(query)

        request_url = self.search_url

        if query:
            request_url += f'/search?q={query}'

        content = await self.get_url(request_url)

        # Ensure valid content is returned before parsing
        if content is None:
            print("No content received from the search. Please check your request or website structure.")
            return []

        return self.mangas_from_page(content)

    async def get_chapters(self, manga_card: MangaCard, page: int = 1) -> List[MangaChapter]:
        request_url = f'{manga_card.url}'

        content = await self.get_url(request_url)

        # Ensure valid content is returned before parsing
        if content is None:
            print(f"No content found for {manga_card.url}. Please check the URL or the website.")
            return []

        return self.chapters_from_page(content, manga_card)[(page - 1) * 20:page * 20]

    async def iter_chapters(self, manga_url: str, manga_name) -> AsyncIterable[MangaChapter]:
        manga_card = MangaCard(self, manga_name, manga_url, '')

        request_url = f'{manga_card.url}'

        content = await self.get_url(request_url)

        if content is None:
            print(f"No content found for {manga_card.url}. Please check the URL or the website.")
            return

        for chapter in self.chapters_from_page(content, manga_card):
            yield chapter

    async def contains_url(self, url: str):
        return url.startswith(self.base_url.geturl())
            
    async def check_updated_urls(self, last_chapters: List[LastChapter]):
        updates = await self.updates_from_page()
        
        updated = []
        not_updated = []
        for lc in last_chapters:
            if lc.url in updates.keys():
                if updates.get(lc.url) != lc.chapter_url:
                    updated.append(lc.url)
            elif updates.get(lc.url) == lc.chapter_url:
                not_updated.append(lc.url)
                
        return updated, not_updated
