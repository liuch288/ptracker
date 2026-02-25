"""Account management commands."""

from pathlib import Path
from datetime import datetime
import typer
from rich.console import Console
from rich.table import Table
from ptracker.repositories import AccountRepository, HoldingRepository
from ptracker.utils.id_generator import generate_id

console = Console()
app = typer.Typer(help="Manage brokerage accounts")


def get_data_dir() -> Path:
    """Get ptracker data directory."""
    return Path.home() / ".ptracker"


@app.command("add")
def add_account(
    name: str = typer.Argument(..., help="Account name"),
    type: str = typer.Option("brokerage", "--type", "-t", help="Account type"),
    description: str = typer.Option("", "--desc", "-d", help="Account description"),
    currency: str = typer.Option("USD", "--currency", "-c", help="Base currency"),
):
    """Add a new account."""
    data_dir = get_data_dir()
    
    if not data_dir.exists():
        console.print("[red]Error: ptracker not initialized. Run 'ptracker init' first.[/red]")
        raise typer.Exit(1)
    
    # Initialize repository
    account_repo = AccountRepository(data_dir / "accounts.json")
    
    # Check if account already exists
    existing = account_repo.find_by_name(name)
    if existing:
        console.print(f"[red]Error: Account '{name}' already exists.[/red]")
        raise typer.Exit(1)
    
    # Generate account ID
    account_id = generate_id("acct")
    
    # Create account data
    account_data = {
        'id': account_id,
        'name': name,
        'type': type,
        'description': description,
        'currency': currency,
        'created_at': datetime.now().isoformat()
    }
    
    # Save account
    account_repo.insert(account_data)
    
    # Success message
    console.print(f"[green]✓[/green] Account created: [bold]{name}[/bold]")
    console.print(f"  ID: {account_id}")
    console.print(f"  Type: {type}")
    console.print(f"  Currency: {currency}")
    if description:
        console.print(f"  Description: {description}")


@app.command("list")
def list_accounts():
    """List all accounts."""
    data_dir = get_data_dir()
    
    if not data_dir.exists():
        console.print("[red]Error: ptracker not initialized. Run 'ptracker init' first.[/red]")
        raise typer.Exit(1)
    
    # Initialize repository
    account_repo = AccountRepository(data_dir / "accounts.json")
    
    # Get all accounts
    accounts = account_repo.find_all()
    
    if not accounts:
        console.print("[yellow]No accounts found. Add one with 'ptracker account add <name>'[/yellow]")
        return
    
    # Create table
    table = Table(title="Accounts", show_header=True, header_style="bold cyan")
    table.add_column("Name", style="bold")
    table.add_column("Type")
    table.add_column("Currency")
    table.add_column("Description")
    table.add_column("Created", style="dim")
    
    for account in sorted(accounts, key=lambda a: a['name']):
        created = account['created_at'][:10] if 'created_at' in account else 'N/A'
        table.add_row(
            account['name'],
            account.get('type', 'N/A'),
            account.get('currency', 'N/A'),
            account.get('description', ''),
            created
        )
    
    console.print(table)
    console.print(f"\n[dim]Total: {len(accounts)} account(s)[/dim]")


@app.command("query")
def query_account(
    name: str = typer.Argument(..., help="Account name to query")
):
    """Query account details and associated holdings."""
    data_dir = get_data_dir()
    
    if not data_dir.exists():
        console.print("[red]Error: ptracker not initialized. Run 'ptracker init' first.[/red]")
        raise typer.Exit(1)
    
    # Initialize repositories
    account_repo = AccountRepository(data_dir / "accounts.json")
    holding_repo = HoldingRepository(data_dir / "holdings.json")
    
    # Find account
    account = account_repo.find_by_name(name)
    if not account:
        console.print(f"[red]Error: Account '{name}' not found.[/red]")
        raise typer.Exit(1)
    
    # Display account details
    console.print(f"\n[bold cyan]Account: {account['name']}[/bold cyan]")
    console.print(f"  ID: {account['id']}")
    console.print(f"  Type: {account.get('type', 'N/A')}")
    console.print(f"  Currency: {account.get('currency', 'N/A')}")
    if account.get('description'):
        console.print(f"  Description: {account['description']}")
    console.print(f"  Created: {account.get('created_at', 'N/A')[:10]}")
    
    # Get holdings for this account
    all_holdings = holding_repo.find_all()
    account_holdings = [h for h in all_holdings if h['account'] == name]
    
    if account_holdings:
        console.print(f"\n[bold]Holdings ({len(account_holdings)}):[/bold]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Asset")
        table.add_column("Direction")
        table.add_column("Quantity", justify="right")
        table.add_column("Avg Cost", justify="right")
        table.add_column("Total Invested", justify="right")
        
        for holding in sorted(account_holdings, key=lambda h: h['asset']):
            table.add_row(
                holding['asset'],
                holding['direction'],
                f"{holding['quantity']:.2f}",
                f"{holding['avg_cost']:.2f}",
                f"{holding['total_invested']:.2f}"
            )
        
        console.print(table)
    else:
        console.print("\n[dim]No holdings in this account[/dim]")


@app.command("delete")
def delete_account(
    name: str = typer.Argument(..., help="Account name to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Force delete without confirmation")
):
    """Delete an account (only if no transactions exist)."""
    data_dir = get_data_dir()
    
    if not data_dir.exists():
        console.print("[red]Error: ptracker not initialized. Run 'ptracker init' first.[/red]")
        raise typer.Exit(1)
    
    # Initialize repositories
    account_repo = AccountRepository(data_dir / "accounts.json")
    
    # Find account
    account = account_repo.find_by_name(name)
    if not account:
        console.print(f"[red]Error: Account '{name}' not found.[/red]")
        raise typer.Exit(1)
    
    # Check for transactions
    from ptracker.repositories import TransactionRepository
    from ptracker.services.validation import ValidationService
    
    transaction_repo = TransactionRepository(data_dir / "transactions.json")
    validation_service = ValidationService(transaction_repo)
    
    if not validation_service.validate_account_deletion(name):
        console.print(f"[red]Error: Cannot delete account '{name}' - it has associated transactions.[/red]")
        console.print("[dim]Delete all transactions for this account first.[/dim]")
        raise typer.Exit(1)
    
    # Confirm deletion
    if not force:
        confirm = typer.confirm(f"Are you sure you want to delete account '{name}'?")
        if not confirm:
            console.print("[yellow]Deletion cancelled.[/yellow]")
            return
    
    # Delete account
    account_repo.delete(account['id'])
    
    console.print(f"[green]✓[/green] Account '{name}' deleted successfully.")
