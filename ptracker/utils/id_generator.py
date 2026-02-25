"""ID generation utilities for ptracker."""

import time
import random

BASE36 = '0123456789abcdefghijklmnopqrstuvwxyz'


def to_base36(n: int) -> str:
    """Convert integer to base36 string (no leading zeros).
    
    Args:
        n: Integer to convert
        
    Returns:
        Base36 string representation
        
    Example:
        >>> to_base36(0)
        '0'
        >>> to_base36(35)
        'z'
        >>> to_base36(36)
        '10'
    """
    if n == 0:
        return '0'
    
    result = ''
    while n > 0:
        n, r = divmod(n, 36)
        result = BASE36[r] + result
    return result


def timestamp_to_base36(timestamp_ms: int) -> str:
    """Convert millisecond timestamp to base36 string.
    
    Args:
        timestamp_ms: Millisecond Unix timestamp
        
    Returns:
        Base36 string representation of timestamp
    """
    return to_base36(timestamp_ms)


def random_base36(length: int = 2) -> str:
    """Generate random base36 string of specified length.
    
    Args:
        length: Number of characters to generate (default: 2)
        
    Returns:
        Random base36 string
        
    Example:
        >>> len(random_base36())
        2
        >>> len(random_base36(4))
        4
    """
    return ''.join(random.choice(BASE36) for _ in range(length))


def generate_id(prefix: str) -> str:
    """Generate unique ID in format: {prefix}_{time_base36}_{random_base36}.
    
    Args:
        prefix: One of 'txn', 'hold', 'real', 'acct'
        
    Returns:
        Unique ID string (12-14 characters including prefix)
        
    Example:
        >>> id = generate_id('txn')
        >>> id.startswith('txn_')
        True
        >>> len(id.split('_'))
        3
    """
    # Current millisecond timestamp
    timestamp_ms = int(time.time() * 1000)
    
    # Time part in base36
    ts_part = timestamp_to_base36(timestamp_ms)
    
    # 2-character random base36
    rand_part = random_base36(2)
    
    return f"{prefix}_{ts_part}_{rand_part}"
