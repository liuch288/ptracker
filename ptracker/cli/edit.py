"""Edit command for modifying existing records."""

from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from ptracker.repositories import TransactionRepository, HoldingRepository, RealizedRepository, AccountRepository
from ptracker.services.validation import ValidationService

console = Console()
app = typer.Typer(help="Edit existing records")

# 定义可编辑字段
EDITABLE_FIELDS = {
    'trans': ['price', 'fee', 'account', 'note'],
    'holding': ['account', 'note', 'status'],
    'realized': ['account', 'note'],
}


def get_data_dir() -> Path:
    """Get ptracker data directory."""
    return Path.home() / ".ptracker"


def parse_field_args(field_args: list[str]) -> dict:
    """Parse field=value arguments into a dictionary.
    
    Args:
        field_args: List of "field=value" strings
        
    Returns:
        Dictionary of field names to parsed values
    """
    result = {}
    for arg in field_args:
        if '=' not in arg:
            raise ValueError(f"Invalid field format: '{arg}'. Use 'field=value'")
        
        field, _, value = arg.partition('=')
        if not field:
            raise ValueError(f"Field name cannot be empty in '{arg}'")
        
        result[field.strip()] = value.strip()
    
    return result


def validate_and_convert_field(
    record_type: str,
    field: str,
    value: str,
    original_record: dict
) -> tuple:
    """Validate and convert field value to appropriate type.
    
    Args:
        record_type: Type of record (trans, holding, realized)
        field: Field name
        value: String value from CLI
        original_record: Original record for reference
        
    Returns:
        Tuple of (converted_value, error_message)
    """
    if record_type == 'trans':
        if field == 'price':
            try:
                return float(value), None
            except ValueError:
                return None, f"Invalid price value: '{value}'. Must be a number."
        
        elif field == 'fee':
            try:
                return float(value), None
            except ValueError:
                return None, f"Invalid fee value: '{value}'. Must be a number."
        
        elif field == 'account':
            # Verify account exists
            data_dir = get_data_dir()
            account_repo = AccountRepository(data_dir / "accounts.json")
            if not account_repo.find_by_name(value):
                return None, f"Account '{value}' does not exist."
            return value, None
        
        elif field == 'note':
            return value, None
    
    elif record_type == 'holding':
        if field == 'account':
            data_dir = get_data_dir()
            account_repo = AccountRepository(data_dir / "accounts.json")
            if not account_repo.find_by_name(value):
                return None, f"Account '{value}' does not exist."
            return value, None
        
        elif field == 'note':
            return value, None
        
        elif field == 'status':
            if value not in ['active', 'closed']:
                return None, f"Invalid status: '{value}'. Must be 'active' or 'closed'."
            return value, None
    
    elif record_type == 'realized':
        if field == 'account':
            data_dir = get_data_dir()
            account_repo = AccountRepository(data_dir / "accounts.json")
            if not account_repo.find_by_name(value):
                return None, f"Account '{value}' does not exist."
            return value, None
        
        elif field == 'note':
            return value, None
    
    return None, f"Unknown field: {field}"


@app.command("edit")
def edit_record(
    record_type: str = typer.Argument(
        ...,
        help="Record type: trans, holding, or realized",
        case_sensitive=False
    ),
    id: Optional[str] = typer.Option(
        None,
        "--id",
        "-i",
        help="Record ID to edit (for trans/realized/holding)"
    ),
    asset: Optional[str] = typer.Option(
        None,
        "--asset",
        "-a",
        help="Asset code (for holding, optional if --id is used)"
    ),
    account: Optional[str] = typer.Option(
        None,
        "--account",
        help="Account name (for holding, optional if --id is used)"
    ),
    direction: Optional[str] = typer.Option(
        None,
        "--direction",
        "-d",
        help="Direction: long or short (for holding, optional if --id is used)"
    ),
    fields: list[str] = typer.Argument(
        ...,
        help="Fields to update in format field=value (e.g., price=100.5)"
    ),
):
    """Edit an existing record.
    
    Examples:
        ptracker edit trans --id txn_xxx price=150.0 fee=5.0
        ptracker edit holding --id hold_xxx note="Updated note"
        ptracker edit holding --asset 700.HK --account longbridge note="Updated note"
        ptracker edit realized --id real_xxx note="Updated note"
    """
    data_dir = get_data_dir()

    if not data_dir.exists():
        console.print("[red]Error: ptracker not initialized. Run 'ptracker init' first.[/red]")
        raise typer.Exit(1)

    # Normalize record type
    record_type = record_type.lower()
    if record_type not in ['trans', 'holding', 'realized']:
        console.print(f"[red]Error: Invalid record type '{record_type}'. Must be one of: trans, holding, realized[/red]")
        raise typer.Exit(1)

    # Validate required arguments based on record type
    if record_type in ['trans', 'realized']:
        if not id:
            console.print(f"[red]Error: --id is required for {record_type}.[/red]")
            raise typer.Exit(1)
    elif record_type == 'holding':
        # For holding, either --id or (--asset + --account) is required
        if id:
            # Using --id mode, other options are optional
            pass
        elif not asset or not account:
            console.print(f"[red]Error: For holding, either --id or both --asset and --account are required.[/red]")
            raise typer.Exit(1)

    # Parse field arguments
    try:
        field_updates = parse_field_args(fields)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    if not field_updates:
        console.print("[red]Error: No fields to update. Provide at least one field=value.[/red]")
        raise typer.Exit(1)

    # Get editable fields for this record type
    editable = EDITABLE_FIELDS.get(record_type, [])

    # Validate that all fields are editable
    for field in field_updates.keys():
        if field not in editable:
            console.print(f"[red]Error: Field '{field}' is not editable for {record_type}.[/red]")
            console.print(f"[dim]Editable fields: {', '.join(editable)}[/dim]")
            raise typer.Exit(1)

    # Find and update based on record type
    if record_type == 'trans':
        return edit_transaction(data_dir, id, field_updates)
    elif record_type == 'holding':
        return edit_holding(data_dir, id, asset, account, direction, field_updates)
    elif record_type == 'realized':
        return edit_realized(data_dir, id, field_updates)


def edit_transaction(data_dir: Path, tx_id: str, field_updates: dict):
    """Edit a transaction record."""
    transaction_repo = TransactionRepository(data_dir / "transactions.json")
    
    # Find the transaction
    transaction = transaction_repo.find_by_id(tx_id)
    if not transaction:
        console.print(f"[red]Error: Transaction '{tx_id}' not found.[/red]")
        raise typer.Exit(1)

    # Validate and convert each field
    validated_updates = {}
    for field, value in field_updates.items():
        converted, error = validate_and_convert_field('trans', field, value, transaction)
        if error:
            console.print(f"[red]Error: {error}[/red]")
            raise typer.Exit(1)
        validated_updates[field] = converted

    # Perform update
    success = transaction_repo.update(tx_id, validated_updates)
    
    if success:
        console.print(f"[green]✓[/green] Transaction updated: [bold]{tx_id}[/bold]")
        for field, value in validated_updates.items():
            console.print(f"  {field}: {transaction.get(field)} → {value}")
    else:
        console.print(f"[red]Error: Failed to update transaction '{tx_id}'.[/red]")
        raise typer.Exit(1)


def edit_holding(data_dir: Path, holding_id: Optional[str], asset: Optional[str], account: Optional[str], direction: Optional[str], field_updates: dict):
    """Edit a holding record."""
    holding_repo = HoldingRepository(data_dir / "holdings.json")
    
    # Find the holding: by id OR by asset/account/direction
    holding = None
    if holding_id:
        # Use ID to find holding
        holding = holding_repo.find_by_id(holding_id)
    else:
        # Use asset/account/direction to find holding (backward compatible)
        direction = direction or "long"
        holding = holding_repo.find_by_asset_account(asset.upper(), account, direction)
    
    if not holding:
        if holding_id:
            console.print(f"[red]Error: Holding '{holding_id}' not found.[/red]")
        else:
            console.print(f"[red]Error: Holding not found for {asset} in {account} (direction: {direction}).[/red]")
        raise typer.Exit(1)

    # Validate and convert each field
    validated_updates = {}
    for field, value in field_updates.items():
        converted, error = validate_and_convert_field('holding', field, value, holding)
        if error:
            console.print(f"[red]Error: {error}[/red]")
            raise typer.Exit(1)
        validated_updates[field] = converted

    # Use update_by_id if we have the id, otherwise use the old method
    if holding_id:
        success = holding_repo.update_by_id(holding['id'], validated_updates)
        identifier = holding_id
    else:
        # For backward compatibility, use the old method
        from tinydb import Query
        db, lock = holding_repo._write()
        try:
            Q = Query()
            db.remove(
                (Q.asset == asset.upper()) &
                (Q.account == account) &
                (Q.direction == direction)
            )
            # Insert updated holding
            updated_holding = {**holding, **validated_updates}
            db.insert(updated_holding)
            success = True
        finally:
            db.close()
            lock.release()
        identifier = f"{asset.upper()}/{account}"
    
    if success:
        console.print(f"[green]✓[/green] Holding updated: [bold]{identifier}[/bold]")
        for field, value in validated_updates.items():
            console.print(f"  {field}: {holding.get(field)} → {value}")
    else:
        console.print(f"[red]Error: Failed to update holding.[/red]")
        raise typer.Exit(1)


def edit_realized(data_dir: Path, realized_id: str, field_updates: dict):
    """Edit a realized position record."""
    realized_repo = RealizedRepository(data_dir / "realized.json")
    
    # Find the realized position
    realized = realized_repo.find_by_id(realized_id)
    if not realized:
        console.print(f"[red]Error: Realized position '{realized_id}' not found.[/red]")
        raise typer.Exit(1)

    # Validate and convert each field
    validated_updates = {}
    for field, value in field_updates.items():
        converted, error = validate_and_convert_field('realized', field, value, realized)
        if error:
            console.print(f"[red]Error: {error}[/red]")
            raise typer.Exit(1)
        validated_updates[field] = converted

    # Perform update
    success = realized_repo.update(realized_id, validated_updates)
    
    if success:
        console.print(f"[green]✓[/green] Realized position updated: [bold]{realized_id}[/bold]")
        for field, value in validated_updates.items():
            console.print(f"  {field}: {realized.get(field)} → {value}")
    else:
        console.print(f"[red]Error: Failed to update realized position '{realized_id}'.[/red]")
        raise typer.Exit(1)


# Export the main command for use in main.py
edit_record = edit_record  # The typer command is already named edit_record
