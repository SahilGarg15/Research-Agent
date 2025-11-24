"""Writer Agent - Generates structured research reports."""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent
import json
from datetime import datetime


class WriterAgent(BaseAgent):
    """
    Compiles verified information into a structured research report.
    """
    
    def __init__(self, llm_client, model_name: str = None):
        super().__init__("WriterAgent", llm_client, model_name)
        
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a structured research report.
        
        Args:
            input_data: {
                "original_query": str,
                "research_outline": Dict,
                "verified_facts": List[Dict],
                "summaries": List[Dict]
            }
            
        Returns:
            {
                "report": str - Full research report,
                "sections": Dict[str, str] - Report by section,
                "word_count": int,
                "metadata": Dict
            }
        """
        self.validate_input(
            input_data,
            ["original_query", "research_outline", "verified_facts"]
        )
        
        query = input_data["original_query"]
        outline = input_data["research_outline"]
        facts = input_data["verified_facts"]
        summaries = input_data.get("summaries", [])
        
        self.log_progress(f"Writing research report for: {query}")
        
        # Generate each section
        sections = {}
        
        # Executive Summary
        sections["Executive Summary"] = await self._write_executive_summary(
            query, facts
        )
        
        # Introduction
        sections["Introduction"] = await self._write_introduction(query, outline)
        
        # Main content sections
        for section_name, section_points in outline.items():
            if section_name not in ["Introduction", "Conclusion"]:
                sections[section_name] = await self._write_section(
                    section_name, section_points, facts, summaries
                )
                
        # Conclusion
        sections["Conclusion"] = await self._write_conclusion(query, facts)
        
        # Compile full report
        full_report = self._compile_report(query, sections)
        
        word_count = len(full_report.split())
        
        self.log_progress(f"Generated {word_count} word report with {len(sections)} sections")
        
        return {
            "report": full_report,
            "sections": sections,
            "word_count": word_count,
            "metadata": {
                "title": query,
                "date": datetime.now().isoformat(),
                "sections_count": len(sections),
                "sources_count": len(summaries)
            }
        }
        
    async def _write_executive_summary(
        self,
        query: str,
        facts: List[Dict]
    ) -> str:
        """Generate executive summary."""
        
        top_facts = sorted(
            facts,
            key=lambda x: x.get("confidence_score", 0),
            reverse=True
        )[:10]
        
        facts_text = "\n".join([
            f"- {f.get('fact', '')}"
            for f in top_facts
        ])
        
        prompt = f"""Write a concise executive summary (150-200 words) for a research report on:
"{query}"

Key findings:
{facts_text}

The summary should highlight the most important insights and findings."""

        return await self._generate_content(prompt)
        
    async def _write_introduction(self, query: str, outline: Dict) -> str:
        """Generate introduction."""
        
        sections_list = ", ".join(outline.keys())
        
        prompt = f"""Write an introduction (200-300 words) for a research report on:
"{query}"

The report covers the following topics: {sections_list}

The introduction should provide context, explain importance, and outline the report structure."""

        return await self._generate_content(prompt)
        
    async def _write_section(
        self,
        section_name: str,
        section_points: List[str],
        facts: List[Dict],
        summaries: List[Dict]
    ) -> str:
        """Generate a content section."""
        
        # Filter relevant facts for this section
        relevant_facts = [
            f for f in facts
            if any(point.lower() in f.get('fact', '').lower() for point in section_points)
        ][:15]
        
        if not relevant_facts:
            relevant_facts = facts[:10]  # Use general facts
            
        facts_text = "\n".join([
            f"- {f.get('fact', '')} (confidence: {f.get('confidence_score', 0)}%)"
            for f in relevant_facts
        ])
        
        points_text = "\n".join([f"- {p}" for p in section_points])
        
        prompt = f"""Write a detailed section (300-500 words) for:
Section: {section_name}

Key points to cover:
{points_text}

Available facts and data:
{facts_text}

Write in a professional, informative style with clear structure and data-driven insights."""

        return await self._generate_content(prompt)
        
    async def _write_conclusion(self, query: str, facts: List[Dict]) -> str:
        """Generate conclusion."""
        
        high_confidence_facts = [
            f for f in facts
            if f.get("confidence_score", 0) >= 80
        ][:8]
        
        facts_text = "\n".join([
            f"- {f.get('fact', '')}"
            for f in high_confidence_facts
        ])
        
        prompt = f"""Write a conclusion (200-300 words) for a research report on:
"{query}"

Key verified findings:
{facts_text}

The conclusion should synthesize findings, highlight implications, and suggest future directions."""

        return await self._generate_content(prompt)
        
    async def _generate_content(self, prompt: str) -> str:
        """Generate content using LLM."""
        
        system_prompt = """You are an expert research writer. Create clear, well-structured, 
academic-style content based on the provided information. Use proper paragraphs, transitions,
and maintain a professional tone. Focus on facts and insights."""

        try:
            response = await self._call_llm(system_prompt, prompt)
            return response.strip()
            
        except Exception as e:
            self.logger.error(f"Content generation failed: {e}")
            return f"[Content generation failed for this section]"
            
    def _compile_report(self, title: str, sections: Dict[str, str]) -> str:
        """Compile all sections into final report."""
        
        report_parts = [
            f"# {title}",
            f"\n*Research Report Generated: {datetime.now().strftime('%B %d, %Y')}*\n",
            "---\n"
        ]
        
        for section_name, content in sections.items():
            report_parts.append(f"## {section_name}\n")
            report_parts.append(f"{content}\n")
            
        return "\n".join(report_parts)
        
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
            temperature=0.7,
            max_tokens=1500
        )
        return response.choices[0].message.content
