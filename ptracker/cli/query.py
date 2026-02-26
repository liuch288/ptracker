"""Query commands for holdings and portfolio."""

from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from ptracker.repositories import HoldingRepository, RealizedRepository
from ptracker.services.price_service import PriceService
from ptracker.services.pnl_calculator import PnLCalculator
from ptracker.utils.color_helper import get_pnl_color
from ptracker.config import ConfigManager

console = Console()
app = typer.Typer(help="Query holdings and portfolio information")


def get_data_dir() -> Path:
    """Get ptracker data directory."""
    return Path.home() / ".ptracker"


@app.command("holdings")
def query_holdings(
    account: Optional[str] = typer.Option(None, "--account", "-a", help="Filter by account"),
    asset: Optional[str] = typer.Option(None, "--asset", help="Filter by asset"),
    sort_by: Optional[str] = typer.Option(None, "--sort", "-s", help="Sort by field (asset, quantity, avg_cost, total_invested, last_updated)"),
    currency: Optional[str] = typer.Option(None, "--currency", help="Convert values to currency"),
):
    """Query current holdings."""
    data_dir = get_data_dir()
    
    if not data_dir.exists():
        console.print("[red]Error: ptracker not initialized. Run 'ptracker init' first.[/red]")
        raise typer.Exit(1)
    
    # Get default currency from config if not specified
    if not currency:
        config = ConfigManager(data_dir / "config.toml")
        currency = config.get_default_currency()
    
    # Get holdings
    holding_repo = HoldingRepository(data_dir / "holdings.json")
    holdings = holding_repo.find_all()
    
    # Apply filters
    if account:
        holdings = [h for h in holdings if h['account'] == account]
    
    if asset:
        holdings = [h for h in holdings if h['asset'].upper() == asset.upper()]
    
    if not holdings:
        console.print("[yellow]No holdings found.[/yellow]")
        return
    
    # Sort holdings
    if sort_by:
        valid_sorts = ['asset', 'quantity', 'avg_cost', 'total_invested', 'last_updated']
        if sort_by not in valid_sorts:
            console.print(f"[red]Error: Invalid sort field '{sort_by}'. Valid options: {', '.join(valid_sorts)}[/red]")
            raise typer.Exit(1)
        
        holdings.sort(key=lambda h: h.get(sort_by, 0))
    else:
        # Default sort by asset
        holdings.sort(key=lambda h: h['asset'])
    
    # Currency conversion (if specified)
    if currency:
        price_service = PriceService()
        console.print(f"[dim]Converting to {currency}...[/dim]\n")
    
    # Create table for active holdings
    if holdings:
        table = Table(title="Active Holdings", show_header=True, header_style="bold cyan")
        table.add_column("Asset", style="bold")
        table.add_column("Account")
        table.add_column("Dir")
        table.add_column("Quantity", justify="right")
        table.add_column("Avg Cost", justify="right")
        table.add_column("Total Invested", justify="right")
        table.add_column("Currency")
        table.add_column("First Open", style="dim")
        table.add_column("Last Updated", style="dim")
        
        total_invested = 0.0
        
        for holding in holdings:
            invested = holding['total_invested']
            avg_cost = holding['avg_cost']
            curr = holding['currency']
            
            # Convert currency if needed
            if currency and curr != currency:
                rate = price_service.get_exchange_rate(curr, currency)
                invested = invested * rate
                avg_cost = avg_cost * rate
                curr = currency
            
            total_invested += invested
            
            table.add_row(
                holding['asset'],
                holding['account'],
                holding['direction'][:1].upper(),
                f"{holding['quantity']:.2f}",
                f"{avg_cost:.2f}",
                f"{invested:.2f}",
                curr,
                holding['first_open_date'],
                holding['last_updated']
            )
        
        console.print(table)
        console.print(f"\n[bold]Total Invested: {total_invested:.2f} {currency}[/bold]")


@app.command("value")
def query_value(
    account: Optional[str] = typer.Option(None, "--account", "-a", help="Filter by account"),
    currency: Optional[str] = typer.Option(None, "--currency", "-c", help="Convert to currency"),
    breakdown: Optional[str] = typer.Option(None, "--breakdown", "-b", help="Breakdown by: asset, account, or currency"),
):
    """Calculate total portfolio value."""
    data_dir = get_data_dir()
    
    if not data_dir.exists():
        console.print("[red]Error: ptracker not initialized. Run 'ptracker init' first.[/red]")
        raise typer.Exit(1)
    
    # Get default currency from config if not specified
    if not currency:
        config = ConfigManager(data_dir / "config.toml")
        currency = config.get_default_currency()
    
    # Get holdings
    holding_repo = HoldingRepository(data_dir / "holdings.json")
    holdings = holding_repo.find_all()
    
    if account:
        holdings = [h for h in holdings if h['account'] == account]
    
    if not holdings:
        console.print("[yellow]No holdings found.[/yellow]")
        return
    
    # Initialize price service
    price_service = PriceService()
    pnl_calculator = PnLCalculator(price_service)
    
    console.print("[dim]Fetching current prices...[/dim]\n")
    
    # Use the currency (either specified or default)
    target_curr = currency
    
    # Calculate values
    total_invested = 0.0
    total_current_value = 0.0
    breakdown_data = {}
    
    for holding in holdings:
        # Get current price
        quote = price_service.get_price(holding['asset'])
        
        if not quote:
            console.print(f"[yellow]Warning: Could not fetch price for {holding['asset']}, skipping...[/yellow]")
            continue
        
        current_price = quote.price
        
        # Calculate values
        invested = holding['total_invested']
        current_value = abs(holding['quantity']) * current_price
        
        # Convert currency if needed
        if target_curr and holding['currency'] != target_curr:
            rate = price_service.get_exchange_rate(holding['currency'], target_curr)
            invested = invested * rate
            current_value = current_value * rate
        
        total_invested += invested
        total_current_value += current_value
        
        # Breakdown
        if breakdown:
            if breakdown == 'asset':
                key = holding['asset']
            elif breakdown == 'account':
                key = holding['account']
            elif breakdown == 'currency':
                key = holding['currency']
            else:
                console.print(f"[red]Error: Invalid breakdown '{breakdown}'. Use: asset, account, or currency[/red]")
                raise typer.Exit(1)
            
            if key not in breakdown_data:
                breakdown_data[key] = {'invested': 0.0, 'current': 0.0}
            
            breakdown_data[key]['invested'] += invested
            breakdown_data[key]['current'] += current_value
    
    # Display results
    total_pnl = total_current_value - total_invested
    total_return = (total_pnl / total_invested * 100) if total_invested > 0 else 0.0
    
    pnl_color = get_pnl_color(total_pnl, data_dir / "config.toml")
    return_color = get_pnl_color(total_return, data_dir / "config.toml")
    
    console.print(f"[bold]Portfolio Summary[/bold]")
    console.print(f"  Total Invested:     {total_invested:>15,.2f} {target_curr}")
    console.print(f"  Current Value:      {total_current_value:>15,.2f} {target_curr}")
    console.print(f"  Unrealized P&L:     [{pnl_color}]{total_pnl:>+15,.2f}[/{pnl_color}] {target_curr}")
    console.print(f"  Return:             [{return_color}]{total_return:>+15,.2f}%[/{return_color}]")
    
    # Display breakdown if requested
    if breakdown and breakdown_data:
        console.print(f"\n[bold]Breakdown by {breakdown.capitalize()}:[/bold]")
        
        table = Table(show_header=True, header_style="bold")
        table.add_column(breakdown.capitalize())
        table.add_column("Invested", justify="right")
        table.add_column("Current Value", justify="right")
        table.add_column("P&L", justify="right")
        table.add_column("Return %", justify="right")
        
        for key, data in sorted(breakdown_data.items()):
            pnl = data['current'] - data['invested']
            ret = (pnl / data['invested'] * 100) if data['invested'] > 0 else 0.0
            
            pnl_color = get_pnl_color(pnl, data_dir / "config.toml")
            ret_color = get_pnl_color(ret, data_dir / "config.toml")
            
            table.add_row(
                key,
                f"{data['invested']:.2f}",
                f"{data['current']:.2f}",
                f"[{pnl_color}]{pnl:+.2f}[/{pnl_color}]",
                f"[{ret_color}]{ret:+.2f}%[/{ret_color}]"
            )
        
        console.print(table)
@app.command("realized")
def query_realized(
    account: Optional[str] = typer.Option(None, "--account", "-a", help="Filter by account"),
    asset: Optional[str] = typer.Option(None, "--asset", help="Filter by asset"),
    currency: Optional[str] = typer.Option(None, "--currency", "-c", help="Convert to currency"),
    sort_by: Optional[str] = typer.Option("date", "--sort", "-s", help="Sort by: date, pnl, return, days (default: date)"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of results"),
):
    """Query realized (closed) positions."""
    data_dir = get_data_dir()

    if not data_dir.exists():
        console.print("[red]Error: ptracker not initialized. Run 'ptracker init' first.[/red]")
        raise typer.Exit(1)

    # Get default currency from config if not specified
    if not currency:
        config = ConfigManager(data_dir / "config.toml")
        currency = config.get_default_currency()

    # Get realized positions
    realized_repo = RealizedRepository(data_dir / "realized.json")
    realized_positions = realized_repo.find_all()

    # Apply filters
    if account:
        realized_positions = [r for r in realized_positions if r['account'] == account]

    if asset:
        realized_positions = [r for r in realized_positions if r['asset'].upper() == asset.upper()]

    if not realized_positions:
        console.print("[yellow]No realized positions found.[/yellow]")
        return

    # Initialize price service for currency conversion
    from ptracker.services.price_service import PriceService
    price_service = PriceService()

    # Sort
    if sort_by == "date":
        realized_positions.sort(key=lambda r: r['last_close_date'], reverse=True)
    elif sort_by == "pnl":
        realized_positions.sort(key=lambda r: r['realized_pnl'], reverse=True)
    elif sort_by == "return":
        realized_positions.sort(key=lambda r: r['return_pct'], reverse=True)
    elif sort_by == "days":
        realized_positions.sort(key=lambda r: r['holding_days'], reverse=True)
    else:
        console.print(f"[red]Error: Invalid sort field '{sort_by}'. Valid options: date, pnl, return, days[/red]")
        raise typer.Exit(1)

    # Apply limit
    if limit:
        realized_positions = realized_positions[:limit]

    # Create table
    table = Table(title="Realized Positions", show_header=True, header_style="bold cyan")
    table.add_column("Asset", style="bold")
    table.add_column("Account")
    table.add_column("Dir")
    table.add_column("Quantity", justify="right")
    table.add_column("Invested", justify="right")
    table.add_column("Proceeds", justify="right")
    table.add_column("Realized P&L", justify="right")
    table.add_column("Return %", justify="right")
    table.add_column("Currency")
    table.add_column("Days", justify="right")
    table.add_column("Opened", style="dim")
    table.add_column("Closed", style="dim")

    total_pnl = 0.0

    for realized in realized_positions:
        invested = realized['total_invested']
        proceeds = realized['total_proceeds']
        pnl = realized['realized_pnl']
        curr = realized.get('currency', 'USD')
        
        # Convert currency if needed
        if currency and curr != currency:
            rate = price_service.get_exchange_rate(curr, currency)
            invested = invested * rate
            proceeds = proceeds * rate
            pnl = pnl * rate
            curr = currency
        
        pnl_color = get_pnl_color(pnl, data_dir / "config.toml")
        return_color = get_pnl_color(realized['return_pct'], data_dir / "config.toml")

        total_pnl += pnl

        table.add_row(
            realized['asset'],
            realized['account'],
            realized['direction'][:1].upper(),
            f"{realized['total_quantity']:.2f}",
            f"{invested:.2f}",
            f"{proceeds:.2f}",
            f"[{pnl_color}]{pnl:+.2f}[/{pnl_color}]",
            f"[{return_color}]{realized['return_pct']:+.2f}%[/{return_color}]",
            curr,
            str(realized['holding_days']),
            realized['first_open_date'],
            realized['last_close_date']
        )

    console.print(table)

    # Summary
    pnl_color = get_pnl_color(total_pnl, data_dir / "config.toml")
    console.print(f"\n[bold]Total Realized P&L: [{pnl_color}]{total_pnl:+.2f}[/{pnl_color}] {currency}[/bold]")
    console.print(f"[dim]Showing {len(realized_positions)} position(s)[/dim]")





if __name__ == "__main__":
    app()
