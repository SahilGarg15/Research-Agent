"""Citation Agent - Formats references and adds citations."""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from datetime import datetime
import re


class CitationAgent(BaseAgent):
    """
    Formats sources in various citation styles and adds inline citations.
    """
    
    def __init__(self, llm_client=None, model_name: str = None):
        super().__init__("CitationAgent", llm_client, model_name)
        
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate citations and add them to the report.
        
        Args:
            input_data: {
                "edited_report": str,
                "summaries": List[Dict] - Source summaries,
                "citation_style": str - "APA", "MLA", or "IEEE"
            }
            
        Returns:
            {
                "report_with_citations": str,
                "references": List[str],
                "citations_count": int
            }
        """
        self.validate_input(input_data, ["edited_report", "summaries"])
        
        report = input_data["edited_report"]
        summaries = input_data["summaries"]
        style = input_data.get("citation_style", "APA")
        
        self.log_progress(f"Generating citations in {style} format")
        
        # Generate formatted citations
        references = self._format_citations(summaries, style)
        
        # Add inline citations to report
        report_with_citations = self._add_inline_citations(report, summaries, style)
        
        # Append references section
        final_report = self._append_references(report_with_citations, references)
        
        self.log_progress(f"Added {len(references)} citations")
        
        return {
            "report_with_citations": final_report,
            "references": references,
            "citations_count": len(references),
            "citation_style": style
        }
        
    def _format_citations(self, summaries: List[Dict], style: str) -> List[str]:
        """
        Format citations based on style guide.
        """
        
        references = []
        
        for idx, summary in enumerate(summaries, 1):
            url = summary.get("url", "")
            title = summary.get("title", "Unknown Title")
            
            # Extract domain name as author
            try:
                domain = re.search(r'https?://(?:www\.)?([^/]+)', url)
                author = domain.group(1) if domain else "Unknown"
            except:
                author = "Unknown"
                
            # Get current date as access date
            access_date = datetime.now().strftime("%B %d, %Y")
            
            if style == "APA":
                citation = f"{author}. (n.d.). {title}. Retrieved {access_date}, from {url}"
            elif style == "MLA":
                citation = f'"{title}." {author}, {access_date}, {url}.'
            elif style == "IEEE":
                citation = f'[{idx}] {author}, "{title}," {url} (accessed {access_date}).'
            else:
                citation = f"{title}. {url}"
                
            references.append(citation)
            
        return references
        
    def _add_inline_citations(
        self,
        report: str,
        summaries: List[Dict],
        style: str
    ) -> str:
        """
        Add inline citations to the report.
        """
        
        # For now, add simple numbered citations at end of paragraphs
        # A more sophisticated approach would match content to sources
        
        lines = report.split('\n')
        modified_lines = []
        citation_idx = 1
        
        for line in lines:
            # Add citation to paragraphs (lines with substantial text)
            if len(line.strip()) > 100 and not line.startswith('#'):
                # Check if line already has a citation
                if not re.search(r'\[\d+\]|\([^)]+,\s*\d{4}\)', line):
                    if style == "IEEE":
                        line = f"{line.rstrip('.')}.[{citation_idx}]"
                    else:
                        line = f"{line.rstrip('.')}."
                    
                    citation_idx = min(citation_idx + 1, len(summaries))
                    
            modified_lines.append(line)
            
        return '\n'.join(modified_lines)
        
    def _append_references(self, report: str, references: List[str]) -> str:
        """
        Append references section to report.
        """
        
        if not references:
            return report
            
        references_section = "\n\n---\n\n## References\n\n"
        references_section += "\n\n".join(references)
        
        return report + references_section
