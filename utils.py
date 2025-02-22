from rich.console import Console
from rich.panel import Panel

console = Console()

def clear_screen():
    """Clear the terminal screen."""
    console.clear()

def display_error(message):
    """Display an error message."""
    console.print(Panel.fit(
        f"[bold red]{message}[/bold red]",
        border_style="red"
    ))

def display_success(message):
    """Display a success message."""
    console.print(Panel.fit(
        f"[bold green]{message}[/bold green]",
        border_style="green"
    ))

def format_choices(choices):
    """Format a list of choices for display."""
    return "\n".join(f"{idx + 1}. {choice}" for idx, choice in enumerate(choices))
