"""Trade management commands."""

from pathlib import Path
from datetime import datetime
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from ptracker.repositories import TransactionRepository, HoldingRepository, RealizedRepository, AccountRepository
from ptracker.services.validation import ValidationService
from ptracker.services.position_calculator import PositionCalculator, ClosureType
from ptracker.utils.id_generator import generate_id
from ptracker.config import ConfigManager
from ptracker.utils.color_helper import get_pnl_color

console = Console()
app = typer.Typer(help="Manage trades and transactions")


def get_data_dir() -> Path:
    """Get ptracker data directory."""
    return Path.home() / ".ptracker"


@app.command("add")
def add_trade(
    trade_type: str = typer.Argument(..., help="Trade type: buy, sell, or dividend"),
    asset: str = typer.Argument(..., help="Asset code (e.g., AAPL, 0700.HK)"),
    quantity: float = typer.Argument(..., help="Quantity (positive number, 0 for dividend)"),
    price: float = typer.Argument(..., help="Price per unit (for dividend: total dividend amount)"),
    currency: str = typer.Option(..., "--currency", "-c", help="Currency code (e.g., USD, HKD)"),
    action: str = typer.Option("open", "--action", "-a", help="Action: open, close, or income (for dividend)"),
    direction: str = typer.Option("long", "--direction", "-d", help="Direction: long or short"),
    account: Optional[str] = typer.Option(None, "--account", help="Account name"),
    date: Optional[str] = typer.Option(None, "--date", help="Transaction date (YYYY-MM-DD or ISO format)"),
    fee: float = typer.Option(0.0, "--fee", "-f", help="Transaction fee"),
    note: str = typer.Option("", "--note", "-n", help="Transaction note"),
):
    """Add a new trade transaction or dividend."""
    data_dir = get_data_dir()

    if not data_dir.exists():
        console.print("[red]Error: ptracker not initialized. Run 'ptracker init' first.[/red]")
        raise typer.Exit(1)

    # Validate trade type
    if trade_type.lower() not in ['buy', 'sell', 'dividend']:
        console.print(f"[red]Error: Invalid trade type '{trade_type}'. Must be 'buy', 'sell', or 'dividend'.[/red]")
        raise typer.Exit(1)

    trade_type = trade_type.lower()

    # Handle dividend type
    if trade_type == 'dividend':
        action = 'income'
        quantity = 0.0  # Dividends don't use quantity

    # Validate action
    if action.lower() not in ['open', 'close', 'income']:
        console.print(f"[red]Error: Invalid action '{action}'. Must be 'open', 'close', or 'income'.[/red]")
        raise typer.Exit(1)

    action = action.lower()

    # Validate direction
    if direction.lower() not in ['long', 'short']:
        console.print(f"[red]Error: Invalid direction '{direction}'. Must be 'long' or 'short'.[/red]")
        raise typer.Exit(1)

    direction = direction.lower()

    # Get account (from option or config)
    if not account:
        config_mgr = ConfigManager(data_dir / "config.toml")
        config_mgr.load()
        account = config_mgr.get_default_account()

        if not account:
            console.print("[red]Error: No account specified and no default account configured.[/red]")
            console.print("[dim]Use --account option or set default account with 'ptracker config set general.default_account <name>'[/dim]")
            raise typer.Exit(1)

    # Verify account exists
    account_repo = AccountRepository(data_dir / "accounts.json")
    if not account_repo.find_by_name(account):
        console.print(f"[red]Error: Account '{account}' not found.[/red]")
        console.print("[dim]Create it first with 'ptracker account add <name>'[/dim]")
        raise typer.Exit(1)

    # Get date (from option or current time)
    if date:
        try:
            if 'T' in date:
                tx_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
            else:
                tx_date = datetime.fromisoformat(f"{date}T00:00:00")
        except ValueError:
            console.print(f"[red]Error: Invalid date format '{date}'. Use YYYY-MM-DD or ISO format.[/red]")
            raise typer.Exit(1)
    else:
        tx_date = datetime.now()

    # Calculate signed quantity based on type/action/direction
    if trade_type == 'dividend':
        signed_quantity = 0.0
    elif trade_type == "buy" and action == "open" and direction == "long":
        signed_quantity = abs(quantity)
    elif trade_type == "buy" and action == "close" and direction == "short":
        signed_quantity = abs(quantity)
    elif trade_type == "sell" and action == "close" and direction == "long":
        signed_quantity = -abs(quantity)
    elif trade_type == "sell" and action == "open" and direction == "short":
        signed_quantity = -abs(quantity)
    else:
        console.print(f"[red]Error: Invalid combination of type/action/direction: {trade_type}/{action}/{direction}[/red]")
        raise typer.Exit(1)

    # Generate transaction ID
    tx_id = generate_id("txn")

    # Create transaction data
    transaction_data = {
        'id': tx_id,
        'datetime': tx_date.isoformat(),
        'type': trade_type,
        'action': action,
        'direction': direction,
        'asset': asset.upper(),
        'quantity': signed_quantity,
        'price': price,
        'currency': currency.upper(),
        'fee': fee,
        'account': account,
        'note': note
    }

    # Validate transaction
    validation_service = ValidationService()
    errors = validation_service.validate_transaction(transaction_data)
    if errors:
        console.print("[red]Validation errors:[/red]")
        for error in errors:
            console.print(f"  - {error}")
        raise typer.Exit(1)

    # Save transaction
    transaction_repo = TransactionRepository(data_dir / "transactions.json")
    transaction_repo.insert(transaction_data)

    # For dividends, update holding if exists
    if trade_type == 'dividend':
        holding_repo = HoldingRepository(data_dir / "holdings.json")
        existing_holding = holding_repo.find_by_asset_account(asset.upper(), account, direction)
        
        if existing_holding:
            # Reduce total_invested and recalculate avg_cost
            old_total_invested = existing_holding['total_invested']
            old_quantity = existing_holding['quantity']
            
            # Dividend reduces the cost basis
            new_total_invested = old_total_invested - price
            
            # Prevent negative total_invested
            if new_total_invested < 0:
                console.print(f"[yellow]⚠️  Warning: Dividend amount ({price}) exceeds total invested ({old_total_invested:.2f})[/yellow]")
                console.print(f"[yellow]   Setting total_invested to 0[/yellow]")
                new_total_invested = 0
            
            new_avg_cost = new_total_invested / old_quantity if old_quantity > 0 else 0
            
            # Update holding
            updated_holding = {
                **existing_holding,
                'total_invested': new_total_invested,
                'avg_cost': new_avg_cost,
                'last_updated': tx_date.strftime('%Y-%m-%d')
            }
            
            holding_repo.upsert(updated_holding)
            
            console.print(f"[green]✓[/green] Dividend recorded: [bold]{tx_id}[/bold]")
            console.print(f"  DIVIDEND {asset.upper()}: {price} {currency}")
            console.print(f"  Account: {account}")
            console.print(f"  Date: {tx_date.strftime('%Y-%m-%d %H:%M:%S')}")
            if note:
                console.print(f"  Note: {note}")
            console.print(f"\n[cyan]Position updated:[/cyan]")
            console.print(f"  Total invested: {old_total_invested:.2f} → {new_total_invested:.2f} {currency}")
            console.print(f"  Avg cost: {existing_holding['avg_cost']:.2f} → {new_avg_cost:.2f} {currency}")
        else:
            console.print(f"[green]✓[/green] Dividend recorded: [bold]{tx_id}[/bold]")
            console.print(f"  DIVIDEND {asset.upper()}: {price} {currency}")
            console.print(f"  Account: {account}")
            console.print(f"  Date: {tx_date.strftime('%Y-%m-%d %H:%M:%S')}")
            if note:
                console.print(f"  Note: {note}")
            console.print(f"\n[yellow]ℹ️  No active position found for {asset.upper()} in {account}[/yellow]")
        
        return

    # Recalculate position using incremental update
    holding_repo = HoldingRepository(data_dir / "holdings.json")
    realized_repo = RealizedRepository(data_dir / "realized.json")
    position_calc = PositionCalculator(transaction_repo, holding_repo, realized_repo)

    # Get existing holding
    existing_holding = holding_repo.find_by_asset_account(asset.upper(), account, direction)

    # Update position incrementally
    position_update = position_calc.update_position_incremental(transaction_data, existing_holding)

    if position_update:
        # Update or remove holding
        if position_update.holding and position_update.holding['quantity'] != 0:
            holding_repo.upsert(position_update.holding)
        elif position_update.closure_type in [ClosureType.FULL, ClosureType.REVERSED]:
            # Remove holding
            existing = holding_repo.find_by_asset_account(asset.upper(), account, direction)
            if existing:
                # Delete by finding and removing
                from tinydb import Query
                db, lock = holding_repo._write()
                try:
                    Q = Query()
                    db.remove(
                        (Q.asset == asset.upper()) &
                        (Q.account == account) &
                        (Q.direction == direction)
                    )
                finally:
                    db.close()
                    lock.release()

        # Save realized position if created
        if position_update.realized:
            realized_repo.insert(position_update.realized)

    # Success message
    console.print(f"[green]✓[/green] Transaction recorded: [bold]{tx_id}[/bold]")
    console.print(f"  {trade_type.upper()} {abs(signed_quantity)} {asset.upper()} @ {price} {currency}")
    console.print(f"  Action: {action}, Direction: {direction}")
    console.print(f"  Account: {account}")
    console.print(f"  Date: {tx_date.strftime('%Y-%m-%d %H:%M:%S')}")

    if position_update:
        if position_update.closure_type == ClosureType.FULL:
            console.print(f"\n[yellow]⚠️  Position fully closed[/yellow]")
            if position_update.realized:
                pnl = position_update.realized['realized_pnl']
                pnl_color = get_pnl_color(pnl, data_dir / "config.toml")
                console.print(f"  Realized P&L: [{pnl_color}]{pnl:+.2f}[/{pnl_color}] {currency}")
        elif position_update.closure_type == ClosureType.PARTIAL:
            console.print(f"\n[yellow]⚠️  Position partially closed[/yellow]")
        elif position_update.closure_type == ClosureType.REVERSED:
            console.print(f"\n[yellow]⚠️  Position reversed[/yellow]")



@app.command("list")
def list_trades(
    asset: Optional[str] = typer.Option(None, "--asset", "-a", help="Filter by asset"),
    account: Optional[str] = typer.Option(None, "--account", help="Filter by account"),
    from_date: Optional[str] = typer.Option(None, "--from", help="From date (YYYY-MM-DD)"),
    to_date: Optional[str] = typer.Option(None, "--to", help="To date (YYYY-MM-DD)"),
    trade_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by type (buy/sell/dividend)"),
    action: Optional[str] = typer.Option(None, "--action", help="Filter by action (open/close/income)"),
    direction: Optional[str] = typer.Option(None, "--direction", "-d", help="Filter by direction (long/short)"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum number of transactions to show"),
):
    """List transactions with optional filters."""
    data_dir = get_data_dir()

    if not data_dir.exists():
        console.print("[red]Error: ptracker not initialized. Run 'ptracker init' first.[/red]")
        raise typer.Exit(1)

    # Get all transactions
    transaction_repo = TransactionRepository(data_dir / "transactions.json")
    transactions = transaction_repo.find_all()

    if not transactions:
        console.print("[yellow]No transactions found. Add one with 'ptracker trade add'[/yellow]")
        return

    # Apply filters
    if asset:
        transactions = [t for t in transactions if t['asset'].upper() == asset.upper()]

    if account:
        transactions = [t for t in transactions if t['account'] == account]

    if from_date:
        transactions = [t for t in transactions if t['datetime'][:10] >= from_date]

    if to_date:
        transactions = [t for t in transactions if t['datetime'][:10] <= to_date]

    if trade_type:
        transactions = [t for t in transactions if t['type'] == trade_type.lower()]

    if action:
        transactions = [t for t in transactions if t['action'] == action.lower()]

    if direction:
        transactions = [t for t in transactions if t['direction'] == direction.lower()]

    if not transactions:
        console.print("[yellow]No transactions match the filters.[/yellow]")
        return

    # Sort by date (newest first)
    transactions.sort(key=lambda t: t['datetime'], reverse=True)

    # Limit results
    if len(transactions) > limit:
        transactions = transactions[:limit]
        console.print(f"[dim]Showing {limit} most recent transactions (total: {len(transactions)})[/dim]\n")

    # Create table
    table = Table(title="Transactions", show_header=True, header_style="bold cyan")
    table.add_column("Date", style="dim")
    table.add_column("Type")
    table.add_column("Asset", style="bold")
    table.add_column("Qty", justify="right")
    table.add_column("Price", justify="right")
    table.add_column("Currency")
    table.add_column("Action")
    table.add_column("Dir")
    table.add_column("Account")
    table.add_column("ID", style="dim")

    for tx in transactions:
        if tx['type'] == 'dividend':
            type_color = "blue"
            qty_display = "-"
        else:
            type_color = "green" if tx['type'] == 'buy' else "red"
            qty_display = f"{abs(tx['quantity']):.2f}"

        table.add_row(
            tx['datetime'][:10],
            f"[{type_color}]{tx['type'].upper()}[/{type_color}]",
            tx['asset'],
            qty_display,
            f"{tx['price']:.2f}",
            tx['currency'],
            tx['action'],
            tx['direction'][:1].upper(),
            tx['account'],
            tx['id'][:12] + "..."
        )

    console.print(table)
    console.print(f"\n[dim]Total: {len(transactions)} transaction(s)[/dim]")



if __name__ == "__main__":
    app()
