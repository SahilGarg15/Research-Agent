"""Gap-Finder Agent - Identifies missing information in research."""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent
import json


class GapFinderAgent(BaseAgent):
    """
    Compares collected data with research outline to find knowledge gaps.
    """
    
    def __init__(self, llm_client, model_name: str = None):
        super().__init__("GapFinderAgent", llm_client, model_name)
        
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Identify gaps in research coverage.
        
        Args:
            input_data: {
                "research_outline": Dict - From QueryExpansionAgent,
                "verified_facts": List[Dict] - From FactCheckerAgent,
                "key_questions": List[str] - Original questions
            }
            
        Returns:
            {
                "gaps_found": List[Dict] - Missing topics/questions,
                "coverage_score": float - 0-100%,
                "additional_queries": List[str] - Suggested searches,
                "needs_more_research": bool
            }
        """
        self.validate_input(input_data, ["research_outline", "verified_facts"])
        
        outline = input_data["research_outline"]
        verified_facts = input_data["verified_facts"]
        key_questions = input_data.get("key_questions", [])
        
        self.log_progress("Analyzing research coverage")
        
        # Analyze gaps using LLM
        gaps_analysis = await self._analyze_gaps(outline, verified_facts, key_questions)
        
        coverage_score = gaps_analysis.get("coverage_score", 0)
        needs_more = coverage_score < 80
        
        self.log_progress(
            f"Coverage score: {coverage_score}%, "
            f"Needs more research: {needs_more}"
        )
        
        return {
            "gaps_found": gaps_analysis.get("gaps", []),
            "coverage_score": coverage_score,
            "additional_queries": gaps_analysis.get("additional_queries", []),
            "needs_more_research": needs_more,
            "recommendations": gaps_analysis.get("recommendations", [])
        }
        
    async def _analyze_gaps(
        self,
        outline: Dict[str, Any],
        facts: List[Dict],
        questions: List[str]
    ) -> Dict[str, Any]:
        """
        Use LLM to analyze gaps between outline and collected facts.
        """
        # Format outline
        outline_text = "\n".join([
            f"## {section}\n" + "\n".join([f"- {point}" for point in points])
            for section, points in outline.items()
        ])
        
        # Format facts
        facts_text = "\n".join([
            f"- {f.get('fact', '')} (confidence: {f.get('confidence_score', 0)}%)"
            for f in facts[:50]  # Limit to top 50 facts
        ])
        
        # Format questions
        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        
        system_prompt = """You are a research gap analyst. Compare the research outline with collected facts to identify:
1. Topics in the outline not covered by facts
2. Key questions not answered
3. Areas needing more depth
4. Missing perspectives or data

Provide response in JSON:
{
    "coverage_score": 75,
    "gaps": [
        {
            "topic": "missing topic",
            "severity": "high|medium|low",
            "description": "what's missing"
        }
    ],
    "additional_queries": ["search query 1", "search query 2"],
    "recommendations": ["recommendation 1", "recommendation 2"]
}"""

        user_prompt = f"""Research Outline:
{outline_text}

Key Questions:
{questions_text}

Collected Facts ({len(facts)} total):
{facts_text}

Analyze the gaps and suggest additional research."""

        try:
            response = await self._call_llm(system_prompt, user_prompt)
            return json.loads(response)
            
        except Exception as e:
            self.logger.error(f"Gap analysis failed: {e}")
            
            # Fallback: simple heuristic
            coverage = min(100, (len(facts) / max(len(questions), 5)) * 100)
            
            return {
                "coverage_score": coverage,
                "gaps": [],
                "additional_queries": questions[:3],  # Use original questions
                "recommendations": ["Collect more diverse sources"]
            }
            
    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call the LLM."""
        if not self.llm_client:
            raise ValueError("LLM client not configured")
            
        response = await self.llm_client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5,
            max_tokens=2000
        )
        return response.choices[0].message.content
