"""Initialization command for ptracker."""

from pathlib import Path
import typer
from rich.console import Console
from tinydb import TinyDB
from ptracker.config import ConfigManager, DEFAULT_CONFIG

console = Console()


def get_data_dir() -> Path:
    """Get ptracker data directory path.
    
    Returns:
        Path to ~/.ptracker/
    """
    return Path.home() / ".ptracker"


def init_command():
    """Initialize ptracker data directory and files."""
    data_dir = get_data_dir()
    
    # Check if already initialized
    if data_dir.exists() and (data_dir / "config.toml").exists():
        console.print(f"[yellow]⚠️  ptracker is already initialized at {data_dir}[/yellow]")
        console.print("[dim]Use 'ptracker config' to view or modify settings[/dim]")
        return
    
    # Create data directory
    data_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]✓[/green] Created directory: {data_dir}")
    
    # Create empty JSON files
    json_files = [
        "transactions.json",
        "holdings.json",
        "realized.json",
        "accounts.json"
    ]
    
    for filename in json_files:
        filepath = data_dir / filename
        if not filepath.exists():
            # Create empty TinyDB database
            db = TinyDB(filepath)
            db.close()
            console.print(f"[green]✓[/green] Created file: {filename}")
    
    # Create config.toml with default settings
    config_path = data_dir / "config.toml"
    if not config_path.exists():
        config_mgr = ConfigManager(config_path)
        config_mgr.save(DEFAULT_CONFIG)
        console.print(f"[green]✓[/green] Created config: config.toml")
    
    # Success message
    console.print(f"\n[bold green]✅ ptracker initialized successfully![/bold green]")
    console.print(f"\n[dim]Data directory: {data_dir}[/dim]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Add an account: [cyan]ptracker account add <name>[/cyan]")
    console.print("  2. Record a trade: [cyan]ptracker trade add buy <asset> <quantity> <price> --currency <CUR>[/cyan]")
    console.print("  3. View holdings: [cyan]ptracker query holdings[/cyan]")
