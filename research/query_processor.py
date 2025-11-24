"""
Smart Query Processing System
Handles keyword extraction, query expansion, synonym replacement,
question classification, and auto-correction.
"""

import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import asyncio


@dataclass
class ProcessedQuery:
    """Result of query processing."""
    original: str
    corrected: str
    keywords: List[str]
    expanded_queries: List[str]
    synonyms: Dict[str, List[str]]
    question_type: str
    sub_topics: List[str]


class QueryProcessor:
    """Smart query processing for better search results."""
    
    # Common question patterns
    QUESTION_PATTERNS = {
        "definition": r"^(what is|what are|define|meaning of)",
        "how_to": r"^(how to|how do|how can)",
        "why": r"^(why|what causes|what leads to)",
        "comparison": r"(compare|difference between|versus|vs)",
        "pros_cons": r"(advantages|disadvantages|pros|cons|benefits|drawbacks)",
        "examples": r"(examples of|case studies|instances of)",
        "statistics": r"(statistics|data|numbers|percentage)",
        "history": r"(history of|evolution of|origin of)",
        "future": r"(future of|trends in|predictions)",
        "location": r"(where|location|place)",
        "time": r"(when|timeline|date)"
    }
    
    # Common typo corrections
    CORRECTIONS = {
        "artifical": "artificial",
        "inteligence": "intelligence",
        "seperate": "separate",
        "definately": "definitely",
        "recieve": "receive",
        "occured": "occurred",
        "untill": "until",
        "acheive": "achieve"
    }
    
    # Topic synonyms for expansion
    SYNONYMS = {
        "AI": ["artificial intelligence", "machine learning", "deep learning", "neural networks"],
        "health": ["healthcare", "medical", "wellness", "medicine"],
        "technology": ["tech", "digital", "innovation", "advancement"],
        "business": ["company", "enterprise", "organization", "firm"],
        "education": ["learning", "teaching", "academic", "school"],
        "climate": ["environmental", "weather", "global warming", "sustainability"],
        "economy": ["economic", "financial", "market", "business"],
        "research": ["study", "investigation", "analysis", "examination"]
    }
    
    def __init__(self, llm_client=None, model_name: str = None):
        self.llm_client = llm_client
        self.model_name = model_name
    
    async def process(self, query: str) -> ProcessedQuery:
        """
        Process a query through all enhancement steps.
        
        Args:
            query: Raw user query
            
        Returns:
            ProcessedQuery with all enhancements
        """
        # Step 1: Correct common typos
        corrected = self._auto_correct(query)
        
        # Step 2: Classify question type
        question_type = self._classify_question(corrected)
        
        # Step 3: Extract keywords
        keywords = self._extract_keywords(corrected)
        
        # Step 4: Expand query with synonyms
        expanded = self._expand_query(corrected, keywords)
        
        # Step 5: Generate sub-topics (if LLM available)
        sub_topics = await self._generate_sub_topics(corrected) if self.llm_client else []
        
        # Step 6: Build synonym map
        synonym_map = self._build_synonym_map(keywords)
        
        return ProcessedQuery(
            original=query,
            corrected=corrected,
            keywords=keywords,
            expanded_queries=expanded,
            synonyms=synonym_map,
            question_type=question_type,
            sub_topics=sub_topics
        )
    
    def _auto_correct(self, query: str) -> str:
        """Auto-correct common typos."""
        corrected = query
        
        for typo, correction in self.CORRECTIONS.items():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(typo), re.IGNORECASE)
            corrected = pattern.sub(correction, corrected)
        
        return corrected
    
    def _classify_question(self, query: str) -> str:
        """Classify the type of question."""
        query_lower = query.lower()
        
        for q_type, pattern in self.QUESTION_PATTERNS.items():
            if re.search(pattern, query_lower):
                return q_type
        
        return "general"
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query."""
        # Remove common stop words
        stop_words = {
            "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
            "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
            "to", "was", "will", "with", "the", "this", "but", "they", "have",
            "had", "what", "when", "where", "who", "which", "why", "how"
        }
        
        # Tokenize and filter
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
        
        return unique_keywords[:10]  # Top 10 keywords
    
    def _expand_query(self, query: str, keywords: List[str]) -> List[str]:
        """Expand query with related variations."""
        expanded = [query]  # Always include original
        
        # Add queries with synonyms
        for keyword in keywords:
            # Check if keyword has known synonyms
            for term, synonyms in self.SYNONYMS.items():
                if keyword.lower() in term.lower() or term.lower() in keyword.lower():
                    for synonym in synonyms[:2]:  # Use top 2 synonyms
                        expanded_query = query.replace(keyword, synonym)
                        if expanded_query != query:
                            expanded.append(expanded_query)
        
        # Add question-specific expansions
        query_lower = query.lower()
        
        if "ai" in query_lower or "artificial intelligence" in query_lower:
            expanded.extend([
                query + " applications",
                query + " case studies",
                query + " benefits and risks"
            ])
        
        if "impact" in query_lower:
            expanded.extend([
                query.replace("impact", "effects"),
                query.replace("impact", "influence"),
                query + " research"
            ])
        
        # Remove duplicates
        return list(dict.fromkeys(expanded))[:5]  # Top 5 variations
    
    def _build_synonym_map(self, keywords: List[str]) -> Dict[str, List[str]]:
        """Build a map of keywords to their synonyms."""
        synonym_map = {}
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            synonyms = []
            
            # Find matching synonyms
            for term, syn_list in self.SYNONYMS.items():
                if keyword_lower in term.lower() or term.lower() in keyword_lower:
                    synonyms.extend(syn_list)
            
            if synonyms:
                synonym_map[keyword] = list(set(synonyms))[:5]
        
        return synonym_map
    
    async def _generate_sub_topics(self, query: str) -> List[str]:
        """Generate sub-topics using LLM."""
        if not self.llm_client or not self.model_name:
            return []
        
        try:
            system_prompt = """You are a research planning expert. Break down the given topic into 3-5 key sub-topics that should be researched.
Return ONLY a JSON array of strings, like: ["subtopic 1", "subtopic 2", "subtopic 3"]"""
            
            user_prompt = f"Break down this research topic into key sub-topics:\n\n{query}"
            
            response = await self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON
            import json
            try:
                sub_topics = json.loads(content)
                if isinstance(sub_topics, list):
                    return sub_topics[:5]
            except:
                # Fallback: extract lines
                lines = [line.strip(' -•*') for line in content.split('\n') if line.strip()]
                return [line for line in lines if len(line) > 10][:5]
        
        except Exception as e:
            print(f"Sub-topic generation failed: {e}")
            return []
    
    def get_search_variants(self, query: str) -> List[str]:
        """
        Get search query variants optimized for different search engines.
        
        Returns multiple versions of the query for better coverage.
        """
        variants = [query]
        
        # Add quoted version for exact matches
        variants.append(f'"{query}"')
        
        # Add question format
        if not query.lower().startswith(("what", "how", "why", "when", "where")):
            variants.append(f"what is {query}")
        
        # Add "overview" version
        variants.append(f"{query} overview")
        
        # Add "research" version
        variants.append(f"{query} research studies")
        
        return variants[:4]  # Return top 4 variants


class QueryExpander:
    """Advanced query expansion using LLM."""
    
    def __init__(self, llm_client=None, model_name: str = None):
        self.llm_client = llm_client
        self.model_name = model_name
    
    async def expand_semantic(self, query: str) -> List[str]:
        """Expand query using semantic understanding."""
        if not self.llm_client or not self.model_name:
            return [query]
        
        try:
            system_prompt = """Generate 3-5 alternative ways to search for the given topic. Focus on:
1. Different phrasings
2. Related concepts
3. Specific aspects
4. Alternative terminology

Return as JSON array: ["variant 1", "variant 2", ...]"""
            
            response = await self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.8,
                max_tokens=300
            )
            
            content = response.choices[0].message.content.strip()
            
            import json
            try:
                variants = json.loads(content)
                if isinstance(variants, list):
                    return [query] + variants[:4]
            except:
                pass
        
        except Exception as e:
            print(f"Semantic expansion failed: {e}")
        
        return [query]
