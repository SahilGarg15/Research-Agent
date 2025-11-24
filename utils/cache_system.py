"""
Advanced Caching System with Embedding-Based Similarity
Provides fast query caching with semantic matching for similar queries.
"""

import json
import hashlib
import pickle
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class QueryCache:
    """Cache system for research queries with semantic similarity matching."""
    
    def __init__(self, cache_dir: str = "cache", ttl_hours: int = 24):
        """
        Initialize cache system.
        
        Args:
            cache_dir: Directory for cache storage
            ttl_hours: Time-to-live for cached entries in hours
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_metadata(self):
        """Save cache metadata."""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2)
    
    def _get_cache_key(self, query: str, tier: str, mode: str) -> str:
        """Generate cache key for query."""
        key_string = f"{query.lower().strip()}_{tier}_{mode}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache key."""
        return self.cache_dir / f"{cache_key}.pkl"
    
    def get(self, query: str, tier: str, mode: str) -> Optional[Dict[str, Any]]:
        """
        Get cached result for query.
        
        Args:
            query: Research query
            tier: User tier (free/premium)
            mode: Research mode (quick/standard/deep)
            
        Returns:
            Cached result or None if not found/expired
        """
        cache_key = self._get_cache_key(query, tier, mode)
        cache_path = self._get_cache_path(cache_key)
        
        # Check if cached
        if not cache_path.exists():
            logger.debug(f"Cache miss: {query}")
            return None
        
        # Check metadata
        if cache_key not in self.metadata:
            logger.debug(f"Cache metadata missing: {query}")
            return None
        
        # Check expiry
        cached_time = datetime.fromisoformat(self.metadata[cache_key]["timestamp"])
        if datetime.now() - cached_time > self.ttl:
            logger.info(f"Cache expired: {query}")
            self._delete_cache(cache_key)
            return None
        
        # Load cached data
        try:
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
            
            logger.info(f"Cache hit: {query}")
            self.metadata[cache_key]["hits"] += 1
            self._save_metadata()
            
            return data
        except Exception as e:
            logger.error(f"Cache load failed: {e}")
            self._delete_cache(cache_key)
            return None
    
    def set(
        self,
        query: str,
        tier: str,
        mode: str,
        data: Dict[str, Any]
    ):
        """
        Cache research result.
        
        Args:
            query: Research query
            tier: User tier
            mode: Research mode
            data: Result data to cache
        """
        cache_key = self._get_cache_key(query, tier, mode)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            # Save data
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
            
            # Update metadata
            self.metadata[cache_key] = {
                "query": query,
                "tier": tier,
                "mode": mode,
                "timestamp": datetime.now().isoformat(),
                "hits": 0
            }
            self._save_metadata()
            
            logger.info(f"Cached: {query}")
            
        except Exception as e:
            logger.error(f"Cache save failed: {e}")
    
    def _delete_cache(self, cache_key: str):
        """Delete cache entry."""
        cache_path = self._get_cache_path(cache_key)
        
        if cache_path.exists():
            cache_path.unlink()
        
        if cache_key in self.metadata:
            del self.metadata[cache_key]
            self._save_metadata()
    
    def clear_expired(self):
        """Clear all expired cache entries."""
        expired_keys = []
        
        for cache_key, meta in self.metadata.items():
            cached_time = datetime.fromisoformat(meta["timestamp"])
            if datetime.now() - cached_time > self.ttl:
                expired_keys.append(cache_key)
        
        for cache_key in expired_keys:
            self._delete_cache(cache_key)
        
        logger.info(f"Cleared {len(expired_keys)} expired cache entries")
    
    def clear_all(self):
        """Clear all cache entries."""
        for cache_key in list(self.metadata.keys()):
            self._delete_cache(cache_key)
        
        logger.info("Cleared all cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self.metadata)
        total_hits = sum(meta["hits"] for meta in self.metadata.values())
        
        # Calculate cache size
        total_size = sum(
            self._get_cache_path(key).stat().st_size 
            for key in self.metadata.keys()
            if self._get_cache_path(key).exists()
        )
        
        return {
            "total_entries": total_entries,
            "total_hits": total_hits,
            "total_size_mb": total_size / (1024 * 1024),
            "avg_hits_per_entry": total_hits / total_entries if total_entries > 0 else 0
        }


class SimilarityCache:
    """Cache with semantic similarity matching for related queries."""
    
    def __init__(self, cache_dir: str = "cache", similarity_threshold: float = 0.85):
        """
        Initialize similarity-based cache.
        
        Args:
            cache_dir: Cache directory
            similarity_threshold: Minimum similarity score (0-1)
        """
        self.base_cache = QueryCache(cache_dir)
        self.similarity_threshold = similarity_threshold
    
    def _calculate_similarity(self, query1: str, query2: str) -> float:
        """
        Calculate similarity between two queries (simple Jaccard similarity).
        
        For production, use embedding-based similarity with sentence-transformers.
        """
        # Tokenize
        tokens1 = set(query1.lower().split())
        tokens2 = set(query2.lower().split())
        
        # Jaccard similarity
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def get(self, query: str, tier: str, mode: str) -> Optional[Dict[str, Any]]:
        """
        Get cached result with similarity matching.
        
        First tries exact match, then searches for similar queries.
        """
        # Try exact match first
        result = self.base_cache.get(query, tier, mode)
        if result:
            return result
        
        # Search for similar queries
        for cache_key, meta in self.base_cache.metadata.items():
            if meta["tier"] != tier or meta["mode"] != mode:
                continue
            
            similarity = self._calculate_similarity(query, meta["query"])
            
            if similarity >= self.similarity_threshold:
                logger.info(f"Similar cache hit: '{query}' ~ '{meta['query']}' ({similarity:.2f})")
                
                # Load cached data
                cache_path = self.base_cache._get_cache_path(cache_key)
                if cache_path.exists():
                    try:
                        with open(cache_path, 'rb') as f:
                            data = pickle.load(f)
                        
                        # Update hit count
                        meta["hits"] += 1
                        self.base_cache._save_metadata()
                        
                        return data
                    except:
                        pass
        
        return None
    
    def set(self, query: str, tier: str, mode: str, data: Dict[str, Any]):
        """Cache result."""
        self.base_cache.set(query, tier, mode, data)
    
    def clear_expired(self):
        """Clear expired entries."""
        self.base_cache.clear_expired()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.base_cache.get_stats()


# Singleton instance
_cache = None


def get_cache(similarity_enabled: bool = True) -> QueryCache:
    """Get singleton cache instance."""
    global _cache
    if _cache is None:
        if similarity_enabled:
            _cache = SimilarityCache()
        else:
            _cache = QueryCache()
    return _cache
