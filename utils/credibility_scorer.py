"""
Source Credibility Scoring System
Evaluates source reliability based on domain authority, content quality, and bias indicators.
"""

from typing import Dict, Any, List
import re
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class CredibilityScorer:
    """Score source credibility and reliability."""
    
    # Domain authority lists
    HIGH_AUTHORITY_DOMAINS = {
        # Academic
        ".edu", ".ac.uk", "scholar.google", "arxiv.org", "researchgate.net",
        "pubmed.ncbi.nlm.nih.gov", "ieee.org", "acm.org", "springer.com",
        "sciencedirect.com", "nature.com", "science.org",
        
        # Government
        ".gov", ".gov.uk", "who.int", "cdc.gov", "nasa.gov", "nih.gov",
        
        # Major encyclopedias
        "wikipedia.org", "britannica.com", "stanford.edu",
        
        # Established news (fact-checked)
        "reuters.com", "apnews.com", "bbc.com", "nytimes.com", "wsj.com",
        "economist.com", "scientificamerican.com", "nature.com"
    }
    
    MEDIUM_AUTHORITY_DOMAINS = {
        ".org", "medium.com", "forbes.com", "bloomberg.com", "cnbc.com",
        "theguardian.com", "washingtonpost.com", "techcrunch.com",
        "wired.com", "arstechnica.com", "npr.org", "pbs.org"
    }
    
    # Bias indicators
    BIAS_INDICATORS = [
        # Strong bias language
        "fake news", "mainstream media", "deep state", "conspiracy",
        "they don't want you to know", "wake up", "truth revealed",
        
        # Sensationalism
        "shocking", "amazing", "unbelievable", "you won't believe",
        "this one trick", "doctors hate", "secret",
        
        # Political extremism
        "far-left", "far-right", "radical", "extremist"
    ]
    
    # Quality indicators
    QUALITY_INDICATORS = [
        # Citations
        "according to", "study shows", "research indicates",
        "published in", "peer-reviewed", "data suggests",
        
        # Attribution
        "dr.", "professor", "ph.d.", "researcher", "expert",
        
        # Methodology
        "methodology", "sample size", "statistical", "analysis"
    ]
    
    def __init__(self):
        """Initialize credibility scorer."""
        pass
    
    def score_source(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score single source credibility.
        
        Args:
            source: Source dictionary with url, title, snippet
            
        Returns:
            Dictionary with score and breakdown
        """
        url = source.get("url", "")
        title = source.get("title", "")
        snippet = source.get("snippet", "")
        
        # Initialize scores
        scores = {
            "domain_authority": self._score_domain_authority(url),
            "content_quality": self._score_content_quality(snippet),
            "bias_level": self._score_bias(title, snippet),
            "citation_presence": self._score_citations(snippet)
        }
        
        # Calculate weighted overall score (0-100)
        overall_score = (
            scores["domain_authority"] * 0.4 +
            scores["content_quality"] * 0.25 +
            (100 - scores["bias_level"]) * 0.2 +  # Lower bias = higher score
            scores["citation_presence"] * 0.15
        )
        
        # Determine credibility level
        if overall_score >= 80:
            credibility = "High"
            color = "green"
        elif overall_score >= 60:
            credibility = "Medium"
            color = "yellow"
        else:
            credibility = "Low"
            color = "red"
        
        return {
            "overall_score": round(overall_score, 1),
            "credibility_level": credibility,
            "color": color,
            "breakdown": scores,
            "domain": urlparse(url).netloc
        }
    
    def _score_domain_authority(self, url: str) -> float:
        """
        Score domain authority (0-100).
        
        Args:
            url: Source URL
            
        Returns:
            Authority score
        """
        url_lower = url.lower()
        
        # Check high authority
        for domain in self.HIGH_AUTHORITY_DOMAINS:
            if domain in url_lower:
                return 90.0
        
        # Check medium authority
        for domain in self.MEDIUM_AUTHORITY_DOMAINS:
            if domain in url_lower:
                return 70.0
        
        # HTTPS check
        if url.startswith("https://"):
            return 50.0
        
        return 30.0
    
    def _score_content_quality(self, content: str) -> float:
        """
        Score content quality based on indicators (0-100).
        
        Args:
            content: Content text
            
        Returns:
            Quality score
        """
        if not content:
            return 30.0
        
        content_lower = content.lower()
        
        # Count quality indicators
        quality_count = sum(
            1 for indicator in self.QUALITY_INDICATORS
            if indicator in content_lower
        )
        
        # Length check (too short = low quality)
        word_count = len(content.split())
        length_score = min(word_count / 50 * 100, 100)  # 50+ words = full score
        
        # Grammar check (simple - proper capitalization)
        sentences = content.split('.')
        capitalized = sum(1 for s in sentences if s.strip() and s.strip()[0].isupper())
        grammar_score = (capitalized / max(len(sentences), 1)) * 100
        
        # Combined score
        quality_score = (
            (quality_count * 15) * 0.4 +  # Indicator presence
            length_score * 0.4 +
            grammar_score * 0.2
        )
        
        return min(quality_score, 100.0)
    
    def _score_bias(self, title: str, content: str) -> float:
        """
        Score bias level (0-100, higher = more biased).
        
        Args:
            title: Source title
            content: Content text
            
        Returns:
            Bias score
        """
        text = (title + " " + content).lower()
        
        # Count bias indicators
        bias_count = sum(
            1 for indicator in self.BIAS_INDICATORS
            if indicator in text
        )
        
        # Excessive punctuation (!!!, ???)
        excessive_punct = len(re.findall(r'[!?]{3,}', text))
        
        # ALL CAPS words
        words = text.split()
        caps_count = sum(1 for word in words if word.isupper() and len(word) > 3)
        caps_ratio = caps_count / max(len(words), 1)
        
        # Calculate bias score
        bias_score = (
            bias_count * 20 +  # Each indicator = +20
            excessive_punct * 15 +  # Each excessive punct = +15
            caps_ratio * 100  # High caps ratio = high bias
        )
        
        return min(bias_score, 100.0)
    
    def _score_citations(self, content: str) -> float:
        """
        Score citation presence (0-100).
        
        Args:
            content: Content text
            
        Returns:
            Citation score
        """
        if not content:
            return 0.0
        
        content_lower = content.lower()
        
        # Citation patterns
        citation_patterns = [
            r'\(\d{4}\)',  # (2023)
            r'\[\d+\]',    # [1]
            r'et al\.',    # et al.
            r'according to',
            r'study',
            r'research'
        ]
        
        citation_count = sum(
            len(re.findall(pattern, content_lower))
            for pattern in citation_patterns
        )
        
        # Score based on citation density
        word_count = len(content.split())
        citation_density = (citation_count / max(word_count, 1)) * 1000  # Per 1000 words
        
        return min(citation_density * 20, 100.0)
    
    def score_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score multiple sources and add credibility data.
        
        Args:
            sources: List of source dictionaries
            
        Returns:
            Sources with added credibility_score field
        """
        scored_sources = []
        
        for source in sources:
            try:
                score = self.score_source(source)
                source["credibility_score"] = score
                scored_sources.append(source)
            except Exception as e:
                logger.error(f"Failed to score source: {e}")
                source["credibility_score"] = {
                    "overall_score": 50.0,
                    "credibility_level": "Unknown",
                    "color": "gray",
                    "breakdown": {},
                    "domain": "unknown"
                }
                scored_sources.append(source)
        
        # Sort by credibility score (highest first)
        scored_sources.sort(
            key=lambda x: x["credibility_score"]["overall_score"],
            reverse=True
        )
        
        return scored_sources
    
    def get_credibility_report(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate credibility report for all sources.
        
        Args:
            sources: List of scored sources
            
        Returns:
            Credibility report dictionary
        """
        if not sources:
            return {
                "total_sources": 0,
                "average_score": 0,
                "high_credibility": 0,
                "medium_credibility": 0,
                "low_credibility": 0
            }
        
        scores = [s.get("credibility_score", {}).get("overall_score", 50) for s in sources]
        
        high_count = sum(1 for s in scores if s >= 80)
        medium_count = sum(1 for s in scores if 60 <= s < 80)
        low_count = sum(1 for s in scores if s < 60)
        
        return {
            "total_sources": len(sources),
            "average_score": round(sum(scores) / len(scores), 1),
            "high_credibility": high_count,
            "medium_credibility": medium_count,
            "low_credibility": low_count,
            "high_percentage": round(high_count / len(sources) * 100, 1),
            "median_score": round(sorted(scores)[len(scores) // 2], 1)
        }


# Singleton instance
_scorer = None


def get_credibility_scorer() -> CredibilityScorer:
    """Get singleton credibility scorer instance."""
    global _scorer
    if _scorer is None:
        _scorer = CredibilityScorer()
    return _scorer
