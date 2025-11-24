"""Web scraping utilities using Playwright and BeautifulSoup."""

import asyncio
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
import aiohttp
import logging
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import config

logger = logging.getLogger(__name__)


class WebScraper:
    """Web scraper with multiple extraction strategies."""
    
    def __init__(self, timeout: int = None):
        self.timeout = timeout or config.TIMEOUT_SECONDS
        
    async def fetch_with_requests(self, url: str) -> Optional[str]:
        """
        Fetch page content using aiohttp (fast, no JS).
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                ) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return None
                        
        except Exception as e:
            logger.error(f"Request fetch error for {url}: {e}")
            return None
            
    async def fetch_with_playwright(self, url: str) -> Optional[str]:
        """
        Fetch page content using Playwright (handles JS).
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None
        """
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                await page.goto(url, timeout=self.timeout * 1000)
                await page.wait_for_load_state('networkidle', timeout=self.timeout * 1000)
                
                content = await page.content()
                await browser.close()
                
                return content
                
        except PlaywrightTimeout:
            logger.warning(f"Playwright timeout for {url}")
            return None
        except Exception as e:
            logger.error(f"Playwright fetch error for {url}: {e}")
            return None
            
    async def scrape(self, url: str, use_playwright: bool = False) -> Optional[Dict[str, Any]]:
        """
        Scrape a webpage and extract content.
        
        Args:
            url: URL to scrape
            use_playwright: Use Playwright for JS-heavy sites
            
        Returns:
            Dictionary with extracted content
        """
        logger.info(f"Scraping: {url}")
        
        # Fetch HTML
        if use_playwright:
            html = await self.fetch_with_playwright(url)
        else:
            html = await self.fetch_with_requests(url)
            
        if not html:
            return None
            
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html, 'lxml')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        # Extract metadata
        title = soup.title.string if soup.title else ""
        
        meta_desc = soup.find("meta", attrs={"name": "description"})
        description = meta_desc.get("content", "") if meta_desc else ""
        
        # Extract main content
        article = soup.find("article") or soup.find("main") or soup.find("body")
        
        if article:
            # Get text content
            paragraphs = article.find_all("p")
            text_content = "\n\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            
            # Get headings
            headings = []
            for h in article.find_all(["h1", "h2", "h3"]):
                headings.append({
                    "level": h.name,
                    "text": h.get_text(strip=True)
                })
        else:
            text_content = soup.get_text(separator="\n", strip=True)
            headings = []
            
        # Extract links
        links = []
        for link in soup.find_all("a", href=True):
            href = link.get("href", "")
            link_text = link.get_text(strip=True)
            if href and link_text and href.startswith("http"):
                links.append({"text": link_text, "url": href})
                
        result = {
            "url": url,
            "title": title.strip(),
            "description": description.strip(),
            "content": text_content[:10000],  # Limit content size
            "headings": headings[:20],
            "links": links[:50],
            "success": True
        }
        
        logger.info(f"Scraped {len(text_content)} chars from {url}")
        return result


async def scrape_url(url: str, use_playwright: bool = False) -> Optional[Dict[str, Any]]:
    """
    Convenience function to scrape a single URL.
    
    Args:
        url: URL to scrape
        use_playwright: Use Playwright for JS rendering
        
    Returns:
        Scraped content dictionary
    """
    scraper = WebScraper()
    return await scraper.scrape(url, use_playwright)


async def scrape_multiple(urls: list, use_playwright: bool = False) -> list:
    """
    Scrape multiple URLs in parallel.
    
    Args:
        urls: List of URLs to scrape
        use_playwright: Use Playwright for JS rendering
        
    Returns:
        List of scraped content dictionaries
    """
    scraper = WebScraper()
    tasks = [scraper.scrape(url, use_playwright) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out errors and None values
    return [r for r in results if isinstance(r, dict) and r is not None]
