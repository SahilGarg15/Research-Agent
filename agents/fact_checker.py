"""Fact-Checker Agent - Verifies claims and assigns confidence scores."""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent
import json
from collections import Counter


class FactCheckerAgent(BaseAgent):
    """
    Cross-checks facts across multiple sources and assigns confidence scores.
    """
    
    def __init__(self, llm_client, model_name: str = None):
        super().__init__("FactCheckerAgent", llm_client, model_name)
        
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify facts across summaries and assign confidence scores.
        
        Args:
            input_data: {
                "summaries": List[Dict] - Summaries from SummarizerAgent
            }
            
        Returns:
            {
                "verified_facts": List[Dict] - Facts with confidence scores,
                "contradictions": List[Dict] - Conflicting information,
                "consensus_facts": List[Dict] - High-confidence facts
            }
        """
        self.validate_input(input_data, ["summaries"])
        
        summaries = input_data["summaries"]
        
        self.log_progress(f"Fact-checking across {len(summaries)} sources")
        
        # Extract all facts from summaries
        all_facts = []
        for summary in summaries:
            facts = summary.get("key_facts", [])
            stats = summary.get("statistics", [])
            url = summary.get("url", "")
            
            for fact in facts:
                all_facts.append({
                    "fact": fact,
                    "source": url,
                    "type": "fact"
                })
                
            for stat in stats:
                all_facts.append({
                    "fact": stat,
                    "source": url,
                    "type": "statistic"
                })
                
        self.log_progress(f"Extracted {len(all_facts)} facts")
        
        # Group similar facts and check for contradictions
        verified_facts = await self._verify_facts(all_facts)
        
        # Identify high-confidence consensus facts
        consensus_facts = [
            f for f in verified_facts 
            if f.get("confidence_score", 0) >= 80
        ]
        
        # Identify contradictions
        contradictions = [
            f for f in verified_facts
            if f.get("has_contradiction", False)
        ]
        
        self.log_progress(
            f"Verified {len(verified_facts)} facts, "
            f"{len(consensus_facts)} high-confidence, "
            f"{len(contradictions)} contradictions"
        )
        
        return {
            "verified_facts": verified_facts,
            "contradictions": contradictions,
            "consensus_facts": consensus_facts,
            "total_sources": len(summaries)
        }
        
    async def _verify_facts(self, facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Verify facts using LLM to group similar claims and detect contradictions.
        
        Args:
            facts: List of fact dictionaries
            
        Returns:
            List of verified facts with confidence scores
        """
        if not facts:
            return []
            
        # Group facts by type
        fact_groups = {"fact": [], "statistic": []}
        for fact in facts:
            fact_type = fact.get("type", "fact")
            fact_groups[fact_type].append(fact)
            
        verified = []
        
        # Process each group
        for fact_type, group_facts in fact_groups.items():
            if not group_facts:
                continue
                
            # Batch facts for verification
            batch_size = 10
            for i in range(0, len(group_facts), batch_size):
                batch = group_facts[i:i+batch_size]
                verified_batch = await self._verify_fact_batch(batch)
                verified.extend(verified_batch)
                
        return verified
        
    async def _verify_fact_batch(self, fact_batch: List[Dict]) -> List[Dict]:
        """Verify a batch of facts."""
        
        # Prepare facts for LLM
        facts_text = "\n".join([
            f"{i+1}. {f['fact']} (Source: {f['source']})"
            for i, f in enumerate(fact_batch)
        ])
        
        system_prompt = """You are a fact verification expert. Analyze the given facts and:
1. Identify similar or duplicate claims
2. Detect contradictions
3. Assign confidence scores (0-100) based on:
   - Number of sources supporting the claim
   - Specificity and detail
   - Presence of data/numbers
   - Absence of contradictions

Respond in JSON format:
{
    "verified_facts": [
        {
            "fact": "the main claim",
            "confidence_score": 85,
            "supporting_sources": 3,
            "has_contradiction": false,
            "notes": "explanation"
        }
    ]
}"""

        user_prompt = f"""Facts to verify:

{facts_text}

Please analyze these facts and provide confidence scores."""

        try:
            response = await self._call_llm(system_prompt, user_prompt)
            result = json.loads(response)
            return result.get("verified_facts", [])
            
        except Exception as e:
            self.logger.error(f"Fact verification failed: {e}")
            
            # Fallback: simple source counting
            return [
                {
                    "fact": f["fact"],
                    "confidence_score": 50,
                    "supporting_sources": 1,
                    "has_contradiction": False,
                    "source": f["source"]
                }
                for f in fact_batch
            ]
            
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
            temperature=0.2,
            max_tokens=2000
        )
        return response.choices[0].message.content
