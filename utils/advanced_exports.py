"""
Advanced Export Features
Provides citations export, mind-map generation, and raw data export.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class AdvancedExporter:
    """Advanced export functionality for research reports."""
    
    def __init__(self, export_dir: str = "exports"):
        """
        Initialize exporter.
        
        Args:
            export_dir: Directory for exported files
        """
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(exist_ok=True)
    
    def export_citations(
        self,
        sources: List[Dict[str, Any]],
        format: str = "apa",
        filename: str = None
    ) -> str:
        """
        Export citations in various formats.
        
        Args:
            sources: List of source dictionaries
            format: Citation format (apa, mla, chicago, bibtex)
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to exported file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"citations_{format}_{timestamp}.txt"
        
        filepath = self.export_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Citations ({format.upper()} Format)\n")
            f.write("=" * 60 + "\n\n")
            
            for i, source in enumerate(sources, 1):
                citation = self._format_citation(source, format)
                f.write(f"{i}. {citation}\n\n")
        
        logger.info(f"Citations exported: {filepath}")
        return str(filepath)
    
    def _format_citation(self, source: Dict[str, Any], format: str) -> str:
        """Format single citation."""
        title = source.get("title", "Untitled")
        url = source.get("url", "")
        date = source.get("date", datetime.now().strftime("%Y-%m-%d"))
        author = source.get("author", "Unknown")
        
        if format == "apa":
            # APA 7th Edition
            return f"{author}. ({date}). {title}. Retrieved from {url}"
        
        elif format == "mla":
            # MLA 9th Edition
            return f'{author}. "{title}." Web. {date}. <{url}>.'
        
        elif format == "chicago":
            # Chicago Manual of Style
            return f'{author}. "{title}." Accessed {date}. {url}.'
        
        elif format == "bibtex":
            # BibTeX format
            key = title.lower().replace(" ", "_")[:20]
            return f"""@misc{{{key},
    author = {{{author}}},
    title = {{{title}}},
    year = {{{date[:4]}}},
    url = {{{url}}},
    note = {{Accessed: {date}}}
}}"""
        
        else:
            return f"{author}. {title}. {url}. Accessed {date}."
    
    def export_mindmap(
        self,
        report: Dict[str, Any],
        filename: str = None
    ) -> str:
        """
        Export research as mind-map (text-based tree structure).
        
        Args:
            report: Research report dictionary
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mindmap_{timestamp}.txt"
        
        filepath = self.export_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            query = report.get("query", "Research Query")
            f.write(f"Mind Map: {query}\n")
            f.write("=" * 60 + "\n\n")
            
            # Main topic
            f.write(f"📌 {query}\n")
            
            # Key points from outline
            outline = report.get("research_outline", {})
            if isinstance(outline, dict):
                for section, points in outline.items():
                    f.write(f"\n  ├─ {section}\n")
                    
                    if isinstance(points, list):
                        for point in points:
                            f.write(f"  │  ├─ {point}\n")
                    elif isinstance(points, str):
                        f.write(f"  │  └─ {points}\n")
            
            # Sources
            sources = report.get("sources", [])
            if sources:
                f.write(f"\n  └─ Sources ({len(sources)})\n")
                for source in sources[:5]:  # Top 5 sources
                    title = source.get("title", "Unknown")
                    f.write(f"     ├─ {title}\n")
        
        logger.info(f"Mind-map exported: {filepath}")
        return str(filepath)
    
    def export_raw_data(
        self,
        report: Dict[str, Any],
        filename: str = None
    ) -> str:
        """
        Export complete raw data as JSON.
        
        Args:
            report: Complete research report
            filename: Output filename
            
        Returns:
            Path to exported file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"raw_data_{timestamp}.json"
        
        filepath = self.export_dir / filename
        
        # Prepare export data
        export_data = {
            "export_info": {
                "timestamp": datetime.now().isoformat(),
                "version": "2.0"
            },
            "research": report
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Raw data exported: {filepath}")
        return str(filepath)
    
    def export_markdown_enhanced(
        self,
        report: Dict[str, Any],
        filename: str = None,
        include_metadata: bool = True
    ) -> str:
        """
        Export enhanced Markdown with table of contents and metadata.
        
        Args:
            report: Research report
            filename: Output filename
            include_metadata: Include metadata section
            
        Returns:
            Path to exported file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_enhanced_{timestamp}.md"
        
        filepath = self.export_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            # Title
            query = report.get("query", "Research Report")
            f.write(f"# {query}\n\n")
            
            # Metadata
            if include_metadata:
                f.write("---\n\n")
                f.write("## Document Information\n\n")
                f.write(f"- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"- **Research Mode:** {report.get('mode', 'standard').capitalize()}\n")
                f.write(f"- **Sources:** {len(report.get('sources', []))}\n")
                f.write(f"- **Word Count:** {len(report.get('final_report', '').split())}\n\n")
                f.write("---\n\n")
            
            # Table of contents
            f.write("## Table of Contents\n\n")
            outline = report.get("research_outline", {})
            if isinstance(outline, dict):
                for i, section in enumerate(outline.keys(), 1):
                    f.write(f"{i}. [{section}](#{section.lower().replace(' ', '-')})\n")
            f.write("\n---\n\n")
            
            # Main content
            final_report = report.get("final_report", "")
            f.write(final_report)
            f.write("\n\n---\n\n")
            
            # Sources section
            sources = report.get("sources", [])
            if sources:
                f.write("## Sources\n\n")
                for i, source in enumerate(sources, 1):
                    title = source.get("title", "Untitled")
                    url = source.get("url", "")
                    snippet = source.get("snippet", "")
                    
                    f.write(f"### [{i}] {title}\n\n")
                    f.write(f"- **URL:** {url}\n")
                    if snippet:
                        f.write(f"- **Excerpt:** {snippet[:200]}...\n")
                    f.write("\n")
        
        logger.info(f"Enhanced Markdown exported: {filepath}")
        return str(filepath)
    
    def export_all_formats(
        self,
        report: Dict[str, Any],
        base_filename: str = None
    ) -> Dict[str, str]:
        """
        Export report in all available formats.
        
        Args:
            report: Research report
            base_filename: Base name for files
            
        Returns:
            Dictionary of format -> filepath
        """
        if not base_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"report_{timestamp}"
        
        exports = {}
        
        try:
            # Citations (multiple formats)
            sources = report.get("sources", [])
            for fmt in ["apa", "mla", "chicago", "bibtex"]:
                try:
                    path = self.export_citations(
                        sources,
                        format=fmt,
                        filename=f"{base_filename}_citations_{fmt}.txt"
                    )
                    exports[f"citations_{fmt}"] = path
                except Exception as e:
                    logger.error(f"Citation export failed ({fmt}): {e}")
            
            # Mind-map
            try:
                path = self.export_mindmap(
                    report,
                    filename=f"{base_filename}_mindmap.txt"
                )
                exports["mindmap"] = path
            except Exception as e:
                logger.error(f"Mind-map export failed: {e}")
            
            # Raw data
            try:
                path = self.export_raw_data(
                    report,
                    filename=f"{base_filename}_raw.json"
                )
                exports["raw_data"] = path
            except Exception as e:
                logger.error(f"Raw data export failed: {e}")
            
            # Enhanced Markdown
            try:
                path = self.export_markdown_enhanced(
                    report,
                    filename=f"{base_filename}_enhanced.md"
                )
                exports["markdown_enhanced"] = path
            except Exception as e:
                logger.error(f"Enhanced Markdown export failed: {e}")
        
        except Exception as e:
            logger.error(f"Export all formats failed: {e}")
        
        return exports


# Singleton instance
_exporter = None


def get_exporter() -> AdvancedExporter:
    """Get singleton exporter instance."""
    global _exporter
    if _exporter is None:
        _exporter = AdvancedExporter()
    return _exporter
