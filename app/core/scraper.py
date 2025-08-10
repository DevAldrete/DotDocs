"""Scrapy spider integration for multi-page doc crawling.

Usage (programmatic):
  from app.core.scraper import crawl_urls
  asyncio.run(crawl_urls(["https://example.com/docs"], max_pages=20))

For now we keep it simple: same-domain links within allowed path prefix.
"""
from __future__ import annotations

import asyncio
from typing import List, Set
from urllib.parse import urljoin, urlparse

from scrapy.crawler import CrawlerProcess
from scrapy import Spider, Request
from scrapy.linkextractors import LinkExtractor

from app.core.ingest import ingest_url


class DocsSpider(Spider):
    name = "dotdocs_spider"

    custom_settings = {
        "LOG_ENABLED": False,
        "DOWNLOAD_TIMEOUT": 30,
    }

    def __init__(self, start_urls: List[str], max_pages: int = 50, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = start_urls
        self.max_pages = max_pages
        self.seen: Set[str] = set()
        self.allowed_netloc = urlparse(start_urls[0]).netloc
        self.collected: List[str] = []
        self.extractor = LinkExtractor(allow_domains=[self.allowed_netloc])

    def parse(self, response):
        url = response.url
        if url in self.seen:
            return
        self.seen.add(url)
        self.collected.append(url)
        if len(self.collected) >= self.max_pages:
            return
        for link in self.extractor.extract_links(response):
            if link.url not in self.seen and urlparse(link.url).netloc == self.allowed_netloc:
                yield Request(link.url, callback=self.parse)


async def crawl_and_ingest(start_url: str, max_pages: int = 30) -> List[str]:
    # Run Scrapy in thread to not block event loop
    loop = asyncio.get_running_loop()
    collected: List[str] = []

    def _run():
        process = CrawlerProcess()
        spider = DocsSpider(start_urls=[start_url], max_pages=max_pages)
        process.crawl(spider)
        process.start()
        collected.extend(spider.collected)

    await loop.run_in_executor(None, _run)
    # Ingest sequentially (could be parallelized later)
    for u in collected:
        try:
            await ingest_url(u, reingest=True)
        except Exception:
            continue
    return collected
