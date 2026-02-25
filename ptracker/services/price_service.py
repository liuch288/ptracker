"""Price service with fallback mechanism."""

from typing import Optional, Dict
from datetime import datetime, timedelta
import yfinance as yf


class PriceQuote:
    """Price quote data."""
    
    def __init__(self, asset: str, price: float, currency: str, timestamp: datetime):
        self.asset = asset
        self.price = price
        self.currency = currency
        self.timestamp = timestamp


class PriceService:
    """Fetch current market prices with fallback mechanism."""
    
    def __init__(self, cache_seconds: int = 60):
        """Initialize price service.
        
        Args:
            cache_seconds: Cache TTL in seconds (default: 60)
        """
        self.cache_seconds = cache_seconds
        self._price_cache: Dict[str, tuple[PriceQuote, datetime]] = {}
        self._exchange_rate_cache: Dict[str, tuple[float, datetime]] = {}
    
    def get_price(self, asset: str) -> Optional[PriceQuote]:
        """Get current price for asset.
        
        Priority:
        1. Check cache
        2. Try yfinance
        3. Fallback to akshare
        
        Args:
            asset: Asset code (Yahoo Finance format)
            
        Returns:
            PriceQuote or None if not found
        """
        # Check cache
        if asset in self._price_cache:
            quote, cached_at = self._price_cache[asset]
            if datetime.now() - cached_at < timedelta(seconds=self.cache_seconds):
                return quote
        
        # Try yfinance
        try:
            ticker = yf.Ticker(asset)
            info = ticker.info
            
            if 'currentPrice' in info:
                price = info['currentPrice']
            elif 'regularMarketPrice' in info:
                price = info['regularMarketPrice']
            elif 'previousClose' in info:
                price = info['previousClose']
            else:
                price = None
            
            if price:
                currency = info.get('currency', 'USD')
                quote = PriceQuote(
                    asset=asset,
                    price=float(price),
                    currency=currency,
                    timestamp=datetime.now()
                )
                
                # Cache the result
                self._price_cache[asset] = (quote, datetime.now())
                return quote
        
        except Exception:
            pass
        
        # Try akshare fallback
        try:
            import akshare as ak
            
            # Map Yahoo format to akshare format
            # This is a simplified mapping - may need expansion
            if asset.endswith('.HK'):
                # Hong Kong stocks
                symbol = asset.replace('.HK', '')
                df = ak.stock_hk_spot_em()
                row = df[df['代码'] == symbol]
                if not row.empty:
                    price = float(row.iloc[0]['最新价'])
                    quote = PriceQuote(
                        asset=asset,
                        price=price,
                        currency='HKD',
                        timestamp=datetime.now()
                    )
                    self._price_cache[asset] = (quote, datetime.now())
                    return quote
            
            elif asset.endswith('.SS') or asset.endswith('.SZ'):
                # A-shares
                symbol = asset[:-3]
                df = ak.stock_zh_a_spot_em()
                row = df[df['代码'] == symbol]
                if not row.empty:
                    price = float(row.iloc[0]['最新价'])
                    quote = PriceQuote(
                        asset=asset,
                        price=price,
                        currency='CNY',
                        timestamp=datetime.now()
                    )
                    self._price_cache[asset] = (quote, datetime.now())
                    return quote
        
        except Exception:
            pass
        
        # Both failed
        return None
    
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """Get current exchange rate between currencies.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Exchange rate (1 from_currency = X to_currency)
        """
        if from_currency == to_currency:
            return 1.0
        
        # Check cache
        cache_key = f"{from_currency}{to_currency}"
        if cache_key in self._exchange_rate_cache:
            rate, cached_at = self._exchange_rate_cache[cache_key]
            if datetime.now() - cached_at < timedelta(seconds=self.cache_seconds):
                return rate
        
        # Try yfinance currency pair
        try:
            pair = f"{from_currency}{to_currency}=X"
            ticker = yf.Ticker(pair)
            info = ticker.info
            
            if 'regularMarketPrice' in info:
                rate = float(info['regularMarketPrice'])
                self._exchange_rate_cache[cache_key] = (rate, datetime.now())
                return rate
        
        except Exception:
            pass
        
        # Fallback: return 1.0 (no conversion)
        return 1.0
    
    def convert_amount(
        self,
        amount: float,
        from_currency: str,
        to_currency: str
    ) -> float:
        """Convert amount from one currency to another.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency code
            to_currency: Target currency code
            
        Returns:
            Converted amount
        """
        if from_currency == to_currency:
            return amount
        
        rate = self.get_exchange_rate(from_currency, to_currency)
        return amount * rate
