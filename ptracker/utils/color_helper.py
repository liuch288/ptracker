"""Color helper utilities for ptracker."""

from pathlib import Path
from ptracker.config import ConfigManager


def get_pnl_color(value: float, config_path: Path = None) -> str:
    """Get color for P&L value based on user preference.
    
    Args:
        value: P&L value (positive for profit, negative for loss)
        config_path: Path to config file (defaults to ~/.ptracker/config.toml)
        
    Returns:
        Color name ('green' or 'red')
    """
    if config_path is None:
        config_path = Path.home() / ".ptracker" / "config.toml"
    
    config_mgr = ConfigManager(config_path)
    color_scheme = config_mgr.get_color_scheme()
    
    # green_up: green for profit, red for loss (Western style)
    # red_up: red for profit, green for loss (Chinese style)
    if color_scheme == "red_up":
        return "red" if value >= 0 else "green"
    else:  # default to green_up
        return "green" if value >= 0 else "red"
