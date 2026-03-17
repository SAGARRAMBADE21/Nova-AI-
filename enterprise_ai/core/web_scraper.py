"""
core/web_scraper.py
Web Scraping Layer
Pipeline: URL → Scrape → Extract → Clean → Chunk → Embed
Rules: Public only | Respect robots.txt | TTL management
"""

import os
import logging
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT   = "EnterpriseAI-Scraper/1.0"


@dataclass
class ScrapedContent:
    url:       str
    title:     str
    content:   str
    timestamp: str
    source:    str = "web_scraping"
    score:     float = 0.6


class WebScraper:

    # ── Public interface ─────────────────────────────────────────────────

    def scrape(self, query: str, url: Optional[str] = None) -> list[ScrapedContent]:
        """
        Scrape content relevant to query.
        If URL is given — scrape directly.
        Otherwise extract URL from query, or search DuckDuckGo for the best result.
        """
        target_url = url or self._infer_url(query) or self._search_duckduckgo(query)
        if not target_url:
            logger.info("[WebScraper] No URL found and DuckDuckGo search returned nothing.")
            return []

        return self._scrape_url(target_url, query)

    # ── Core scraping pipeline ───────────────────────────────────────────

    def _scrape_url(self, url: str, query: str) -> list[ScrapedContent]:
        # 1. Check robots.txt
        if not self._is_allowed(url):
            logger.warning(f"[WebScraper] Blocked by robots.txt | url={url}")
            return []

        # 2. Scrape
        try:
            response = requests.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=10,
            )
            response.raise_for_status()
        except requests.exceptions.SSLError:
            # Fallback: retry without SSL verification (common on Windows)
            logger.warning(f"[WebScraper] SSL error, retrying without verification | url={url}")
            try:
                response = requests.get(
                    url,
                    headers={"User-Agent": USER_AGENT},
                    timeout=10,
                    verify=False,
                )
                response.raise_for_status()
            except requests.RequestException as e:
                logger.error(f"[WebScraper] Fetch error after SSL fallback | url={url} | error={e}")
                return []
        except requests.RequestException as e:
            logger.error(f"[WebScraper] Fetch error | url={url} | error={e}")
            return []

        # 3. Extract
        soup    = BeautifulSoup(response.text, "html.parser")
        title   = soup.title.string if (soup.title and soup.title.string) else url
        # Remove script/style tags
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text    = soup.get_text(separator="\n", strip=True)

        # 4. Clean
        lines   = [l.strip() for l in text.splitlines() if len(l.strip()) > 40]
        content = "\n".join(lines[:100])  # Limit to 100 lines

        # 5. Chunk
        chunks  = self._chunk(content, url, title)

        logger.info(f"[WebScraper] Scraped {len(chunks)} chunks | url={url}")
        return chunks

    def _chunk(self, content: str, url: str, title: str,
               chunk_size: int = 500) -> list[ScrapedContent]:
        timestamp = str(int(time.time()))
        words     = content.split()
        chunks    = []
        for i in range(0, len(words), chunk_size):
            chunk_text = " ".join(words[i:i + chunk_size])
            chunks.append(ScrapedContent(
                url       = url,
                title     = title,
                content   = chunk_text,
                timestamp = timestamp,
                source    = f"web:{urlparse(url).netloc}",
            ))
        return chunks

    def _is_allowed(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            return rp.can_fetch(USER_AGENT, url)
        except Exception:
            return True  # Allow if robots.txt is inaccessible

    def _infer_url(self, query: str) -> Optional[str]:
        """Detect if query contains a URL."""
        import re
        urls = re.findall(r'https?://[^\s]+', query)
        return urls[0] if urls else None

    def _search_duckduckgo(self, query: str) -> Optional[str]:
        """
        Search DuckDuckGo Lite and return the first result URL.
        Uses the HTML scraping approach (no API key required).
        """
        try:
            search_url = "https://lite.duckduckgo.com/lite/"
            response = requests.post(
                search_url,
                data={"q": query, "kl": "us-en"},
                headers={
                    "User-Agent": USER_AGENT,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                timeout=8,
                verify=False,
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            # DuckDuckGo Lite result links are <a class="result-link"> or plain <a> with href starting http
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if href.startswith("http") and "duckduckgo.com" not in href:
                    logger.info(f"[WebScraper] DuckDuckGo top result: {href}")
                    return href
        except Exception as e:
            logger.warning(f"[WebScraper] DuckDuckGo search failed: {e}")
        return None
