"""CLI commands for ptracker."""

from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from tinydb import TinyDB
from ptracker.config import ConfigManager, DEFAULT_CONFIG
import toml

console = Console()


def init_command():
    """Initialize ptracker data directory and files."""
    # Get data directory path
    data_dir = Path.home() / ".ptracker"
    
    # Check if already initialized
    if data_dir.exists() and (data_dir / "config.toml").exists():
        console.print(f"[yellow]⚠️  ptracker is already initialized at {data_dir}[/yellow]")
        console.print("[dim]Use 'ptracker config' to view or modify settings[/dim]")
        return
    
    # Create directory
    data_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]✓[/green] Created directory: {data_dir}")
    
    # Create empty JSON files
    json_files = ['transactions.json', 'holdings.json', 'realized.json', 'accounts.json']
    for filename in json_files:
        filepath = data_dir / filename
        if not filepath.exists():
            # Initialize empty TinyDB
            db = TinyDB(filepath)
            db.close()
            console.print(f"[green]✓[/green] Created file: {filename}")
    
    # Create config.toml
    config_path = data_dir / "config.toml"
    if not config_path.exists():
        with open(config_path, 'w') as f:
            toml.dump(DEFAULT_CONFIG, f)
        console.print(f"[green]✓[/green] Created config: config.toml")
    
    # Success message
    console.print(f"\n[bold green]🎉 ptracker initialized successfully![/bold green]")
    console.print(f"[dim]Data directory: {data_dir}[/dim]")
    console.print(f"\n[bold]Next steps:[/bold]")
    console.print("  1. Add an account: [cyan]ptracker account add <name>[/cyan]")
    console.print("  2. Record a transaction: [cyan]ptracker trade add buy <asset> <quantity> <price> --currency <CUR>[/cyan]")
    console.print("  3. View holdings: [cyan]ptracker query holdings[/cyan]")
