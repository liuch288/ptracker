"""Configuration commands for ptracker."""

from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from ptracker.config import ConfigManager

console = Console()
app = typer.Typer(help="Manage ptracker configuration")


def get_data_dir() -> Path:
    """Get ptracker data directory."""
    return Path.home() / ".ptracker"


@app.command("show")
def show_config():
    """Display current configuration."""
    data_dir = get_data_dir()
    config_path = data_dir / "config.toml"
    
    if not config_path.exists():
        console.print("[red]Error: ptracker not initialized. Run 'ptracker init' first.[/red]")
        raise typer.Exit(1)
    
    config_mgr = ConfigManager(config_path)
    config = config_mgr.load()
    
    console.print("[bold]Current Configuration:[/bold]\n")
    
    # General settings
    table = Table(title="General Settings", show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="bold")
    table.add_column("Value")
    
    table.add_row("Default Currency", config['general']['default_currency'])
    table.add_row("Default Account", config['general']['default_account'] or "[dim]Not set[/dim]")
    table.add_row("Cost Basis Method", config['general']['cost_basis_method'])
    
    console.print(table)
    console.print()
    
    # Display settings
    table = Table(title="Display Settings", show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="bold")
    table.add_column("Value")
    
    table.add_row("Date Format", config['display']['date_format'])
    table.add_row("Decimal Places", str(config['display']['decimal_places']))
    
    color_scheme = config['display'].get('color_scheme', 'green_up')
    color_desc = "Green for profit/up, Red for loss/down" if color_scheme == 'green_up' else "Red for profit/up, Green for loss/down"
    table.add_row("Color Scheme", f"{color_scheme} ({color_desc})")
    
    console.print(table)
    console.print()
    
    # API settings
    table = Table(title="API Settings", show_header=True, header_style="bold cyan")
    table.add_column("Setting", style="bold")
    table.add_column("Value")
    
    table.add_row("Price Cache (seconds)", str(config['api']['price_cache_seconds']))
    table.add_row("Request Timeout (seconds)", str(config['api']['request_timeout']))
    
    console.print(table)


@app.command("set")
def set_config(
    key: str = typer.Argument(..., help="Configuration key (e.g., 'display.color_scheme')"),
    value: str = typer.Argument(..., help="New value"),
):
    """Set a configuration value."""
    data_dir = get_data_dir()
    config_path = data_dir / "config.toml"
    
    if not config_path.exists():
        console.print("[red]Error: ptracker not initialized. Run 'ptracker init' first.[/red]")
        raise typer.Exit(1)
    
    config_mgr = ConfigManager(config_path)
    
    # Validate color scheme
    if key == 'display.color_scheme' and value not in ['green_up', 'red_up']:
        console.print(f"[red]Error: Invalid color scheme '{value}'. Must be 'green_up' or 'red_up'.[/red]")
        raise typer.Exit(1)
    
    # Set the value
    config_mgr.set(key, value)
    
    console.print(f"[green]✓[/green] Configuration updated: {key} = {value}")


@app.command("color")
def set_color_scheme():
    """Change color scheme preference interactively."""
    data_dir = get_data_dir()
    config_path = data_dir / "config.toml"
    
    if not config_path.exists():
        console.print("[red]Error: ptracker not initialized. Run 'ptracker init' first.[/red]")
        raise typer.Exit(1)
    
    config_mgr = ConfigManager(config_path)
    current_scheme = config_mgr.get_color_scheme()
    
    console.print(f"[bold]Current color scheme:[/bold] {current_scheme}\n")
    console.print("[bold]Choose new color scheme:[/bold]")
    console.print("  1. [green]Green[/green] for profit/up, [red]Red[/red] for loss/down (Western style)")
    console.print("  2. [red]Red[/red] for profit/up, [green]Green[/green] for loss/down (Chinese style)")
    
    choice = typer.prompt("Select option", type=int, default=1 if current_scheme == 'green_up' else 2)
    
    new_scheme = "green_up" if choice == 1 else "red_up"
    
    if new_scheme == current_scheme:
        console.print("[yellow]No change made.[/yellow]")
        return
    
    config_mgr.set('display.color_scheme', new_scheme)
    console.print(f"[green]✓[/green] Color scheme updated to: {new_scheme}")


if __name__ == "__main__":
    app()
