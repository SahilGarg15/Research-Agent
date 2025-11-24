"""Enhanced orchestrator with subscription tier support."""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from agents.query_expansion import QueryExpansionAgent
from agents.search_agent import SearchAgent
from agents.summarizer import SummarizerAgent
from agents.fact_checker import FactCheckerAgent
from agents.gap_finder import GapFinderAgent
from agents.writer import WriterAgent
from agents.editor import EditorAgent
from agents.citation import CitationAgent
from agents.publisher import PublisherAgent

from subscription.manager import SubscriptionManager, SubscriptionTier
from models.router import ModelRouter
from utils.logger import setup_logger, log_agent_start, log_agent_complete, display_research_summary


class TieredResearchOrchestrator:
    """
    Coordinates all agents with subscription tier awareness.
    """
    
    def __init__(self, user_id: str = "default_user", tier: SubscriptionTier = SubscriptionTier.FREE):
        """
        Initialize orchestrator with subscription tier.
        
        Args:
            user_id: User identifier
            tier: Subscription tier (free or premium)
        """
        self.user_id = user_id
        self.tier = tier
        self.logger = setup_logger("TieredOrchestrator")
        
        # Initialize subscription manager
        self.subscription_manager = SubscriptionManager()
        subscription = self.subscription_manager.get_subscription(user_id)
        subscription.tier = tier
        
        # Initialize model router
        self.model_router = ModelRouter()
        
        # Select appropriate model based on tier
        self.model_config = self.model_router.select_model(tier)
        self.llm_client = self.model_router.get_client(self.model_config)
        
        self.logger.info(f"Initialized with {tier.value} tier")
        self.logger.info(f"Using model: {self.model_config['model']}")
        
        # Get model name to pass to agents
        model_name = self.model_config['model']
        
        # Initialize agents with model name
        self.agents = {
            "query_expansion": QueryExpansionAgent(self.llm_client, model_name),
            "search": SearchAgent(self.llm_client),
            "summarizer": SummarizerAgent(self.llm_client, model_name),
            "fact_checker": FactCheckerAgent(self.llm_client, model_name),
            "gap_finder": GapFinderAgent(self.llm_client, model_name),
            "writer": WriterAgent(self.llm_client, model_name),
            "editor": EditorAgent(self.llm_client, model_name),
            "citation": CitationAgent(self.llm_client, model_name),
            "publisher": PublisherAgent(self.llm_client)
        }
        
    async def research(
        self,
        query: str,
        output_format: str = "pdf",
        citation_style: str = "APA"
    ) -> Dict[str, Any]:
        """
        Execute the complete research pipeline with tier-aware features.
        
        Args:
            query: Research topic/question
            output_format: Output format(s)
            citation_style: Citation style
            
        Returns:
            Dictionary with research results and output paths
        """
        
        # Check access
        can_access, error_msg = self.subscription_manager.check_access(self.user_id)
        if not can_access:
            return {
                "success": False,
                "error": error_msg,
                "tier": self.tier.value
            }
        
        # Get subscription limits
        subscription = self.subscription_manager.get_subscription(self.user_id)
        limits = subscription.get_limits()
        
        self.logger.info(f"Starting research for: {query}")
        self.logger.info(f"Tier: {self.tier.value.upper()}")
        self.logger.info(f"Word limit: {limits.word_limit}")
        self.logger.info(f"Max iterations: {limits.max_search_rounds}")
        
        start_time = datetime.now()
        
        # Context storage
        context = {
            "original_query": query,
            "tier": self.tier.value,
            "limits": limits.dict(),
            "iteration": 0
        }
        
        try:
            # Stage 1: Query Expansion
            self.logger.info("=" * 60)
            self.logger.info("STAGE 1: Query Expansion")
            self.logger.info("=" * 60)
            
            expansion_result = await self.agents["query_expansion"].run({
                "query": query
            })
            
            # Update context with expansion results, with fallback
            if expansion_result.output_data:
                context.update(expansion_result.output_data)
            
            # Ensure required keys exist
            if "research_outline" not in context:
                context["research_outline"] = {
                    "Introduction": ["Background", "Context"],
                    "Main Content": ["Key points", "Details"],
                    "Conclusion": ["Summary", "Findings"]
                }
            if "expanded_topics" not in context:
                context["expanded_topics"] = [query]
            if "key_questions" not in context:
                context["key_questions"] = [f"What is {query}?", f"How does {query} work?"]
            
            # Stage 2: Research Loop (tier-dependent iterations)
            max_iterations = limits.max_search_rounds
            
            for iteration in range(max_iterations):
                context["iteration"] = iteration + 1
                
                self.logger.info(f"\n{'=' * 60}")
                self.logger.info(f"RESEARCH ITERATION {iteration + 1}/{max_iterations}")
                self.logger.info("=" * 60)
                
                # Search
                self.logger.info("\nSTAGE 2: Web Search")
                search_queries = self._generate_search_queries(context)
                
                search_result = await self.agents["search"].run({
                    "queries": search_queries,
                    "max_results_per_query": 10 if self.tier == SubscriptionTier.PREMIUM else 5
                })
                
                context["search_results"] = search_result.output_data["search_results"]
                
                # Summarize
                self.logger.info("\nSTAGE 3: Content Summarization")
                max_urls = 15 if self.tier == SubscriptionTier.PREMIUM else 10
                
                summarizer_result = await self.agents["summarizer"].run({
                    "search_results": context["search_results"],
                    "max_urls": max_urls
                })
                
                if "summaries" not in context:
                    context["summaries"] = []
                context["summaries"].extend(summarizer_result.output_data["summaries"])
                
                # Fact Check (tier-dependent)
                if limits.advanced_fact_checking:
                    self.logger.info("\nSTAGE 4: Advanced Fact Checking")
                    fact_check_result = await self.agents["fact_checker"].run({
                        "summaries": context["summaries"]
                    })
                    context["verified_facts"] = fact_check_result.output_data["verified_facts"]
                    context["consensus_facts"] = fact_check_result.output_data["consensus_facts"]
                else:
                    self.logger.info("\nSTAGE 4: Basic Fact Extraction")
                    context["verified_facts"] = self._extract_basic_facts(context["summaries"])
                    context["consensus_facts"] = context["verified_facts"][:20]
                
                # Gap Analysis (only for premium with multi-round)
                if limits.multi_round_search and iteration < max_iterations - 1:
                    self.logger.info("\nSTAGE 5: Gap Analysis")
                    gap_result = await self.agents["gap_finder"].run({
                        "research_outline": context["research_outline"],
                        "verified_facts": context["verified_facts"],
                        "key_questions": context.get("key_questions", [])
                    })
                    
                    context["gaps"] = gap_result.output_data["gaps_found"]
                    context["coverage_score"] = gap_result.output_data["coverage_score"]
                    
                    display_research_summary({
                        "Iteration": f"{iteration + 1}/{max_iterations}",
                        "Tier": self.tier.value.upper(),
                        "Sources": len(context["summaries"]),
                        "Facts": len(context["verified_facts"]),
                        "Coverage": f"{context['coverage_score']:.1f}%"
                    })
                    
                    if not gap_result.output_data["needs_more_research"]:
                        self.logger.info("\n✅ Research coverage sufficient!")
                        break
                else:
                    context["coverage_score"] = 75.0  # Estimate for free tier
                    
            # Stage 6: Report Generation
            self.logger.info(f"\n{'=' * 60}")
            self.logger.info("STAGE 6: Report Generation")
            self.logger.info("=" * 60)
            
            writer_result = await self.agents["writer"].run({
                "original_query": query,
                "research_outline": context["research_outline"],
                "verified_facts": context["verified_facts"][:limits.word_limit // 20],  # Limit facts
                "summaries": context["summaries"]
            })
            
            context["report"] = writer_result.output_data["report"]
            context["metadata"] = writer_result.output_data["metadata"]
            
            # Apply word limit
            context["report"] = self._apply_word_limit(context["report"], limits.word_limit)
            
            # Stage 7: Editing (premium only)
            if self.tier == SubscriptionTier.PREMIUM:
                self.logger.info("\nSTAGE 7: Report Editing")
                editor_result = await self.agents["editor"].run({
                    "report": context["report"]
                })
                context["edited_report"] = editor_result.output_data["edited_report"]
            else:
                context["edited_report"] = context["report"]
            
            # Stage 8: Citations
            self.logger.info("\nSTAGE 8: Adding Citations")
            
            # Check if requested citation style is allowed
            if citation_style not in limits.citation_styles and citation_style != "basic":
                self.logger.warning(f"Citation style {citation_style} not available in {self.tier.value} tier. Using basic.")
                citation_style = "basic"
            
            citation_result = await self.agents["citation"].run({
                "edited_report": context["edited_report"],
                "summaries": context["summaries"],
                "citation_style": citation_style if self.tier == SubscriptionTier.PREMIUM else "basic"
            })
            
            context["final_report"] = citation_result.output_data["report_with_citations"]
            context["references"] = citation_result.output_data["references"]
            
            # Stage 9: Publishing
            self.logger.info("\nSTAGE 9: Publishing")
            
            # Check format availability
            requested_formats = [output_format] if output_format != "all" else ["pdf", "docx", "markdown"]
            allowed_formats = [f for f in requested_formats if f in limits.export_formats]
            
            if not allowed_formats:
                allowed_formats = ["pdf"]  # Default fallback
            
            publisher_result = await self.agents["publisher"].run({
                "report_with_citations": context["final_report"],
                "metadata": context["metadata"],
                "output_formats": allowed_formats,
                "output_filename": query[:50]
            })
            
            context["output_files"] = publisher_result.output_data["output_files"]
            
            # Record usage
            self.subscription_manager.record_usage(self.user_id)
            
            # Calculate stats
            elapsed = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(f"\n{'=' * 60}")
            self.logger.info("✅ RESEARCH COMPLETE!")
            self.logger.info("=" * 60)
            self.logger.info(f"Tier: {self.tier.value.upper()}")
            self.logger.info(f"Time: {elapsed:.1f}s")
            self.logger.info(f"Sources: {len(context['summaries'])}")
            self.logger.info(f"Facts: {len(context['verified_facts'])}")
            self.logger.info(f"Coverage: {context.get('coverage_score', 0):.1f}%")
            
            # Get usage stats
            usage_stats = self.subscription_manager.get_usage_stats(self.user_id)
            
            return {
                "success": True,
                "query": query,
                "tier": self.tier.value,
                "output_files": context["output_files"],
                "metadata": context["metadata"],
                "statistics": {
                    "sources_count": len(context["summaries"]),
                    "facts_count": len(context["verified_facts"]),
                    "coverage_score": context.get("coverage_score", 0),
                    "time_elapsed": elapsed,
                    "word_count": len(context["final_report"].split())
                },
                "usage": usage_stats
            }
            
        except Exception as e:
            self.logger.error(f"Research pipeline failed: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "tier": self.tier.value
            }
    
    def _generate_search_queries(self, context: Dict[str, Any]) -> List[str]:
        """Generate search queries based on context."""
        queries = []
        
        if context.get("iteration", 1) == 1:
            expanded_topics = context.get("expanded_topics", [])
            queries.extend(expanded_topics[:5])
        else:
            gaps = context.get("gaps", [])
            for gap in gaps[:3]:
                if isinstance(gap, dict):
                    queries.append(gap.get("topic", ""))
        
        if not queries:
            queries.append(context["original_query"])
        
        return queries
    
    def _extract_basic_facts(self, summaries: List[Dict]) -> List[Dict]:
        """Extract basic facts for free tier (no LLM fact-checking)."""
        facts = []
        
        for summary in summaries:
            key_facts = summary.get("key_facts", [])
            for fact in key_facts[:5]:  # Limit per source
                facts.append({
                    "fact": fact,
                    "confidence_score": 60,  # Basic confidence
                    "source": summary.get("url", ""),
                    "supporting_sources": 1
                })
        
        return facts[:50]  # Limit total facts for free tier
    
    def _apply_word_limit(self, report: str, word_limit: int) -> str:
        """Apply word limit to report."""
        words = report.split()
        
        if len(words) <= word_limit:
            return report
        
        # Truncate and add notice
        truncated = " ".join(words[:word_limit])
        truncated += "\n\n---\n\n*[Report truncated due to word limit. Upgrade to Premium for full reports.]*"
        
        return truncated
