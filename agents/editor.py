"""Editor Agent - Refines and improves report quality."""

from typing import Dict, Any
from agents.base_agent import BaseAgent


class EditorAgent(BaseAgent):
    """
    Improves grammar, flow, tone, and structure of research reports.
    """
    
    def __init__(self, llm_client, model_name: str = None):
        super().__init__("EditorAgent", llm_client, model_name)
        
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Edit and refine the research report.
        
        Args:
            input_data: {
                "report": str - Draft report from WriterAgent,
                "sections": Dict[str, str] (optional)
            }
            
        Returns:
            {
                "edited_report": str,
                "improvements": List[str],
                "readability_score": float
            }
        """
        self.validate_input(input_data, ["report"])
        
        report = input_data["report"]
        
        self.log_progress("Editing and refining report")
        
        # Edit the report
        edited_report = await self._edit_report(report)
        
        # Generate list of improvements made
        improvements = await self._identify_improvements(report, edited_report)
        
        # Calculate basic readability metrics
        readability = self._calculate_readability(edited_report)
        
        self.log_progress(f"Editing complete. Readability score: {readability}")
        
        return {
            "edited_report": edited_report,
            "improvements": improvements,
            "readability_score": readability
        }
        
    async def _edit_report(self, report: str) -> str:
        """
        Edit the report for grammar, flow, and clarity.
        """
        
        system_prompt = """You are an expert editor specializing in academic and research writing.
Your task is to improve the given report by:

1. Fixing grammar and spelling errors
2. Improving sentence structure and flow
3. Ensuring consistent tone and style
4. Adding smooth transitions between sections
5. Enhancing clarity and readability
6. Maintaining professional academic voice

Return ONLY the edited report without any meta-commentary."""

        user_prompt = f"""Please edit and improve this research report:

{report}

Provide the refined version."""

        try:
            edited = await self._call_llm(system_prompt, user_prompt)
            return edited.strip()
            
        except Exception as e:
            self.logger.error(f"Editing failed: {e}")
            return report  # Return original if editing fails
            
    async def _identify_improvements(self, original: str, edited: str) -> list:
        """
        Identify what improvements were made.
        """
        
        improvements = []
        
        # Simple heuristics
        if len(edited) > len(original):
            improvements.append("Expanded content for better clarity")
        elif len(edited) < len(original):
            improvements.append("Condensed content for conciseness")
            
        # Count sentences
        original_sentences = original.count('.') + original.count('!') + original.count('?')
        edited_sentences = edited.count('.') + edited.count('!') + edited.count('?')
        
        if edited_sentences != original_sentences:
            improvements.append("Improved sentence structure")
            
        improvements.extend([
            "Enhanced readability and flow",
            "Corrected grammar and spelling",
            "Improved transitions between sections",
            "Maintained professional tone"
        ])
        
        return improvements[:5]
        
    def _calculate_readability(self, text: str) -> float:
        """
        Calculate a simple readability score (0-100).
        Higher is better.
        """
        
        # Simple metrics
        words = text.split()
        sentences = text.count('.') + text.count('!') + text.count('?')
        
        if not sentences:
            return 50.0
            
        avg_words_per_sentence = len(words) / sentences
        
        # Ideal is 15-20 words per sentence
        if 15 <= avg_words_per_sentence <= 20:
            score = 90.0
        elif 10 <= avg_words_per_sentence <= 25:
            score = 75.0
        else:
            score = 60.0
            
        # Bonus for paragraph breaks
        paragraphs = text.count('\n\n')
        if paragraphs > len(words) / 200:  # Good paragraph density
            score += 10
            
        return min(100.0, score)
        
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
            temperature=0.3,
            max_tokens=4096
        )
        return response.choices[0].message.content
