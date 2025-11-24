"""
Chart Generator for Deep Research Mode
Creates visualizations including source distribution, topic coverage, and timelines.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class ChartGenerator:
    """Generate charts and visualizations for research reports."""
    
    def __init__(self, export_dir: str = "exports/charts"):
        """
        Initialize chart generator.
        
        Args:
            export_dir: Directory for chart exports
        """
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
        # Set style
        plt.style.use('dark_background')
    
    def generate_source_distribution_chart(
        self,
        sources: List[Dict[str, Any]],
        filename: str = None
    ) -> str:
        """
        Generate pie chart of source types.
        
        Args:
            sources: List of source dictionaries
            filename: Output filename
            
        Returns:
            Path to chart file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"source_distribution_{timestamp}.png"
        
        filepath = self.export_dir / filename
        
        # Categorize sources
        categories = {}
        for source in sources:
            url = source.get("url", "").lower()
            
            if "wikipedia" in url:
                cat = "Wikipedia"
            elif any(domain in url for domain in [".edu", ".gov"]):
                cat = "Academic/Official"
            elif any(domain in url for domain in [".org"]):
                cat = "Organization"
            elif any(domain in url for domain in ["arxiv", "scholar", "research"]):
                cat = "Research"
            else:
                cat = "General Web"
            
            categories[cat] = categories.get(cat, 0) + 1
        
        # Create chart
        fig, ax = plt.subplots(figsize=(10, 8))
        
        colors = ['#007acc', '#00a3cc', '#00c9cc', '#00e6cc', '#00ffcc']
        wedges, texts, autotexts = ax.pie(
            categories.values(),
            labels=categories.keys(),
            autopct='%1.1f%%',
            startangle=90,
            colors=colors
        )
        
        # Styling
        for text in texts:
            text.set_color('white')
            text.set_fontsize(12)
        
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontsize(10)
            autotext.set_weight('bold')
        
        ax.set_title('Source Distribution by Type', fontsize=16, pad=20)
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='#1e1e1e')
        plt.close()
        
        logger.info(f"Source distribution chart saved: {filepath}")
        return str(filepath)
    
    def generate_topic_coverage_chart(
        self,
        outline: Dict[str, Any],
        filename: str = None
    ) -> str:
        """
        Generate bar chart of topic coverage.
        
        Args:
            outline: Research outline dictionary
            filename: Output filename
            
        Returns:
            Path to chart file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"topic_coverage_{timestamp}.png"
        
        filepath = self.export_dir / filename
        
        # Extract topics and point counts
        topics = []
        point_counts = []
        
        if isinstance(outline, dict):
            for topic, points in outline.items():
                topics.append(topic[:30])  # Truncate long names
                
                if isinstance(points, list):
                    point_counts.append(len(points))
                else:
                    point_counts.append(1)
        
        if not topics:
            logger.warning("No topics found for coverage chart")
            return None
        
        # Create chart
        fig, ax = plt.subplots(figsize=(12, 6))
        
        bars = ax.barh(topics, point_counts, color='#007acc')
        
        # Add value labels
        for i, (bar, count) in enumerate(zip(bars, point_counts)):
            width = bar.get_width()
            ax.text(
                width + 0.1,
                bar.get_y() + bar.get_height() / 2,
                f'{count}',
                ha='left',
                va='center',
                fontsize=10,
                color='white'
            )
        
        ax.set_xlabel('Number of Key Points', fontsize=12)
        ax.set_title('Topic Coverage Analysis', fontsize=16, pad=20)
        ax.set_xlim(0, max(point_counts) * 1.2)
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='#1e1e1e')
        plt.close()
        
        logger.info(f"Topic coverage chart saved: {filepath}")
        return str(filepath)
    
    def generate_word_count_chart(
        self,
        sections: Dict[str, str],
        filename: str = None
    ) -> str:
        """
        Generate bar chart of word counts per section.
        
        Args:
            sections: Dictionary of section_name -> content
            filename: Output filename
            
        Returns:
            Path to chart file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"word_count_{timestamp}.png"
        
        filepath = self.export_dir / filename
        
        # Count words per section
        section_names = []
        word_counts = []
        
        for name, content in sections.items():
            section_names.append(name[:30])
            word_counts.append(len(content.split()))
        
        if not section_names:
            logger.warning("No sections found for word count chart")
            return None
        
        # Create chart
        fig, ax = plt.subplots(figsize=(12, 6))
        
        bars = ax.bar(range(len(section_names)), word_counts, color='#00c9cc')
        
        # Add value labels
        for bar, count in zip(bars, word_counts):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                height + max(word_counts) * 0.01,
                f'{count}',
                ha='center',
                va='bottom',
                fontsize=10,
                color='white'
            )
        
        ax.set_xticks(range(len(section_names)))
        ax.set_xticklabels(section_names, rotation=45, ha='right')
        ax.set_ylabel('Word Count', fontsize=12)
        ax.set_title('Section Word Count Distribution', fontsize=16, pad=20)
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='#1e1e1e')
        plt.close()
        
        logger.info(f"Word count chart saved: {filepath}")
        return str(filepath)
    
    def generate_research_summary_chart(
        self,
        report: Dict[str, Any],
        filename: str = None
    ) -> str:
        """
        Generate comprehensive summary chart with key metrics.
        
        Args:
            report: Complete research report
            filename: Output filename
            
        Returns:
            Path to chart file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"research_summary_{timestamp}.png"
        
        filepath = self.export_dir / filename
        
        # Extract metrics
        sources_count = len(report.get("sources", []))
        word_count = len(report.get("final_report", "").split())
        outline = report.get("research_outline", {})
        topics_count = len(outline) if isinstance(outline, dict) else 0
        mode = report.get("mode", "standard").capitalize()
        
        # Create figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Research Report Summary', fontsize=18, fontweight='bold')
        
        # Chart 1: Key metrics
        metrics = ['Sources', 'Word Count', 'Topics']
        values = [sources_count, word_count / 100, topics_count]  # Scale word count
        
        ax1.barh(metrics, values, color=['#007acc', '#00c9cc', '#00ffcc'])
        ax1.set_title('Key Metrics', fontsize=14)
        ax1.set_xlabel('Count (Word Count / 100)', fontsize=10)
        
        # Chart 2: Mode indicator
        mode_colors = {'Quick': '#ffcc00', 'Standard': '#007acc', 'Deep': '#00ffcc'}
        ax2.text(
            0.5, 0.5,
            f"Research Mode:\n{mode}",
            ha='center',
            va='center',
            fontsize=24,
            fontweight='bold',
            color=mode_colors.get(mode, '#ffffff')
        )
        ax2.set_xlim(0, 1)
        ax2.set_ylim(0, 1)
        ax2.axis('off')
        
        # Chart 3: Source quality indicators (placeholder)
        quality_labels = ['High\nQuality', 'Medium\nQuality', 'General\nWeb']
        quality_counts = [sources_count // 3, sources_count // 3, sources_count // 3]
        
        ax3.pie(
            quality_counts,
            labels=quality_labels,
            autopct='%1.0f%%',
            colors=['#00ffcc', '#00c9cc', '#007acc'],
            startangle=90
        )
        ax3.set_title('Source Quality Distribution (Estimated)', fontsize=14)
        
        # Chart 4: Statistics text
        stats_text = (
            f"Report Statistics\n"
            f"{'=' * 30}\n\n"
            f"Total Sources: {sources_count}\n"
            f"Total Words: {word_count:,}\n"
            f"Topics Covered: {topics_count}\n"
            f"Research Mode: {mode}\n\n"
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        ax4.text(
            0.05, 0.95,
            stats_text,
            ha='left',
            va='top',
            fontsize=11,
            family='monospace',
            color='white'
        )
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0, 1)
        ax4.axis('off')
        
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='#1e1e1e')
        plt.close()
        
        logger.info(f"Research summary chart saved: {filepath}")
        return str(filepath)
    
    def generate_all_charts(
        self,
        report: Dict[str, Any],
        base_filename: str = None
    ) -> Dict[str, str]:
        """
        Generate all available charts for a report.
        
        Args:
            report: Complete research report
            base_filename: Base name for chart files
            
        Returns:
            Dictionary of chart_type -> filepath
        """
        if not base_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"charts_{timestamp}"
        
        charts = {}
        
        try:
            # Source distribution
            sources = report.get("sources", [])
            if sources:
                path = self.generate_source_distribution_chart(
                    sources,
                    filename=f"{base_filename}_sources.png"
                )
                if path:
                    charts["source_distribution"] = path
        except Exception as e:
            logger.error(f"Source distribution chart failed: {e}")
        
        try:
            # Topic coverage
            outline = report.get("research_outline", {})
            if outline:
                path = self.generate_topic_coverage_chart(
                    outline,
                    filename=f"{base_filename}_topics.png"
                )
                if path:
                    charts["topic_coverage"] = path
        except Exception as e:
            logger.error(f"Topic coverage chart failed: {e}")
        
        try:
            # Research summary
            path = self.generate_research_summary_chart(
                report,
                filename=f"{base_filename}_summary.png"
            )
            if path:
                charts["research_summary"] = path
        except Exception as e:
            logger.error(f"Research summary chart failed: {e}")
        
        return charts


# Singleton instance
_generator = None


def get_chart_generator() -> ChartGenerator:
    """Get singleton chart generator instance."""
    global _generator
    if _generator is None:
        _generator = ChartGenerator()
    return _generator
