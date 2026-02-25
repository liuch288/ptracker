"""Configuration management for ptracker."""

from pathlib import Path
from typing import Any, Dict, Optional
import toml


DEFAULT_CONFIG = {
    "general": {
        "default_currency": "USD",
        "default_account": "",
        "cost_basis_method": "average",
    },
    "display": {
        "date_format": "%Y-%m-%d %H:%M:%S",
        "decimal_places": 2,
    },
    "api": {
        "price_cache_seconds": 60,
        "request_timeout": 10,
    },
}


class ConfigManager:
    """Manage system configuration with TOML format."""
    
    def __init__(self, config_path: Path):
        """Initialize with config file path.
        
        Args:
            config_path: Path to config.toml file
        """
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Configuration dictionary
        """
        if self.config_path.exists():
            try:
                self._config = toml.load(self.config_path)
            except Exception:
                # If corrupted, use defaults
                self._config = DEFAULT_CONFIG.copy()
        else:
            # If missing, use defaults
            self._config = DEFAULT_CONFIG.copy()
        
        return self._config
    
    def save(self, config: Dict[str, Any]) -> None:
        """Save configuration to file.
        
        Args:
            config: Configuration dictionary to save
        """
        self._config = config
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            toml.dump(config, f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key in dot notation (e.g., 'general.default_currency')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        if not self._config:
            self.load()
        
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value.
        
        Args:
            key: Configuration key in dot notation (e.g., 'general.default_currency')
            value: Value to set
        """
        if not self._config:
            self.load()
        
        keys = key.split('.')
        config = self._config
        
        # Navigate to the parent dict
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        
        # Save to file
        self.save(self._config)
    
    def get_default_currency(self) -> str:
        """Get default currency setting.
        
        Returns:
            Default currency code (e.g., 'USD')
        """
        return self.get('general.default_currency', 'USD')
    
    def get_default_account(self) -> Optional[str]:
        """Get default account setting.
        
        Returns:
            Default account name or None
        """
        account = self.get('general.default_account', '')
        return account if account else None
    
    def get_cost_basis_method(self) -> str:
        """Get cost basis calculation method.
        
        Returns:
            Cost basis method ('average' or 'fifo')
        """
        return self.get('general.cost_basis_method', 'average')
