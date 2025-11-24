"""
Research Modes System
Supports Quick, Standard, and Deep research modes with different configurations.
"""

from enum import Enum
from typing import Dict, Any
from dataclasses import dataclass


class ResearchMode(str, Enum):
    """Available research modes."""
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


@dataclass
class ModeConfig:
    """Configuration for a research mode."""
    name: str
    max_sources: int
    max_words: int
    search_rounds: int
    fact_checking_level: str
    citation_detail: str
    estimated_time: str
    description: str
    premium_only: bool = False


class ResearchModeManager:
    """Manages research mode configurations."""
    
    MODES = {
        ResearchMode.QUICK: ModeConfig(
            name="Quick Summary",
            max_sources=2,
            max_words=500,
            search_rounds=1,
            fact_checking_level="basic",
            citation_detail="minimal",
            estimated_time="30-60 seconds",
            description="Fast overview with 1-2 sources. Perfect for quick answers.",
            premium_only=False
        ),
        ResearchMode.STANDARD: ModeConfig(
            name="Standard Research",
            max_sources=5,
            max_words=2000,
            search_rounds=1,
            fact_checking_level="standard",
            citation_detail="standard",
            estimated_time="2-3 minutes",
            description="Balanced research with 3-5 sources and concise multi-section answer.",
            premium_only=False
        ),
        ResearchMode.DEEP: ModeConfig(
            name="Deep Research",
            max_sources=15,
            max_words=5000,
            search_rounds=3,
            fact_checking_level="advanced",
            citation_detail="comprehensive",
            estimated_time="5-10 minutes",
            description="Comprehensive research with 10-15 sources, multi-round validation, charts, and PDF export.",
            premium_only=True
        )
    }
    
    @classmethod
    def get_config(cls, mode: ResearchMode) -> ModeConfig:
        """Get configuration for a research mode."""
        return cls.MODES[mode]
    
    @classmethod
    def is_available(cls, mode: ResearchMode, tier: str) -> bool:
        """Check if mode is available for the user's tier."""
        config = cls.get_config(mode)
        
        if config.premium_only and tier != "premium":
            return False
        
        return True
    
    @classmethod
    def get_available_modes(cls, tier: str) -> list:
        """Get list of available modes for a tier."""
        available = []
        
        for mode, config in cls.MODES.items():
            if cls.is_available(mode, tier):
                available.append({
                    "mode": mode,
                    "name": config.name,
                    "description": config.description,
                    "estimated_time": config.estimated_time,
                    "max_sources": config.max_sources,
                    "max_words": config.max_words
                })
        
        return available
    
    @classmethod
    def display_modes(cls, tier: str):
        """Display available modes in a formatted way."""
        print("\n" + "="*60)
        print(" "*18 + "RESEARCH MODES")
        print("="*60 + "\n")
        
        for mode, config in cls.MODES.items():
            available = cls.is_available(mode, tier)
            
            status = "✓" if available else "🔒 Premium"
            
            print(f"{status} {config.name.upper()}")
            print(f"   {config.description}")
            print(f"   Time: {config.estimated_time} | Sources: {config.max_sources} | Words: {config.max_words}")
            
            if not available:
                print(f"   → Upgrade to Premium to unlock")
            
            print()
        
        print("="*60 + "\n")


def get_mode_limits(mode: ResearchMode, tier: str) -> Dict[str, Any]:
    """
    Get research limits for a specific mode and tier.
    
    Returns:
        Dictionary with limits for the research pipeline
    """
    config = ResearchModeManager.get_config(mode)
    
    # Check if user can access this mode
    if config.premium_only and tier != "premium":
        raise ValueError(f"{config.name} is only available for Premium users")
    
    return {
        "mode": mode.value,
        "max_sources": config.max_sources,
        "max_words": config.max_words,
        "search_rounds": config.search_rounds,
        "fact_checking_level": config.fact_checking_level,
        "citation_detail": config.citation_detail,
        "enable_charts": mode == ResearchMode.DEEP,
        "enable_export": mode == ResearchMode.DEEP,
        "multi_round_search": config.search_rounds > 1
    }
