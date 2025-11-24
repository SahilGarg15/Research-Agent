"""Utility functions for logging and monitoring."""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table
import config

console = Console()


def setup_logger(
    name: str = "ResearchAgent",
    log_file: Optional[Path] = None,
    level: str = "INFO"
) -> logging.Logger:
    """
    Set up a logger with both file and console handlers.
    
    Args:
        name: Logger name
        log_file: Path to log file
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with Rich formatting
    console_handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        tracebacks_show_locals=True
    )
    console_handler.setLevel(getattr(logging, level.upper()))
    console_formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file is None:
        log_file = config.LOG_FILE
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger


def log_agent_start(agent_name: str, task: str):
    """Log the start of an agent task with visual formatting."""
    console.print(Panel(
        f"[bold cyan]{agent_name}[/bold cyan]\n[white]{task}[/white]",
        title="🤖 Agent Started",
        border_style="cyan"
    ))


def log_agent_complete(agent_name: str, summary: str):
    """Log the completion of an agent task."""
    console.print(Panel(
        f"[bold green]{agent_name}[/bold green]\n[white]{summary}[/white]",
        title="✅ Agent Completed",
        border_style="green"
    ))


def log_agent_error(agent_name: str, error: str):
    """Log an agent error."""
    console.print(Panel(
        f"[bold red]{agent_name}[/bold red]\n[white]{error}[/white]",
        title="❌ Agent Error",
        border_style="red"
    ))


def create_progress_tracker():
    """Create a Rich progress tracker for multi-step tasks."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    )


def display_research_summary(data: dict):
    """Display a formatted summary of research results."""
    table = Table(title="📊 Research Summary", show_header=True, header_style="bold magenta")
    
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    
    for key, value in data.items():
        table.add_row(key, str(value))
    
    console.print(table)


def display_sources(sources: list):
    """Display a formatted list of sources."""
    table = Table(title="🔗 Sources", show_header=True, header_style="bold blue")
    
    table.add_column("#", style="cyan", width=4)
    table.add_column("Title", style="white")
    table.add_column("URL", style="blue", overflow="fold")
    table.add_column("Confidence", style="green", justify="right")
    
    for idx, source in enumerate(sources, 1):
        table.add_row(
            str(idx),
            source.get("title", "Unknown"),
            source.get("url", ""),
            f"{source.get('confidence', 0)}%"
        )
    
    console.print(table)


class AgentLogger:
    """Context manager for agent logging with progress tracking."""
    
    def __init__(self, agent_name: str, task_description: str):
        self.agent_name = agent_name
        self.task_description = task_description
        self.start_time = None
        
    def __enter__(self):
        self.start_time = datetime.now()
        log_agent_start(self.agent_name, self.task_description)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            log_agent_complete(
                self.agent_name,
                f"Task completed in {elapsed:.2f}s"
            )
        else:
            log_agent_error(
                self.agent_name,
                f"Task failed after {elapsed:.2f}s: {exc_val}"
            )
        
        return False  # Don't suppress exceptions
