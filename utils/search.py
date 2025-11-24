"""Search utilities for web searching across multiple providers."""

import asyncio
import aiohttp
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
from ddgs import DDGS
import config

logger = logging.getLogger(__name__)


class SearchResult:
    """Represents a single search result."""
    
    def __init__(
        self,
        title: str,
        url: str,
        snippet: str,
        source: str = "unknown",
        date: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.source = source
        self.date = date or datetime.now().isoformat()
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "date": self.date,
            "metadata": self.metadata
        }


class SearchEngine:
    """Abstract search engine interface."""
    
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Perform search and return results."""
        raise NotImplementedError


class DuckDuckGoSearch(SearchEngine):
    """DuckDuckGo search implementation."""
    
    def __init__(self):
        self.ddgs = DDGS()
        
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Search using DuckDuckGo.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of SearchResult objects
        """
        try:
            logger.info(f"Searching DuckDuckGo: {query}")
            results = []
            
            # DuckDuckGo search is synchronous, so run in executor
            loop = asyncio.get_event_loop()
            ddg_results = await loop.run_in_executor(
                None,
                lambda: list(self.ddgs.text(query, max_results=max_results))
            )
            
            for result in ddg_results:
                search_result = SearchResult(
                    title=result.get("title", ""),
                    url=result.get("href", ""),
                    snippet=result.get("body", ""),
                    source="duckduckgo",
                    metadata=result
                )
                results.append(search_result)
                
            logger.info(f"Found {len(results)} results from DuckDuckGo")
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []


class SerpAPISearch(SearchEngine):
    """SerpAPI (Google) search implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.SERPAPI_KEY
        
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """
        Search using SerpAPI.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of SearchResult objects
        """
        if not self.api_key:
            logger.warning("SerpAPI key not configured")
            return []
            
        try:
            logger.info(f"Searching SerpAPI: {query}")
            
            url = "https://serpapi.com/search"
            params = {
                "q": query,
                "api_key": self.api_key,
                "num": max_results,
                "engine": "google"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=config.TIMEOUT_SECONDS) as response:
                    if response.status != 200:
                        logger.error(f"SerpAPI error: {response.status}")
                        return []
                        
                    data = await response.json()
                    
            results = []
            organic_results = data.get("organic_results", [])
            
            for result in organic_results[:max_results]:
                search_result = SearchResult(
                    title=result.get("title", ""),
                    url=result.get("link", ""),
                    snippet=result.get("snippet", ""),
                    source="serpapi",
                    date=result.get("date"),
                    metadata=result
                )
                results.append(search_result)
                
            logger.info(f"Found {len(results)} results from SerpAPI")
            return results
            
        except Exception as e:
            logger.error(f"SerpAPI search error: {e}")
            return []


class MultiSearch:
    """Aggregates results from multiple search engines."""
    
    def __init__(self):
        self.engines = [
            DuckDuckGoSearch(),
        ]
        
        # Add SerpAPI if key is configured
        if config.SERPAPI_KEY:
            self.engines.append(SerpAPISearch())
            
    async def search(
        self,
        query: str,
        max_results: int = 10,
        deduplicate: bool = True
    ) -> List[SearchResult]:
        """
        Search across multiple engines and aggregate results.
        
        Args:
            query: Search query
            max_results: Maximum total results
            deduplicate: Remove duplicate URLs
            
        Returns:
            Aggregated list of SearchResult objects
        """
        logger.info(f"Multi-search for: {query}")
        
        # Search all engines in parallel
        tasks = [
            engine.search(query, max_results)
            for engine in self.engines
        ]
        
        all_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten results
        combined = []
        for results in all_results:
            if isinstance(results, list):
                combined.extend(results)
            else:
                logger.error(f"Search error: {results}")
                
        # Deduplicate by URL
        if deduplicate:
            seen_urls = set()
            unique_results = []
            
            for result in combined:
                if result.url not in seen_urls:
                    seen_urls.add(result.url)
                    unique_results.append(result)
                    
            combined = unique_results
            
        # Limit to max_results
        combined = combined[:max_results]
        
        logger.info(f"Total unique results: {len(combined)}")
        return combined


async def search_web(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Convenience function to search the web.
    
    Args:
        query: Search query
        max_results: Maximum results
        
    Returns:
        List of search result dictionaries
    """
    multi_search = MultiSearch()
    results = await multi_search.search(query, max_results)
    return [r.to_dict() for r in results]
