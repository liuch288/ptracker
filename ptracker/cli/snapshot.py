"""Snapshot commands for capturing portfolio state."""

from pathlib import Path
from datetime import datetime
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from ptracker.repositories import HoldingRepository, AccountRepository, RealizedRepository
from ptracker.repositories.snapshot import SnapshotRepository
from ptracker.services.price_service import PriceService
from ptracker.services.pnl_calculator import PnLCalculator
from ptracker.models.snapshot import PortfolioSnapshot, AccountSnapshot, HoldingSnapshot
from ptracker.config import ConfigManager


console = Console()
app = typer.Typer(help="Capture and manage portfolio snapshots")


def get_data_dir() -> Path:
    """Get ptracker data directory."""
    return Path.home() / ".ptracker"


def get_snapshot_repo() -> SnapshotRepository:
    """Get snapshot repository instance."""
    data_dir = get_data_dir()
    return SnapshotRepository(data_dir / "snapshots.json")


def capture_snapshot() -> PortfolioSnapshot:
    """Capture current portfolio state as a snapshot.
    
    Returns:
        PortfolioSnapshot object
    """
    data_dir = get_data_dir()
    snapshot_time = datetime.now()
    
    # Initialize repositories
    holding_repo = HoldingRepository(data_dir / "holdings.json")
    account_repo = AccountRepository(data_dir / "accounts.json")
    realized_repo = RealizedRepository(data_dir / "realized.json")
    
    # Initialize services
    price_service = PriceService()
    pnl_calc = PnLCalculator(price_service)
    
    # Get config for default currency
    config = ConfigManager(data_dir / "config.toml")
    base_currency = config.get_default_currency()
    
    # Fetch all data
    holdings = holding_repo.find_all()
    accounts = account_repo.find_all()
    realized_positions = realized_repo.find_all()
    
    # Calculate total realized P&L
    total_realized_pnl = sum(
        r.get('realized_pnl', 0.0) for r in realized_positions
    )
    
    # Get currency rates
    currency_rates = {}
    currencies = set(a.get('currency', 'USD') for a in accounts)
    currencies.add(base_currency)
    
    for curr in currencies:
        if curr != base_currency:
            rate = price_service.get_exchange_rate(curr, base_currency)
            currency_rates[curr] = rate
    currency_rates[base_currency] = 1.0
    
    # Build account snapshots
    account_snapshots = []
    currency_breakdown = {}
    
    for account in accounts:
        account_name = account['name']
        account_currency = account.get('currency', 'USD')
        
        # Get holdings for this account
        account_holdings = [h for h in holdings if h['account'] == account_name]
        
        # Calculate account totals (convert to base currency)
        total_deposit = account.get('total_deposit', 0.0)
        total_withdrawal = account.get('total_withdrawal', 0.0)
        
        # Convert to base currency if needed
        if account_currency != base_currency:
            rate = currency_rates.get(account_currency, 1.0)
            total_deposit_base = total_deposit * rate
            total_withdrawal_base = total_withdrawal * rate
        else:
            total_deposit_base = total_deposit
            total_withdrawal_base = total_withdrawal
        
        net_deposit = total_deposit_base - total_withdrawal_base
        
        # Process holdings and calculate values
        holding_snapshots = []
        total_market_value = 0.0
        total_cost = 0.0
        total_unrealized_pnl = 0.0
        
        for holding in account_holdings:
            asset = holding['asset']
            quantity = holding['quantity']
            direction = holding['direction']
            avg_cost = holding['avg_cost']
            total_invested = holding['total_invested']
            holding_currency = holding.get('currency', account_currency)
            
            # Get current price
            try:
                price_quote = price_service.get_price(asset)
                current_price = price_quote.price if price_quote else avg_cost
            except Exception:
                current_price = avg_cost
            
            # Calculate market value and unrealized P&L
            market_value = current_price * quantity
            unrealized_pnl = pnl_calc.calculate_unrealized_pnl(holding, current_price)
            return_pct = pnl_calc.calculate_return_pct(unrealized_pnl, total_invested)
            
            # Convert to base currency if needed
            if holding_currency != base_currency:
                rate = currency_rates.get(holding_currency, 1.0)
                market_value_base = market_value * rate
                total_cost_base = total_invested * rate
                unrealized_pnl_base = unrealized_pnl * rate
            else:
                market_value_base = market_value
                total_cost_base = total_invested
                unrealized_pnl_base = unrealized_pnl
            
            holding_snapshot = HoldingSnapshot(
                asset=asset,
                account=account_name,
                direction=direction,
                quantity=quantity,
                avg_cost=avg_cost,
                total_invested=total_invested,
                currency=holding_currency,
                first_open_date=holding['first_open_date'],
                last_updated=holding['last_updated'],
                note=holding.get('note', ''),
                status=holding.get('status', 'active'),
                current_price=current_price,
                market_value=market_value_base,
                unrealized_pnl=unrealized_pnl_base,
                return_pct=return_pct
            )
            holding_snapshots.append(holding_snapshot)
            
            total_market_value += market_value_base
            total_cost += total_cost_base
            total_unrealized_pnl += unrealized_pnl_base
            
            # Track currency breakdown
            if holding_currency not in currency_breakdown:
                currency_breakdown[holding_currency] = 0.0
            currency_breakdown[holding_currency] += market_value_base
        
        # Create account snapshot
        account_snapshot = AccountSnapshot(
            name=account_name,
            currency=account_currency,
            type=account.get('type', 'brokerage'),
            description=account.get('description', ''),
            total_deposit=total_deposit,
            total_withdrawal=total_withdrawal,
            net_deposit=net_deposit,
            total_market_value=total_market_value,
            total_cost=total_cost,
            total_unrealized_pnl=total_unrealized_pnl,
            holdings=holding_snapshots
        )
        account_snapshots.append(account_snapshot)
    
    # Calculate portfolio totals
    portfolio_total_deposit = sum(a.get('total_deposit', 0.0) for a in accounts)
    portfolio_total_withdrawal = sum(a.get('total_withdrawal', 0.0) for a in accounts)
    portfolio_net_deposit = portfolio_total_deposit - portfolio_total_withdrawal
    
    portfolio_total_market_value = sum(
        acc.total_market_value for acc in account_snapshots
    )
    portfolio_total_cost = sum(
        acc.total_cost for acc in account_snapshots
    )
    portfolio_total_unrealized_pnl = sum(
        acc.total_unrealized_pnl for acc in account_snapshots
    )
    
    # Calculate total return percentage
    # Use max to avoid division by zero
    divisor = max(portfolio_total_cost, 1e-10)
    total_return_pct = (
        (portfolio_total_unrealized_pnl + total_realized_pnl) 
        / divisor * 100.0
    )
    # Set to 0.0 if cost is actually zero or negative
    if portfolio_total_cost <= 0:
        total_return_pct = 0.0
    
    # Get price timestamp
    price_timestamp = None
    price_quote_sample = None
    if holdings:
        sample_asset = holdings[0]['asset']
        price_quote_sample = price_service.get_price(sample_asset)
    if price_quote_sample:
        price_timestamp = price_quote_sample.timestamp.isoformat()
    
    # Create portfolio snapshot
    snapshot = PortfolioSnapshot(
        version="1.0",
        snapshot_time=snapshot_time.isoformat(),
        total_deposit=portfolio_total_deposit,
        total_withdrawal=portfolio_total_withdrawal,
        net_deposit=portfolio_net_deposit,
        total_market_value=portfolio_total_market_value,
        total_cost=portfolio_total_cost,
        total_unrealized_pnl=portfolio_total_unrealized_pnl,
        total_realized_pnl=total_realized_pnl,
        total_return_pct=total_return_pct,
        account_count=len(accounts),
        holding_count=len(holdings),
        currency_breakdown=currency_breakdown,
        accounts=account_snapshots,
        price_source="yfinance",
        price_timestamp=price_timestamp,
        currency_rates=currency_rates
    )
    
    return snapshot


@app.command()
def take(
    save: bool = typer.Option(True, "--save/--no-save", help="Save snapshot to database"),
    show: bool = typer.Option(True, "--show/--no-show", help="Display snapshot details"),
):
    """Capture a snapshot of current portfolio state."""
    data_dir = get_data_dir()
    
    if not data_dir.exists():
        console.print("[red]Error: ptracker not initialized. Run 'ptracker init' first.[/red]")
        raise typer.Exit(1)
    
    console.print("[cyan]Capturing portfolio snapshot...[/cyan]")
    
    try:
        snapshot = capture_snapshot()
        
        if save:
            # Save to repository
            snapshot_repo = get_snapshot_repo()
            snapshot_id = snapshot_repo.save_snapshot(snapshot.model_dump())
            console.print(f"[green]Snapshot saved: {snapshot_id}[/green]")
        
        if show:
            # Display summary
            display_snapshot(snapshot)
        
    except Exception as e:
        console.print(f"[red]Error capturing snapshot: {e}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_snapshots(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of snapshots to show"),
):
    """List recent snapshots."""
    data_dir = get_data_dir()
    
    if not data_dir.exists():
        console.print("[red]Error: ptracker not initialized. Run 'ptracker init' first.[/red]")
        raise typer.Exit(1)
    
    snapshot_repo = get_snapshot_repo()
    snapshots = snapshot_repo.find_recent(limit)
    
    if not snapshots:
        console.print("[yellow]No snapshots found.[/yellow]")
        return
    
    # Display table
    table = Table(title="Recent Snapshots", show_header=True, header_style="bold cyan")
    table.add_column("Time", style="bold")
    table.add_column("Market Value", justify="right")
    table.add_column("Unrealized P&L", justify="right")
    table.add_column("Return %", justify="right")
    table.add_column("Holdings", justify="right")
    
    for s in snapshots:
        time_str = s.get('snapshot_time', '')[:19]
        mv = s.get('total_market_value', 0)
        upnl = s.get('total_unrealized_pnl', 0)
        ret = s.get('total_return_pct', 0)
        hc = s.get('holding_count', 0)
        
        # Color for P&L
        pnl_color = "green" if upnl >= 0 else "red"
        ret_color = "green" if ret >= 0 else "red"
        
        table.add_row(
            time_str,
            f"${mv:,.2f}",
            f"[{pnl_color}]${upnl:,.2f}[/{pnl_color}]",
            f"[{ret_color}]{ret:,.2f}%[/{ret_color}]",
            str(hc)
        )
    
    console.print(table)


@app.command("show")
def show_snapshot(
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Snapshot date (YYYY-MM-DD)"),
    latest: bool = typer.Option(True, "--latest/--no-latest", help="Show latest snapshot"),
):
    """Show details of a specific snapshot."""
    data_dir = get_data_dir()
    
    if not data_dir.exists():
        console.print("[red]Error: ptracker not initialized. Run 'ptracker init' first.[/red]")
        raise typer.Exit(1)
    
    snapshot_repo = get_snapshot_repo()
    
    if latest or not date:
        snapshot = snapshot_repo.find_latest()
    else:
        snapshot = snapshot_repo.find_by_date(date)
    
    if not snapshot:
        console.print("[yellow]Snapshot not found.[/yellow]")
        return
    
    # Convert dict back to model for display
    portfolio = PortfolioSnapshot(**snapshot)
    display_snapshot(portfolio)


def display_snapshot(snapshot: PortfolioSnapshot):
    """Display snapshot details."""
    console.print(f"\n[bold cyan]Portfolio Snapshot[/bold cyan]")
    console.print(f"Time: {snapshot.snapshot_time[:19]}")
    console.print(f"Version: {snapshot.version}")
    
    # Summary table
    table = Table(show_header=False, box=None)
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    
    table.add_row("Total Deposit", f"${snapshot.total_deposit:,.2f}")
    table.add_row("Total Withdrawal", f"${snapshot.total_withdrawal:,.2f}")
    table.add_row("Net Deposit", f"${snapshot.net_deposit:,.2f}")
    table.add_row("---", "---")
    table.add_row("Total Market Value", f"${snapshot.total_market_value:,.2f}")
    table.add_row("Total Cost", f"${snapshot.total_cost:,.2f}")
    table.add_row("Unrealized P&L", f"${snapshot.total_unrealized_pnl:,.2f}")
    table.add_row("Realized P&L", f"${snapshot.total_realized_pnl:,.2f}")
    table.add_row("---", "---")
    pnl_color = "green" if snapshot.total_unrealized_pnl >= 0 else "red"
    ret_color = "green" if snapshot.total_return_pct >= 0 else "red"
    table.add_row(
        "Total Return %",
        f"[{ret_color}]{snapshot.total_return_pct:,.2f}%[/{ret_color}]"
    )
    table.add_row("Account Count", str(snapshot.account_count))
    table.add_row("Holding Count", str(snapshot.holding_count))
    
    console.print(table)
    
    # Currency breakdown
    if snapshot.currency_breakdown:
        console.print("\n[bold]Currency Breakdown:[/bold]")
        for curr, value in snapshot.currency_breakdown.items():
            console.print(f"  {curr}: ${value:,.2f}")
    
    # Account breakdown
    if snapshot.accounts:
        console.print("\n[bold cyan]Account Details:[/bold cyan]")
        for account in snapshot.accounts:
            console.print(f"\n[bold]{account.name}[/bold] ({account.currency})")
            console.print(f"  Net Deposit: ${account.net_deposit:,.2f}")
            console.print(f"  Market Value: ${account.total_market_value:,.2f}")
            console.print(f"  Unrealized P&L: ${account.total_unrealized_pnl:,.2f}")
            
            if account.holdings:
                console.print("  Holdings:")
                for h in account.holdings:
                    h_pnl_color = "green" if h.unrealized_pnl >= 0 else "red"
                    h_ret_color = "green" if h.return_pct >= 0 else "red"
                    console.print(
                        f"    {h.asset}: {h.quantity} @ ${h.current_price:.2f} "
                        f"(MV: ${h.market_value:,.2f}, "
                        f"P&L: [${h.unrealized_pnl:,.2f}], "
                        f"Return: [{h_ret_color}]{h.return_pct:,.2f}%[/{h_ret_color}])"
                    )


@app.command("prune")
def prune_snapshots(
    keep: int = typer.Option(30, "--keep", "-k", help="Number of snapshots to keep"),
):
    """Remove old snapshots, keeping only the most recent ones."""
    data_dir = get_data_dir()
    
    if not data_dir.exists():
        console.print("[red]Error: ptracker not initialized. Run 'ptracker init' first.[/red]")
        raise typer.Exit(1)
    
    snapshot_repo = get_snapshot_repo()
    deleted = snapshot_repo.delete_old_snapshots(keep)
    
    if deleted > 0:
        console.print(f"[green]Deleted {deleted} old snapshot(s).[/green]")
    else:
        console.print("[yellow]No snapshots to delete.[/yellow]")
