"""Query commands for holdings and portfolio."""

from pathlib import Path
from typing import Optional, Literal
import typer
from rich.console import Console
from rich.table import Table
from ptracker.repositories import HoldingRepository, RealizedRepository, TransactionRepository
from ptracker.services.price_service import PriceService
from ptracker.services.pnl_calculator import PnLCalculator, get_multiplier
from ptracker.utils.color_helper import get_pnl_color
from ptracker.config import ConfigManager

console = Console()
app = typer.Typer(help="Query holdings and portfolio information")

# ID truncation limit (approximately 12 characters)
ID_TRUNCATE_LENGTH = 12

# Note truncation limit
NOTE_TRUNCATE_LENGTH = 20


def format_id(id_value: Optional[str], full: bool = False) -> str:
    """Format ID for display, optionally truncated.
    
    Args:
        id_value: The ID to format
        full: If True, show full ID; if False, return empty string (ID hidden by default)
        
    Returns:
        Formatted ID string
    """
    if not id_value:
        return ""
    if full:
        return id_value
    # ID hidden by default, only show when full=True
    return ""


def format_note(note: Optional[str], full: bool = False) -> str:
    """Format note for display, optionally truncated.
    
    Args:
        note: The note to format
        full: If True, show full note; if False, truncate to ~20 chars
        
    Returns:
        Formatted note string
    """
    if not note:
        return ""
    if full:
        return note
    return note[:NOTE_TRUNCATE_LENGTH] + "..." if len(note) > NOTE_TRUNCATE_LENGTH else note


def get_data_dir() -> Path:
    """Get ptracker data directory."""
    return Path.home() / ".ptracker"


@app.command("holdings")
def query_holdings(
    account: Optional[str] = typer.Option(None, "--account", "-a", help="Filter by account"),
    asset: Optional[str] = typer.Option(None, "--asset", help="Filter by asset"),
    sort_by: Optional[str] = typer.Option(None, "--sort", "-s", help="Sort by field (asset, quantity, avg_cost, total_invested, last_updated)"),
    currency: Optional[str] = typer.Option(None, "--currency", "-c", help="Convert all values to currency"),
    detail_currency: Optional[str] = typer.Option(None, "--detail-currency", "-d", help="Currency for detail display (or 'mix' for original)"),
    total_currency: Optional[str] = typer.Option(None, "--total-currency", "-t", help="Currency for total calculation"),
    fullid: bool = typer.Option(False, "--fullid", help="Show full ID"),
    fullnote: bool = typer.Option(False, "--fullnote", help="Show full note instead of truncated"),
):
    """Query current holdings."""
    data_dir = get_data_dir()
    
    if not data_dir.exists():
        console.print("[red]Error: ptracker not initialized. Run 'ptracker init' first.[/red]")
        raise typer.Exit(1)
    
    # Get default currency from config
    config = ConfigManager(data_dir / "config.toml")
    default_currency = config.get_default_currency()
    
    # Determine currencies with priority:
    # 1. If --currency specified: both detail and total use it
    # 2. If --detail-currency or --total-currency specified: they override
    # 3. If nothing specified: detail='mix', total=default
    if currency:
        # --currency sets both
        final_detail_currency = currency
        final_total_currency = currency
    else:
        # No --currency, use defaults
        final_detail_currency = 'mix'
        final_total_currency = default_currency
    
    # Override with specific options if provided
    if detail_currency:
        final_detail_currency = detail_currency
    if total_currency:
        final_total_currency = total_currency
    
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
    
    # Initialize price service
    price_service = PriceService()
    
    # Create table for active holdings
    if holdings:
        table = Table(title="Active Holdings", show_header=True, header_style="bold cyan")
        if fullid:
            table.add_column("ID", style="dim")
        table.add_column("Asset", style="bold")
        table.add_column("Account")
        table.add_column("Dir")
        table.add_column("Quantity", justify="right")
        table.add_column("Avg Cost", justify="right")
        table.add_column("Total Invested", justify="right")
        table.add_column("Currency")
        table.add_column("First Open", style="dim")
        table.add_column("Last Updated", style="dim")
        table.add_column("Note", style="dim")
        
        total_invested = 0.0
        
        for holding in holdings:
            invested = holding['total_invested']
            avg_cost = holding['avg_cost']
            curr = holding['currency']
            
            # Get multiplier for options
            multiplier = get_multiplier(holding['asset'], holding['quantity'])
            
            # For detail display
            display_invested = invested
            display_avg_cost = avg_cost / multiplier  # Show per-share price for options
            display_curr = curr
            
            # Convert detail if needed (not 'mix')
            if final_detail_currency != 'mix' and curr != final_detail_currency:
                rate = price_service.get_exchange_rate(curr, final_detail_currency)
                display_invested = invested * rate
                display_avg_cost = display_avg_cost * rate
                display_curr = final_detail_currency
            
            # Convert for total calculation
            if curr != final_total_currency:
                rate = price_service.get_exchange_rate(curr, final_total_currency)
                invested = invested * rate
            
            total_invested += invested
            
            row = []
            if fullid:
                row.append(format_id(holding.get('id'), fullid))
            row.extend([
                holding['asset'],
                holding['account'],
                holding['direction'][:1].upper(),
                f"{holding['quantity']:.2f}",
                f"{display_avg_cost:.2f}",
                f"{display_invested:.2f}",
                display_curr,
                holding['first_open_date'],
                holding['last_updated'],
            ])
            row.append(format_note(holding.get('note'), fullnote))
            
            table.add_row(*row)
        
        console.print(table)
        console.print(f"\n[bold]Total Invested: {total_invested:.2f} {final_total_currency}[/bold]")


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
        
        # Get multiplier for options (100x for option contracts)
        multiplier = get_multiplier(holding['asset'], holding['quantity'])
        
        # Calculate values
        invested = holding['total_invested']
        current_value = abs(holding['quantity']) * current_price * multiplier
        
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
    currency: Optional[str] = typer.Option(None, "--currency", "-c", help="Convert all values to currency"),
    detail_currency: Optional[str] = typer.Option(None, "--detail-currency", "-d", help="Currency for detail display (or 'mix' for original)"),
    total_currency: Optional[str] = typer.Option(None, "--total-currency", "-t", help="Currency for total calculation"),
    sort_by: Optional[str] = typer.Option("date", "--sort", "-s", help="Sort by: date, pnl, return, days (default: date)"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of results"),
    fullid: bool = typer.Option(False, "--fullid", help="Show full ID"),
    fullnote: bool = typer.Option(False, "--fullnote", help="Show full note instead of truncated"),
):
    """Query realized (closed) positions."""
    data_dir = get_data_dir()

    if not data_dir.exists():
        console.print("[red]Error: ptracker not initialized. Run 'ptracker init' first.[/red]")
        raise typer.Exit(1)

    # Get default currency from config
    config = ConfigManager(data_dir / "config.toml")
    default_currency = config.get_default_currency()
    
    # Determine currencies (same logic as holdings)
    if currency:
        final_detail_currency = currency
        final_total_currency = currency
    else:
        final_detail_currency = 'mix'
        final_total_currency = default_currency
    
    if detail_currency:
        final_detail_currency = detail_currency
    if total_currency:
        final_total_currency = total_currency

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
    if fullid:
        table.add_column("ID", style="dim")
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
    table.add_column("Note", style="dim")

    total_pnl = 0.0

    for realized in realized_positions:
        invested = realized['total_invested']
        proceeds = realized['total_proceeds']
        pnl = realized['realized_pnl']
        curr = realized.get('currency', 'USD')
        
        # For detail display
        display_invested = invested
        display_proceeds = proceeds
        display_pnl = pnl
        display_curr = curr
        
        # Convert detail if needed (not 'mix')
        if final_detail_currency != 'mix' and curr != final_detail_currency:
            rate = price_service.get_exchange_rate(curr, final_detail_currency)
            display_invested = invested * rate
            display_proceeds = proceeds * rate
            display_pnl = pnl * rate
            display_curr = final_detail_currency
        
        # Convert for total calculation
        if curr != final_total_currency:
            rate = price_service.get_exchange_rate(curr, final_total_currency)
            pnl = pnl * rate
        
        pnl_color = get_pnl_color(display_pnl, data_dir / "config.toml")
        return_color = get_pnl_color(realized['return_pct'], data_dir / "config.toml")

        total_pnl += pnl

        row = []
        if fullid:
            row.append(format_id(realized.get('id'), fullid))
        row.extend([
            realized['asset'],
            realized['account'],
            realized['direction'][:1].upper(),
            f"{realized['total_quantity']:.2f}",
            f"{display_invested:.2f}",
            f"{display_proceeds:.2f}",
            f"[{pnl_color}]{display_pnl:+.2f}[/{pnl_color}]",
            f"[{return_color}]{realized['return_pct']:+.2f}%[/{return_color}]",
            display_curr,
            str(realized['holding_days']),
            realized['first_open_date'],
            realized['last_close_date'],
        ])
        row.append(format_note(realized.get('note'), fullnote))
        
        table.add_row(*row)

    console.print(table)

    # Summary
    pnl_color = get_pnl_color(total_pnl, data_dir / "config.toml")
    console.print(f"\n[bold]Total Realized P&L: [{pnl_color}]{total_pnl:+.2f}[/{pnl_color}] {final_total_currency}[/bold]")
    console.print(f"[dim]Showing {len(realized_positions)} position(s)[/dim]")




@app.command("pnl")
def query_pnl(
    account: Optional[str] = typer.Option(None, "--account", "-a", help="Filter by account"),
    currency: Optional[str] = typer.Option(None, "--currency", "-c", help="Convert all values to currency"),
    detail_currency: Optional[str] = typer.Option(None, "--detail-currency", "-d", help="Currency for detail display (or 'mix')"),
    total_currency: Optional[str] = typer.Option(None, "--total-currency", "-t", help="Currency for total calculation"),
    detail: bool = typer.Option(False, "--detail", help="Show detailed breakdown by asset"),
    realized_only: bool = typer.Option(False, "--realized-only", help="Show only realized P&L"),
    unrealized_only: bool = typer.Option(False, "--unrealized-only", help="Show only unrealized P&L"),
):
    """Query profit and loss (realized and unrealized)."""
    data_dir = get_data_dir()
    
    if not data_dir.exists():
        console.print("[red]Error: ptracker not initialized. Run 'ptracker init' first.[/red]")
        raise typer.Exit(1)
    
    # Get default currency from config
    config = ConfigManager(data_dir / "config.toml")
    default_currency = config.get_default_currency()
    
    # Determine currencies (same logic as holdings/realized)
    if currency:
        final_detail_currency = currency
        final_total_currency = currency
    else:
        final_detail_currency = 'mix'
        final_total_currency = default_currency
    
    if detail_currency:
        final_detail_currency = detail_currency
    if total_currency:
        final_total_currency = total_currency
    
    # Initialize services
    price_service = PriceService()
    pnl_calculator = PnLCalculator(price_service)
    
    # Get data
    holding_repo = HoldingRepository(data_dir / "holdings.json")
    realized_repo = RealizedRepository(data_dir / "realized.json")
    
    holdings = holding_repo.find_all()
    realized_positions = realized_repo.find_all()
    
    # Apply account filter
    if account:
        holdings = [h for h in holdings if h['account'] == account]
        realized_positions = [r for r in realized_positions if r['account'] == account]
    
    # Calculate unrealized P&L
    unrealized_total_invested = 0.0
    unrealized_total_current = 0.0
    unrealized_by_asset = {}
    
    if not unrealized_only and not realized_only:
        show_unrealized = True
        show_realized = True
    elif unrealized_only:
        show_unrealized = True
        show_realized = False
    else:  # realized_only
        show_unrealized = False
        show_realized = True
    
    if show_unrealized and holdings:
        console.print("[dim]Fetching current prices...[/dim]\n")
        
        for holding in holdings:
            # Get current price
            quote = price_service.get_price(holding['asset'])
            
            if not quote:
                console.print(f"[yellow]Warning: Could not fetch price for {holding['asset']}, skipping...[/yellow]")
                continue
            
            current_price = quote.price
            
            # Get multiplier for options (100x for option contracts)
            multiplier = get_multiplier(holding['asset'], holding['quantity'])
            
            # Calculate values
            invested = holding['total_invested']
            current_value = abs(holding['quantity']) * current_price * multiplier
            curr = holding['currency']
            
            # For detail display
            display_invested = invested
            display_current = current_value
            display_curr = curr
            
            # Convert detail if needed (not 'mix')
            if final_detail_currency != 'mix' and curr != final_detail_currency:
                rate = price_service.get_exchange_rate(curr, final_detail_currency)
                display_invested = invested * rate
                display_current = current_value * rate
                display_curr = final_detail_currency
            
            # Convert for total calculation
            if curr != final_total_currency:
                rate = price_service.get_exchange_rate(curr, final_total_currency)
                invested = invested * rate
                current_value = current_value * rate
            
            unrealized_total_invested += invested
            unrealized_total_current += current_value
            
            # For detail breakdown
            if detail:
                key = f"{holding['asset']}|{holding['account']}"
                if key not in unrealized_by_asset:
                    unrealized_by_asset[key] = {
                        'asset': holding['asset'],
                        'account': holding['account'],
                        'invested': 0.0,
                        'current': 0.0,
                        'currency': display_curr
                    }
                unrealized_by_asset[key]['invested'] += display_invested
                unrealized_by_asset[key]['current'] += display_current
    
    # Calculate realized P&L
    realized_total_invested = 0.0
    realized_total_proceeds = 0.0
    realized_total_pnl = 0.0
    realized_by_asset = {}
    
    if show_realized and realized_positions:
        for realized in realized_positions:
            invested = realized['total_invested']
            proceeds = realized['total_proceeds']
            pnl = realized['realized_pnl']
            curr = realized.get('currency', 'USD')
            
            # For detail display
            display_invested = invested
            display_proceeds = proceeds
            display_pnl = pnl
            display_curr = curr
            
            # Convert detail if needed (not 'mix')
            if final_detail_currency != 'mix' and curr != final_detail_currency:
                rate = price_service.get_exchange_rate(curr, final_detail_currency)
                display_invested = invested * rate
                display_proceeds = proceeds * rate
                display_pnl = pnl * rate
                display_curr = final_detail_currency
            
            # Convert for total calculation
            if curr != final_total_currency:
                rate = price_service.get_exchange_rate(curr, final_total_currency)
                invested = invested * rate
                proceeds = proceeds * rate
                pnl = pnl * rate
            
            realized_total_invested += invested
            realized_total_proceeds += proceeds
            realized_total_pnl += pnl
            
            # For detail breakdown
            if detail:
                key = f"{realized['asset']}|{realized['account']}"
                if key not in realized_by_asset:
                    realized_by_asset[key] = {
                        'asset': realized['asset'],
                        'account': realized['account'],
                        'invested': 0.0,
                        'proceeds': 0.0,
                        'pnl': 0.0,
                        'currency': display_curr
                    }
                realized_by_asset[key]['invested'] += display_invested
                realized_by_asset[key]['proceeds'] += display_proceeds
                realized_by_asset[key]['pnl'] += display_pnl
    
    # Display results
    console.print("[bold]P&L Summary[/bold]")
    console.print("━" * 60)
    
    if show_unrealized:
        unrealized_pnl = unrealized_total_current - unrealized_total_invested
        unrealized_return = (unrealized_pnl / unrealized_total_invested * 100) if unrealized_total_invested > 0 else 0.0
        
        pnl_color = get_pnl_color(unrealized_pnl, data_dir / "config.toml")
        return_color = get_pnl_color(unrealized_return, data_dir / "config.toml")
        
        console.print("\n[bold cyan]Unrealized P&L (Current Holdings)[/bold cyan]")
        console.print(f"  Total Invested:     {unrealized_total_invested:>15,.2f} {final_total_currency}")
        console.print(f"  Current Value:      {unrealized_total_current:>15,.2f} {final_total_currency}")
        console.print(f"  Unrealized P&L:     [{pnl_color}]{unrealized_pnl:>+15,.2f}[/{pnl_color}] {final_total_currency}")
        console.print(f"  Return:             [{return_color}]{unrealized_return:>+15.2f}%[/{return_color}]")
        
        if detail and unrealized_by_asset:
            console.print("\n[bold]Unrealized P&L by Asset[/bold]")
            table = Table(show_header=True, header_style="bold")
            table.add_column("Asset", style="bold")
            table.add_column("Account")
            table.add_column("Invested", justify="right")
            table.add_column("Current Value", justify="right")
            table.add_column("P&L", justify="right")
            table.add_column("Return %", justify="right")
            table.add_column("Currency")
            
            for key, data in sorted(unrealized_by_asset.items()):
                pnl = data['current'] - data['invested']
                ret = (pnl / data['invested'] * 100) if data['invested'] > 0 else 0.0
                
                pnl_color = get_pnl_color(pnl, data_dir / "config.toml")
                ret_color = get_pnl_color(ret, data_dir / "config.toml")
                
                table.add_row(
                    data['asset'],
                    data['account'],
                    f"{data['invested']:,.2f}",
                    f"{data['current']:,.2f}",
                    f"[{pnl_color}]{pnl:+,.2f}[/{pnl_color}]",
                    f"[{ret_color}]{ret:+.2f}%[/{ret_color}]",
                    data['currency']
                )
            
            console.print(table)
            console.print(f"[bold]Subtotal Unrealized: [{pnl_color}]{unrealized_pnl:+,.2f}[/{pnl_color}] {final_total_currency}[/bold]")
    
    if show_realized:
        realized_return = (realized_total_pnl / realized_total_invested * 100) if realized_total_invested > 0 else 0.0
        
        pnl_color = get_pnl_color(realized_total_pnl, data_dir / "config.toml")
        return_color = get_pnl_color(realized_return, data_dir / "config.toml")
        
        console.print("\n[bold yellow]Realized P&L (Closed Positions)[/bold yellow]")
        console.print(f"  Total Invested:     {realized_total_invested:>15,.2f} {final_total_currency}")
        console.print(f"  Total Proceeds:     {realized_total_proceeds:>15,.2f} {final_total_currency}")
        console.print(f"  Realized P&L:       [{pnl_color}]{realized_total_pnl:>+15,.2f}[/{pnl_color}] {final_total_currency}")
        console.print(f"  Return:             [{return_color}]{realized_return:>+15.2f}%[/{return_color}]")
        
        if detail and realized_by_asset:
            console.print("\n[bold]Realized P&L by Asset[/bold]")
            table = Table(show_header=True, header_style="bold")
            table.add_column("Asset", style="bold")
            table.add_column("Account")
            table.add_column("Invested", justify="right")
            table.add_column("Proceeds", justify="right")
            table.add_column("P&L", justify="right")
            table.add_column("Return %", justify="right")
            table.add_column("Currency")
            
            for key, data in sorted(realized_by_asset.items()):
                ret = (data['pnl'] / data['invested'] * 100) if data['invested'] > 0 else 0.0
                
                pnl_color = get_pnl_color(data['pnl'], data_dir / "config.toml")
                ret_color = get_pnl_color(ret, data_dir / "config.toml")
                
                table.add_row(
                    data['asset'],
                    data['account'],
                    f"{data['invested']:,.2f}",
                    f"{data['proceeds']:,.2f}",
                    f"[{pnl_color}]{data['pnl']:+,.2f}[/{pnl_color}]",
                    f"[{ret_color}]{ret:+.2f}%[/{ret_color}]",
                    data['currency']
                )
            
            console.print(table)
            console.print(f"[bold]Subtotal Realized: [{pnl_color}]{realized_total_pnl:+,.2f}[/{pnl_color}] {final_total_currency}[/bold]")
    
    # Total summary (if showing both)
    if show_unrealized and show_realized:
        console.print("\n" + "━" * 60)
        total_pnl = unrealized_pnl + realized_total_pnl
        total_invested = unrealized_total_invested + realized_total_invested
        total_return = (total_pnl / total_invested * 100) if total_invested > 0 else 0.0
        
        pnl_color = get_pnl_color(total_pnl, data_dir / "config.toml")
        return_color = get_pnl_color(total_return, data_dir / "config.toml")
        
        console.print(f"[bold]Total P&L:           [{pnl_color}]{total_pnl:>+15,.2f}[/{pnl_color}] {final_total_currency}[/bold]")
        console.print(f"[bold]Total Return:        [{return_color}]{total_return:>+15.2f}%[/{return_color}][/bold]")
    
    # Additional info
    if show_unrealized and not show_realized:
        console.print(f"\n[dim]Active Holdings: {len(holdings)}[/dim]")
    elif show_realized and not show_unrealized:
        console.print(f"\n[dim]Total Positions: {len(realized_positions)}[/dim]")
    else:
        console.print(f"\n[dim]Active Holdings: {len(holdings)} | Closed Positions: {len(realized_positions)}[/dim]")


@app.command("trades")
def query_trades(
    account: Optional[str] = typer.Option(None, "--account", "-a", help="Filter by account"),
    asset: Optional[str] = typer.Option(None, "--asset", "-t", help="Filter by asset"),
    trade_type: Optional[str] = typer.Option(None, "--type", help="Filter by type: buy, sell, dividend"),
    direction: Optional[str] = typer.Option(None, "--direction", help="Filter by direction: long, short"),
    from_date: Optional[str] = typer.Option(None, "--from", help="Start date (YYYY-MM-DD)"),
    to_date: Optional[str] = typer.Option(None, "--to", help="End date (YYYY-MM-DD)"),
    sort_by: Optional[str] = typer.Option("date", "--sort", help="Sort by: date, asset (default: date)"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit results"),
    output: Optional[str] = typer.Option("table", "--output", "-o", help="Output format: table, json"),
    fullid: bool = typer.Option(False, "--fullid", help="Show full ID"),
    fullnote: bool = typer.Option(False, "--fullnote", help="Show full note instead of truncated"),
):
    """Query trade transactions."""
    data_dir = get_data_dir()

    if not data_dir.exists():
        console.print("[red]Error: ptracker not initialized. Run 'ptracker init' first.[/red]")
        raise typer.Exit(1)

    # Get all transactions
    transaction_repo = TransactionRepository(data_dir / "transactions.json")
    transactions = transaction_repo.find_all()

    if not transactions:
        console.print("[yellow]No transactions found.[/yellow]")
        return

    # Apply filters
    if account:
        transactions = [t for t in transactions if t['account'] == account]

    if asset:
        transactions = [t for t in transactions if t['asset'].upper() == asset.upper()]

    if trade_type:
        transactions = [t for t in transactions if t['type'] == trade_type.lower()]

    if direction:
        transactions = [t for t in transactions if t['direction'] == direction.lower()]

    if from_date:
        transactions = [t for t in transactions if t['datetime'][:10] >= from_date]

    if to_date:
        transactions = [t for t in transactions if t['datetime'][:10] <= to_date]

    if not transactions:
        console.print("[yellow]No transactions match the filters.[/yellow]")
        return

    # Sort
    if sort_by == "asset":
        transactions.sort(key=lambda t: (t['asset'], t['datetime']), reverse=True)
    else:  # date (default)
        transactions.sort(key=lambda t: t['datetime'], reverse=True)

    # Apply limit
    if limit:
        transactions = transactions[:limit]

    # Output as JSON if requested
    if output == "json":
        import json
        console.print(json.dumps(transactions, indent=2, default=str))
        return

    # Create table
    table = Table(title="Transactions", show_header=True, header_style="bold cyan")
    if fullid:
        table.add_column("ID", style="dim")
    table.add_column("Date", style="dim")
    table.add_column("Type")
    table.add_column("Action")
    table.add_column("Direction")
    table.add_column("Asset", style="bold")
    table.add_column("Quantity", justify="right")
    table.add_column("Price", justify="right")
    table.add_column("Currency")
    table.add_column("Fee", justify="right")
    table.add_column("Account")
    table.add_column("Note", style="dim")

    for tx in transactions:
        if tx['type'] == 'dividend':
            type_color = "blue"
            qty_display = "-"
        else:
            type_color = "green" if tx['type'] == 'buy' else "red"
            qty_display = f"{abs(tx['quantity']):.2f}"

        row = []
        if fullid:
            row.append(format_id(tx.get('id'), fullid))
        row.extend([
            tx['datetime'][:10],
            f"[{type_color}]{tx['type'].upper()}[/{type_color}]",
            tx['action'],
            tx['direction'][:1].upper(),
            tx['asset'],
            qty_display,
            f"{tx['price']:.2f}",
            tx['currency'],
            f"{tx.get('fee', 0):.2f}",
            tx['account'],
        ])
        row.append(format_note(tx.get('note'), fullnote))
        
        table.add_row(*row)

    console.print(table)
    console.print(f"\n[dim]Total: {len(transactions)} transaction(s)[/dim]")


if __name__ == "__main__":
    app()
