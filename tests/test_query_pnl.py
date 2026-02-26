"""Tests for query pnl command."""

import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch
from typer.testing import CliRunner
from ptracker.cli.main import app
from ptracker.repositories import HoldingRepository, RealizedRepository
from ptracker.config import ConfigManager


runner = CliRunner()


def setup_test_data(data_dir: Path):
    """Setup test data for pnl query tests."""
    # Create config
    config_path = data_dir / "config.toml"
    config = ConfigManager(config_path)
    config.set('general.default_currency', 'USD')
    
    # Create holdings
    holding_repo = HoldingRepository(data_dir / "holdings.json")
    holdings = [
        {
            'asset': 'AAPL',
            'account': 'us_broker',
            'direction': 'long',
            'quantity': 50.0,
            'avg_cost': 140.0,
            'total_invested': 7000.0,
            'currency': 'USD',
            'first_open_date': '2026-01-01',
            'last_updated': '2026-01-15',
            'note': '',
            'status': 'active'
        },
        {
            'asset': '9988.HK',
            'account': 'hk_broker',
            'direction': 'long',
            'quantity': 200.0,
            'avg_cost': 80.0,
            'total_invested': 16000.0,
            'currency': 'HKD',
            'first_open_date': '2026-01-10',
            'last_updated': '2026-01-20',
            'note': '',
            'status': 'active'
        }
    ]
    for holding in holdings:
        holding_repo.upsert(holding)
    
    # Create realized positions
    realized_repo = RealizedRepository(data_dir / "realized.json")
    realized = [
        {
            'id': 'real_001',
            'asset': '0700.HK',
            'account': 'hk_broker',
            'direction': 'long',
            'first_open_date': '2025-06-01',
            'last_close_date': '2026-01-15',
            'holding_days': 228,
            'total_quantity': 1000.0,
            'total_invested': 160000.0,
            'total_proceeds': 175000.0,
            'total_fees': 100.0,
            'realized_pnl': 14900.0,
            'return_pct': 9.31,
            'currency': 'HKD',
            'note': '',
            'status': 'closed'
        }
    ]
    for r in realized:
        realized_repo.insert(r)


def test_query_pnl_basic():
    """Test basic pnl query without detail."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        setup_test_data(data_dir)
        
        # Mock price service
        mock_quote_aapl = Mock()
        mock_quote_aapl.price = 270.0
        
        mock_quote_9988 = Mock()
        mock_quote_9988.price = 143.0
        
        def mock_get_price(asset):
            if asset == 'AAPL':
                return mock_quote_aapl
            elif asset == '9988.HK':
                return mock_quote_9988
            return None
        
        def mock_get_exchange_rate(from_curr, to_curr):
            if from_curr == to_curr:
                return 1.0
            if from_curr == 'HKD' and to_curr == 'USD':
                return 0.128
            if from_curr == 'USD' and to_curr == 'HKD':
                return 7.8
            return 1.0
        
        with patch('ptracker.cli.query.get_data_dir', return_value=data_dir):
            with patch('ptracker.cli.query.PriceService') as MockPriceService:
                mock_service = Mock()
                mock_service.get_price = mock_get_price
                mock_service.get_exchange_rate = mock_get_exchange_rate
                MockPriceService.return_value = mock_service
                
                result = runner.invoke(app, ["query", "pnl"])
                
                assert result.exit_code == 0
                assert "Unrealized P&L" in result.stdout
                assert "Realized P&L" in result.stdout
                assert "Total P&L" in result.stdout
                print("✓ Basic pnl query works")


def test_query_pnl_with_detail():
    """Test pnl query with detail breakdown."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        setup_test_data(data_dir)
        
        # Mock price service
        mock_quote_aapl = Mock()
        mock_quote_aapl.price = 270.0
        
        mock_quote_9988 = Mock()
        mock_quote_9988.price = 143.0
        
        def mock_get_price(asset):
            if asset == 'AAPL':
                return mock_quote_aapl
            elif asset == '9988.HK':
                return mock_quote_9988
            return None
        
        def mock_get_exchange_rate(from_curr, to_curr):
            if from_curr == to_curr:
                return 1.0
            if from_curr == 'HKD' and to_curr == 'USD':
                return 0.128
            return 1.0
        
        with patch('ptracker.cli.query.get_data_dir', return_value=data_dir):
            with patch('ptracker.cli.query.PriceService') as MockPriceService:
                mock_service = Mock()
                mock_service.get_price = mock_get_price
                mock_service.get_exchange_rate = mock_get_exchange_rate
                MockPriceService.return_value = mock_service
                
                result = runner.invoke(app, ["query", "pnl", "--detail"])
                
                assert result.exit_code == 0
                assert "Unrealized P&L by Asset" in result.stdout
                assert "Realized P&L by Asset" in result.stdout
                assert "AAPL" in result.stdout
                assert "9988.HK" in result.stdout
                assert "0700.HK" in result.stdout
                assert "Currency" in result.stdout
                print("✓ Pnl query with detail works")


def test_query_pnl_realized_only():
    """Test pnl query with realized-only flag."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        setup_test_data(data_dir)
        
        def mock_get_exchange_rate(from_curr, to_curr):
            if from_curr == to_curr:
                return 1.0
            if from_curr == 'HKD' and to_curr == 'USD':
                return 0.128
            return 1.0
        
        with patch('ptracker.cli.query.get_data_dir', return_value=data_dir):
            with patch('ptracker.cli.query.PriceService') as MockPriceService:
                mock_service = Mock()
                mock_service.get_exchange_rate = mock_get_exchange_rate
                MockPriceService.return_value = mock_service
                
                result = runner.invoke(app, ["query", "pnl", "--realized-only"])
                
                assert result.exit_code == 0
                assert "Realized P&L" in result.stdout
                assert "Unrealized P&L" not in result.stdout
                assert "Total P&L" not in result.stdout
                print("✓ Pnl query with realized-only works")


def test_query_pnl_unrealized_only():
    """Test pnl query with unrealized-only flag."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        setup_test_data(data_dir)
        
        # Mock price service
        mock_quote_aapl = Mock()
        mock_quote_aapl.price = 270.0
        
        mock_quote_9988 = Mock()
        mock_quote_9988.price = 143.0
        
        def mock_get_price(asset):
            if asset == 'AAPL':
                return mock_quote_aapl
            elif asset == '9988.HK':
                return mock_quote_9988
            return None
        
        def mock_get_exchange_rate(from_curr, to_curr):
            if from_curr == to_curr:
                return 1.0
            if from_curr == 'HKD' and to_curr == 'USD':
                return 0.128
            return 1.0
        
        with patch('ptracker.cli.query.get_data_dir', return_value=data_dir):
            with patch('ptracker.cli.query.PriceService') as MockPriceService:
                mock_service = Mock()
                mock_service.get_price = mock_get_price
                mock_service.get_exchange_rate = mock_get_exchange_rate
                MockPriceService.return_value = mock_service
                
                result = runner.invoke(app, ["query", "pnl", "--unrealized-only"])
                
                assert result.exit_code == 0
                assert "Unrealized P&L" in result.stdout
                assert "Realized P&L" not in result.stdout
                assert "Total P&L" not in result.stdout
                print("✓ Pnl query with unrealized-only works")


def test_query_pnl_with_currency_conversion():
    """Test pnl query with currency conversion."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        setup_test_data(data_dir)
        
        # Mock price service
        mock_quote_aapl = Mock()
        mock_quote_aapl.price = 270.0
        
        mock_quote_9988 = Mock()
        mock_quote_9988.price = 143.0
        
        def mock_get_price(asset):
            if asset == 'AAPL':
                return mock_quote_aapl
            elif asset == '9988.HK':
                return mock_quote_9988
            return None
        
        def mock_get_exchange_rate(from_curr, to_curr):
            if from_curr == to_curr:
                return 1.0
            if from_curr == 'HKD' and to_curr == 'USD':
                return 0.128
            if from_curr == 'USD' and to_curr == 'HKD':
                return 7.8
            return 1.0
        
        with patch('ptracker.cli.query.get_data_dir', return_value=data_dir):
            with patch('ptracker.cli.query.PriceService') as MockPriceService:
                mock_service = Mock()
                mock_service.get_price = mock_get_price
                mock_service.get_exchange_rate = mock_get_exchange_rate
                MockPriceService.return_value = mock_service
                
                result = runner.invoke(app, ["query", "pnl", "--detail", "--currency", "HKD"])
                
                assert result.exit_code == 0
                assert "HKD" in result.stdout
                print("✓ Pnl query with currency conversion works")


def test_query_pnl_with_account_filter():
    """Test pnl query with account filter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        setup_test_data(data_dir)
        
        # Mock price service
        mock_quote_aapl = Mock()
        mock_quote_aapl.price = 270.0
        
        def mock_get_price(asset):
            if asset == 'AAPL':
                return mock_quote_aapl
            return None
        
        def mock_get_exchange_rate(from_curr, to_curr):
            return 1.0
        
        with patch('ptracker.cli.query.get_data_dir', return_value=data_dir):
            with patch('ptracker.cli.query.PriceService') as MockPriceService:
                mock_service = Mock()
                mock_service.get_price = mock_get_price
                mock_service.get_exchange_rate = mock_get_exchange_rate
                MockPriceService.return_value = mock_service
                
                result = runner.invoke(app, ["query", "pnl", "--detail", "--account", "us_broker"])
                
                assert result.exit_code == 0
                assert "AAPL" in result.stdout
                assert "9988.HK" not in result.stdout
                print("✓ Pnl query with account filter works")


if __name__ == '__main__':
    test_query_pnl_basic()
    print()
    test_query_pnl_with_detail()
    print()
    test_query_pnl_realized_only()
    print()
    test_query_pnl_unrealized_only()
    print()
    test_query_pnl_with_currency_conversion()
    print()
    test_query_pnl_with_account_filter()
    print("\n✅ All query pnl tests passed!")
