"""Tests for ID generator."""

import re
from ptracker.utils.id_generator import generate_id, to_base36, random_base36


def test_to_base36():
    """Test base36 conversion."""
    assert to_base36(0) == '0'
    assert to_base36(35) == 'z'
    assert to_base36(36) == '10'
    assert to_base36(1000) == 'rs'
    print("✓ to_base36 tests passed")


def test_random_base36():
    """Test random base36 generation."""
    rand = random_base36(2)
    assert len(rand) == 2
    assert all(c in '0123456789abcdefghijklmnopqrstuvwxyz' for c in rand)
    
    rand4 = random_base36(4)
    assert len(rand4) == 4
    print("✓ random_base36 tests passed")


def test_generate_id():
    """Test ID generation."""
    # Test transaction ID
    txn_id = generate_id('txn')
    assert txn_id.startswith('txn_')
    parts = txn_id.split('_')
    assert len(parts) == 3
    assert len(parts[2]) == 2  # Random part
    print(f"✓ Generated transaction ID: {txn_id}")
    
    # Test account ID
    acct_id = generate_id('acct')
    assert acct_id.startswith('acct_')
    print(f"✓ Generated account ID: {acct_id}")
    
    # Test holding ID
    hold_id = generate_id('hold')
    assert hold_id.startswith('hold_')
    print(f"✓ Generated holding ID: {hold_id}")
    
    # Test realized ID
    real_id = generate_id('real')
    assert real_id.startswith('real_')
    print(f"✓ Generated realized ID: {real_id}")
    
    # Test uniqueness (with small delay to avoid millisecond collisions)
    import time
    ids = []
    for _ in range(10):
        ids.append(generate_id('txn'))
        time.sleep(0.001)  # 1ms delay
    assert len(ids) == len(set(ids)), "IDs should be unique"
    print("✓ ID uniqueness test passed (10 IDs with delay)")


if __name__ == '__main__':
    test_to_base36()
    test_random_base36()
    test_generate_id()
    print("\n✅ All ID generator tests passed!")
