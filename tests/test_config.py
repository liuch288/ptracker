"""Tests for configuration manager."""

import tempfile
from pathlib import Path
from ptracker.config import ConfigManager


def test_config_manager():
    """Test ConfigManager."""
    # Create temporary config file
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.toml"
        
        # Test initialization with missing file
        config_mgr = ConfigManager(config_path)
        config = config_mgr.load()
        assert config['general']['default_currency'] == 'USD'
        print("✓ Config loaded with defaults")
        
        # Test get method
        currency = config_mgr.get('general.default_currency')
        assert currency == 'USD'
        print(f"✓ Get config value: default_currency = {currency}")
        
        # Test set method
        config_mgr.set('general.default_currency', 'HKD')
        assert config_mgr.get('general.default_currency') == 'HKD'
        print("✓ Set config value: default_currency = HKD")
        
        # Test helper methods
        assert config_mgr.get_default_currency() == 'HKD'
        print(f"✓ get_default_currency() = {config_mgr.get_default_currency()}")
        
        assert config_mgr.get_default_account() is None
        print(f"✓ get_default_account() = {config_mgr.get_default_account()}")
        
        assert config_mgr.get_cost_basis_method() == 'average'
        print(f"✓ get_cost_basis_method() = {config_mgr.get_cost_basis_method()}")
        
        # Test persistence
        config_mgr2 = ConfigManager(config_path)
        config_mgr2.load()
        assert config_mgr2.get('general.default_currency') == 'HKD'
        print("✓ Config persisted to file")


if __name__ == '__main__':
    test_config_manager()
    print("\n✅ All config tests passed!")
