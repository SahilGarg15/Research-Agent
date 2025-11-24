"""
Multi-Source Search Engine System
Supports Brave, Exa, DuckDuckGo, Wikipedia, SerpAPI, and Google CSE
with intelligent fallback and retry mechanisms.
"""

import asyncio
import aiohttp
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging
from ddgs import DDGS
import wikipediaapi

logger = logging.getLogger(__name__)


class SearchResult:
    """Unified search result format."""
    
    def __init__(
        self,
        title: str,
        url: str,
        snippet: str,
        source: str = "unknown",
        date: Optional[str] = None,
        relevance_score: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.source = source
        self.date = date or datetime.now().isoformat()
        self.relevance_score = relevance_score
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "date": self.date,
            "relevance_score": self.relevance_score,
            "metadata": self.metadata
        }


class BraveSearchEngine:
    """Brave Search API - 2,000 free requests/month."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("BRAVE_API_KEY")
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search using Brave API."""
        if not self.api_key:
            logger.warning("Brave API key not configured")
            return []
            
        try:
            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": self.api_key
            }
            
            params = {
                "q": query,
                "count": max_results
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url,
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        
                        for item in data.get("web", {}).get("results", [])[:max_results]:
                            results.append(SearchResult(
                                title=item.get("title", ""),
                                url=item.get("url", ""),
                                snippet=item.get("description", ""),
                                source="brave",
                                relevance_score=0.9
                            ))
                        
                        logger.info(f"Brave Search: Found {len(results)} results")
                        return results
                    else:
                        logger.error(f"Brave Search API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Brave Search failed: {e}")
            return []


class ExaSearchEngine:
    """Exa Search API - 1,000 free requests/month."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("EXA_API_KEY")
        self.base_url = "https://api.exa.ai/search"
        
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search using Exa API."""
        if not self.api_key:
            logger.warning("Exa API key not configured")
            return []
            
        try:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key
            }
            
            payload = {
                "query": query,
                "numResults": max_results,
                "type": "auto",
                "contents": {
                    "text": True
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        
                        for item in data.get("results", [])[:max_results]:
                            results.append(SearchResult(
                                title=item.get("title", ""),
                                url=item.get("url", ""),
                                snippet=item.get("text", "")[:500],
                                source="exa",
                                date=item.get("publishedDate"),
                                relevance_score=item.get("score", 0.8)
                            ))
                        
                        logger.info(f"Exa Search: Found {len(results)} results")
                        return results
                    else:
                        logger.error(f"Exa Search API error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Exa Search failed: {e}")
            return []


class DuckDuckGoSearchEngine:
    """DuckDuckGo Search - Free, unlimited."""
    
    def __init__(self):
        self.ddgs = DDGS()
        
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search using DuckDuckGo."""
        try:
            loop = asyncio.get_event_loop()
            ddg_results = await loop.run_in_executor(
                None,
                lambda: list(self.ddgs.text(query, max_results=max_results))
            )
            
            results = []
            for item in ddg_results[:max_results]:
                results.append(SearchResult(
                    title=item.get("title", ""),
                    url=item.get("href", ""),
                    snippet=item.get("body", ""),
                    source="duckduckgo",
                    relevance_score=0.7
                ))
            
            logger.info(f"DuckDuckGo: Found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo Search failed: {e}")
            return []


class WikipediaSearchEngine:
    """Wikipedia API - Free, unlimited."""
    
    def __init__(self):
        self.wiki = wikipediaapi.Wikipedia(
            user_agent='AutoResearchAgent/2.0 (Educational)',
            language='en'
        )
        
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """Search Wikipedia."""
        try:
            # Get page
            page = self.wiki.page(query)
            
            if page.exists():
                results = [SearchResult(
                    title=page.title,
                    url=page.fullurl,
                    snippet=page.summary[:500],
                    source="wikipedia",
                    relevance_score=0.85
                )]
                
                logger.info(f"Wikipedia: Found article for '{query}'")
                return results
            else:
                logger.info(f"Wikipedia: No article found for '{query}'")
                return []
                
        except Exception as e:
            logger.error(f"Wikipedia Search failed: {e}")
            return []


class SerpAPISearchEngine:
    """SerpAPI - Google Search (Premium)."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SERPAPI_KEY")
        self.base_url = "https://serpapi.com/search"
        
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search using SerpAPI."""
        if not self.api_key:
            logger.warning("SerpAPI key not configured")
            return []
            
        try:
            params = {
                "q": query,
                "num": max_results,
                "api_key": self.api_key,
                "engine": "google"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        
                        for item in data.get("organic_results", [])[:max_results]:
                            results.append(SearchResult(
                                title=item.get("title", ""),
                                url=item.get("link", ""),
                                snippet=item.get("snippet", ""),
                                source="serpapi",
                                relevance_score=0.95
                            ))
                        
                        logger.info(f"SerpAPI: Found {len(results)} results")
                        return results
                    else:
                        logger.error(f"SerpAPI error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"SerpAPI failed: {e}")
            return []


class GoogleCSESearchEngine:
    """Google Custom Search Engine (Premium)."""
    
    def __init__(self, api_key: Optional[str] = None, cx: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_CSE_API_KEY")
        self.cx = cx or os.getenv("GOOGLE_CSE_CX")
        self.base_url = "https://www.googleapis.com/customsearch/v1"
        
    async def search(self, query: str, max_results: int = 10) -> List[SearchResult]:
        """Search using Google CSE."""
        if not self.api_key or not self.cx:
            logger.warning("Google CSE not configured")
            return []
            
        try:
            params = {
                "q": query,
                "num": min(max_results, 10),
                "key": self.api_key,
                "cx": self.cx
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.base_url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = []
                        
                        for item in data.get("items", [])[:max_results]:
                            results.append(SearchResult(
                                title=item.get("title", ""),
                                url=item.get("link", ""),
                                snippet=item.get("snippet", ""),
                                source="google_cse",
                                relevance_score=0.95
                            ))
                        
                        logger.info(f"Google CSE: Found {len(results)} results")
                        return results
                    else:
                        logger.error(f"Google CSE error: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Google CSE failed: {e}")
            return []


class MultiSourceSearchEngine:
    """
    Intelligent multi-source search aggregator with fallback chain.
    
    Free Tier Priority:
    1. Brave Search (2k/month)
    2. Exa Search (1k/month)
    3. DuckDuckGo (unlimited)
    4. Wikipedia (unlimited)
    
    Premium Tier Priority:
    1. SerpAPI (Google)
    2. Google CSE
    3. Brave Search (paid)
    4. Exa Search (paid)
    """
    
    def __init__(self, tier: str = "free"):
        self.tier = tier
        
        # Initialize all engines
        self.brave = BraveSearchEngine()
        self.exa = ExaSearchEngine()
        self.duckduckgo = DuckDuckGoSearchEngine()
        self.wikipedia = WikipediaSearchEngine()
        self.serpapi = SerpAPISearchEngine()
        self.google_cse = GoogleCSESearchEngine()
        
    async def search(
        self,
        query: str,
        max_results: int = 10,
        use_fusion: bool = True
    ) -> List[SearchResult]:
        """
        Search across multiple sources with intelligent fallback.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            use_fusion: If True, combines results from multiple sources
            
        Returns:
            List of SearchResult objects
        """
        if self.tier == "premium":
            return await self._premium_search(query, max_results, use_fusion)
        else:
            return await self._free_search(query, max_results, use_fusion)
    
    async def _free_search(
        self,
        query: str,
        max_results: int,
        use_fusion: bool
    ) -> List[SearchResult]:
        """Free tier search with fallback chain."""
        
        all_results = []
        
        if use_fusion:
            # Try multiple sources in parallel
            tasks = [
                self.brave.search(query, max_results // 2),
                self.duckduckgo.search(query, max_results // 2),
                self.wikipedia.search(query, 2)
            ]
            
            results_list = await asyncio.gather(*tasks, return_exceptions=True)
            
            for results in results_list:
                if isinstance(results, list):
                    all_results.extend(results)
            
            # If we got enough results, return them
            if len(all_results) >= max_results // 2:
                return self._deduplicate_and_rank(all_results)[:max_results]
        
        # Fallback chain if fusion didn't work or wasn't requested
        for engine in [self.brave, self.exa, self.duckduckgo]:
            try:
                results = await engine.search(query, max_results)
                if results:
                    all_results.extend(results)
                    if len(all_results) >= max_results:
                        break
            except Exception as e:
                logger.error(f"Engine failed: {e}")
                continue
        
        # Add Wikipedia as supplementary
        try:
            wiki_results = await self.wikipedia.search(query, 2)
            all_results.extend(wiki_results)
        except:
            pass
        
        return self._deduplicate_and_rank(all_results)[:max_results]
    
    async def _premium_search(
        self,
        query: str,
        max_results: int,
        use_fusion: bool
    ) -> List[SearchResult]:
        """Premium tier search with better sources."""
        
        all_results = []
        
        # Try premium sources first
        for engine in [self.serpapi, self.google_cse]:
            try:
                results = await engine.search(query, max_results)
                if results:
                    all_results.extend(results)
                    if len(all_results) >= max_results:
                        break
            except Exception as e:
                logger.error(f"Premium engine failed: {e}")
                continue
        
        # Fallback to free sources if needed
        if len(all_results) < max_results // 2:
            fallback_results = await self._free_search(query, max_results, use_fusion)
            all_results.extend(fallback_results)
        
        return self._deduplicate_and_rank(all_results)[:max_results]
    
    def _deduplicate_and_rank(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicates and rank by relevance."""
        
        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        
        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        # Sort by relevance score
        unique_results.sort(key=lambda r: r.relevance_score, reverse=True)
        
        return unique_results
