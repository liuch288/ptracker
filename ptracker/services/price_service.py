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
    
    def _convert_to_yahoo_format(self, asset: str) -> str:
        """Convert asset code to Yahoo Finance format.
        
        Yahoo Finance has specific requirements:
        - HK stocks: use 4-digit code (0700.HK not 00700.HK)
        
        Args:
            asset: Original asset code
            
        Returns:
            Asset code in Yahoo Finance format
        """
        # Handle HK stocks: remove leading zeros but keep 4 digits
        if asset.endswith('.HK'):
            code = asset[:-3]  # Remove .HK
            # Remove leading zeros but ensure at least 4 digits
            code = code.lstrip('0')
            if not code:
                # All zeros like 00700 -> use 4 zeros
                code = '0000'
            elif len(code) < 4:
                # Pad to 4 digits (e.g., 700 -> 0700)
                code = code.zfill(4)
            return code + '.HK'
        return asset
    
    def _fetch_yahoo_price(self, yahoo_asset: str, original_asset: str) -> Optional[PriceQuote]:
        """Fetch price from Yahoo Finance.
        
        Args:
            yahoo_asset: Asset code in Yahoo format
            original_asset: Original asset code (for caching)
            
        Returns:
            PriceQuote or None if not found
        """
        try:
            ticker = yf.Ticker(yahoo_asset)
            info = ticker.info
            
            if 'currentPrice' in info:
                price = info['currentPrice']
            elif 'regularMarketPrice' in info:
                price = info['regularMarketPrice']
            elif 'previousClose' in info:
                price = info['previousClose']
            else:
                return None
            
            if price:
                currency = info.get('currency', 'USD')
                quote = PriceQuote(
                    asset=original_asset,
                    price=float(price),
                    currency=currency,
                    timestamp=datetime.now()
                )
                
                # Cache the result (use original asset as key)
                self._price_cache[original_asset] = (quote, datetime.now())
                return quote
        
        except Exception as e:
            print(f"Error fetching Yahoo price for {original_asset}: {e}")
        
        return None
    
    def get_price(self, asset: str) -> Optional[PriceQuote]:
        """Get current price for asset.
        
        Priority:
        1. Check cache
        2. Try yfinance (with format conversion for HK stocks)
        3. Fallback to akshare
        
        Args:
            asset: Asset code (original format)
            
        Returns:
            PriceQuote or None if not found
        """
        # Check cache (use original asset for cache key)
        if asset in self._price_cache:
            quote, cached_at = self._price_cache[asset]
            if datetime.now() - cached_at < timedelta(seconds=self.cache_seconds):
                return quote
        
        # Convert to Yahoo format for query
        yahoo_asset = self._convert_to_yahoo_format(asset)
        
        # Try yfinance with converted format
        quote = self._fetch_yahoo_price(yahoo_asset, asset)
        if quote:
            return quote
        
        # Fallback: try original format if different
        if yahoo_asset != asset:
            quote = self._fetch_yahoo_price(asset, asset)
            if quote:
                return quote
        
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
        
        except Exception as e:
            print(f"Error fetching akshare price for {asset}: {e}")
        
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
        
        except Exception as e:
            print(f"Error fetching exchange rate {from_currency}->{to_currency}: {e}")
        
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
