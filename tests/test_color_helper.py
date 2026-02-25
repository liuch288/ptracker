"""Tests for color helper utilities."""

import tempfile
from pathlib import Path
from ptracker.config import ConfigManager, DEFAULT_CONFIG
from ptracker.utils.color_helper import get_pnl_color


def test_green_up_scheme():
    """Test green_up color scheme (Western style)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.toml"
        
        # Create config with green_up scheme
        config = DEFAULT_CONFIG.copy()
        config['display']['color_scheme'] = 'green_up'
        
        config_mgr = ConfigManager(config_path)
        config_mgr.save(config)
        
        # Test positive value -> green
        assert get_pnl_color(100.0, config_path) == "green"
        assert get_pnl_color(0.01, config_path) == "green"
        
        # Test negative value -> red
        assert get_pnl_color(-100.0, config_path) == "red"
        assert get_pnl_color(-0.01, config_path) == "red"
        
        # Test zero -> green (non-negative)
        assert get_pnl_color(0.0, config_path) == "green"


def test_red_up_scheme():
    """Test red_up color scheme (Chinese style)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.toml"
        
        # Create config with red_up scheme
        config = DEFAULT_CONFIG.copy()
        config['display']['color_scheme'] = 'red_up'
        
        config_mgr = ConfigManager(config_path)
        config_mgr.save(config)
        
        # Test positive value -> red
        assert get_pnl_color(100.0, config_path) == "red"
        assert get_pnl_color(0.01, config_path) == "red"
        
        # Test negative value -> green
        assert get_pnl_color(-100.0, config_path) == "green"
        assert get_pnl_color(-0.01, config_path) == "green"
        
        # Test zero -> red (non-negative)
        assert get_pnl_color(0.0, config_path) == "red"


def test_default_scheme():
    """Test default color scheme when not specified."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.toml"
        
        # Create config without color_scheme (should default to green_up)
        config = {
            "general": {"default_currency": "USD"},
            "display": {"date_format": "%Y-%m-%d"},
            "api": {}
        }
        
        config_mgr = ConfigManager(config_path)
        config_mgr.save(config)
        
        # Should default to green_up
        assert get_pnl_color(100.0, config_path) == "green"
        assert get_pnl_color(-100.0, config_path) == "red"


def test_config_manager_get_color_scheme():
    """Test ConfigManager.get_color_scheme() method."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.toml"
        
        # Test green_up
        config = DEFAULT_CONFIG.copy()
        config['display']['color_scheme'] = 'green_up'
        
        config_mgr = ConfigManager(config_path)
        config_mgr.save(config)
        
        assert config_mgr.get_color_scheme() == 'green_up'
        
        # Test red_up
        config['display']['color_scheme'] = 'red_up'
        config_mgr.save(config)
        config_mgr.load()  # Reload
        
        assert config_mgr.get_color_scheme() == 'red_up'
        
        # Test default
        del config['display']['color_scheme']
        config_mgr.save(config)
        config_mgr.load()
        
        assert config_mgr.get_color_scheme() == 'green_up'


if __name__ == "__main__":
    test_green_up_scheme()
    test_red_up_scheme()
    test_default_scheme()
    test_config_manager_get_color_scheme()
    print("All color helper tests passed!")
