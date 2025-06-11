"""Console utilities for BPM.

This module provides utilities for consistent console output formatting.
"""

from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme
import sys

# Define custom theme
theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red",
    "success": "green",
})

class BPMConsole(Console):
    """Custom console for BPM with consistent formatting."""
    
    def __init__(self):
        """Initialize console with custom theme."""
        super().__init__(theme=theme)
    
    def info(self, message: str) -> None:
        """Print info message.
        
        Args:
            message: Message to print
        """
        self.print(f"[info]{message}[/info]")
    
    def warning(self, message: str) -> None:
        """Print warning message.
        
        Args:
            message: Message to print
        """
        self.print(f"[warning]⚠️ {message}[/warning]")
    
    def error(self, message: str) -> None:
        """Print error message.
        
        Args:
            message: Message to print
        """
        self.print(f"[error]❌ {message}[/error]")
        # sys.exit(1)
    
    def success(self, message: str) -> None:
        """Print success message.
        
        Args:
            message: Message to print
        """
        self.print(f"[success]✅{message}[/success]")
    
    def panel(self, message: str, title: str | None = None, style: str = "info") -> None:
        """Print message in a panel.
        
        Args:
            message: Message to print
            title: Optional panel title
            style: Panel style (info, warning, error, success)
        """
        self.print(Panel(message, title=title, border_style=style))
        
    def section(self, title: str, subtitle: str | None = None) -> None:
        """Print a section header.
        
        Args:
            title: Section title
            subtitle: Optional section subtitle
        """
        if subtitle:
            self.print(f"\n[bold blue]{title}[/bold blue] - {subtitle}")
        else:
            self.print(f"\n[bold blue]{title}[/bold blue]") 