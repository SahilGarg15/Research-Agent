"""Query Expansion Agent - Breaks down user queries into research sub-topics."""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent
import json


class QueryExpansionAgent(BaseAgent):
    """
    Expands user queries into structured research outlines with sub-topics.
    """
    
    def __init__(self, llm_client, model_name: str = None):
        super().__init__("QueryExpansionAgent", llm_client, model_name)
        
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Expand a research query into sub-topics and research outline.
        
        Args:
            input_data: {
                "query": str - The research topic/question
            }
            
        Returns:
            {
                "original_query": str,
                "expanded_topics": List[str],
                "research_outline": Dict,
                "key_questions": List[str]
            }
        """
        self.validate_input(input_data, ["query"])
        query = input_data["query"]
        
        self.log_progress(f"Expanding query: {query}")
        
        # Create prompt for LLM
        system_prompt = """You are a research planning expert. Your job is to analyze a research topic 
and break it down into comprehensive sub-topics, key questions, and a structured outline.

Provide your response in valid JSON format with the following structure:
{
    "expanded_topics": ["topic1", "topic2", ...],
    "research_outline": {
        "Introduction": ["key point 1", "key point 2"],
        "Section 1 Name": ["key point 1", "key point 2"],
        ...
    },
    "key_questions": ["question 1", "question 2", ...]
}"""

        user_prompt = f"""Research Topic: {query}

Please expand this topic into:
1. 5-8 specific sub-topics to research
2. A structured research outline with sections and key points
3. 5-10 key questions that should be answered

Focus on creating a comprehensive research plan that covers all important dimensions of the topic."""

        # Call LLM
        response = await self._call_llm(system_prompt, user_prompt)
        
        # Parse response
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            # Fallback parsing if JSON is malformed
            self.log_progress("Failed to parse JSON, using fallback", "warning")
            result = self._fallback_parse(response, query)
            
        # Enrich with original query
        result["original_query"] = query
        
        self.log_progress(f"Generated {len(result.get('expanded_topics', []))} sub-topics")
        
        return result
    
    def _create_fallback_response(self) -> str:
        """Create a fallback JSON response when LLM call fails."""
        return '''{
            "expanded_topics": ["Overview and fundamentals", "Technical aspects", "Applications and use cases", "Current state and developments", "Future implications"],
            "research_outline": {
                "Introduction": ["Background and context", "Importance and relevance"],
                "Main Content": ["Key concepts", "Technical details", "Real-world applications"],
                "Analysis": ["Current trends", "Challenges and opportunities"],
                "Conclusion": ["Summary of findings", "Future outlook"]
            },
            "key_questions": ["What is the topic about?", "How does it work?", "What are its applications?", "What are the current developments?", "What does the future hold?"]
        }'''
        
    async def _call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """Call the LLM with prompts."""
        if not self.llm_client:
            raise ValueError("LLM client not configured")
            
        try:
            # Try OpenAI-compatible API (works for Groq, DeepSeek, OpenAI, etc.)
            response = await self.llm_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content
            
        except Exception as e:
            self.logger.error(f"LLM call failed: {e}")
            # Return fallback result instead of raising
            return self._create_fallback_response()
            
    def _fallback_parse(self, response: str, query: str) -> Dict[str, Any]:
        """Fallback parser if JSON parsing fails."""
        # Simple extraction logic
        lines = response.split('\n')
        
        expanded_topics = []
        key_questions = []
        research_outline = {"Introduction": [], "Main Content": [], "Conclusion": []}
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Extract list items
                clean_line = line.lstrip('0123456789.-•) ').strip()
                if len(clean_line) > 10:
                    if '?' in clean_line:
                        key_questions.append(clean_line)
                    else:
                        expanded_topics.append(clean_line)
                        
        return {
            "expanded_topics": expanded_topics[:8] or [query],
            "research_outline": research_outline,
            "key_questions": key_questions[:10] or [f"What is {query}?"]
        }
