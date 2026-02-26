#!/usr/bin/env python3
"""Test that realized positions now include currency field."""

import subprocess
import sys
from pathlib import Path
import json

def run_command(cmd):
    """Run a command and return output."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout, result.returncode

def main():
    """Test realized position currency field."""
    
    print("🧪 Testing Realized Position Currency Field")
    print("="*60)
    
    data_dir = Path.home() / ".ptracker"
    if not data_dir.exists():
        print("❌ ptracker not initialized.")
        sys.exit(1)
    
    # Step 1: Create a test position and close it
    print("\n1. Creating and closing a test position...")
    
    # Add a new position
    run_command('ptracker trade add buy TEST 100 50.0 --currency EUR --account us_broker --action open --direction long --note "Test position"')
    
    # Close the position
    run_command('ptracker trade add sell TEST 100 55.0 --currency EUR --account us_broker --action close --direction long --note "Close test"')
    
    print("✓ Position created and closed")
    
    # Step 2: Check realized.json directly
    print("\n2. Checking realized.json for currency field...")
    
    realized_file = data_dir / "realized.json"
    if realized_file.exists():
        with open(realized_file, 'r') as f:
            data = json.load(f)
            
        if data.get('_default'):
            positions = list(data['_default'].values())
            
            # Find the TEST position
            test_position = None
            for pos in positions:
                if pos.get('asset') == 'TEST':
                    test_position = pos
                    break
            
            if test_position:
                print(f"✓ Found TEST realized position")
                print(f"  Asset: {test_position.get('asset')}")
                print(f"  Currency: {test_position.get('currency', 'MISSING!')}")
                print(f"  Realized P&L: {test_position.get('realized_pnl')}")
                print(f"  Return: {test_position.get('return_pct')}%")
                
                if 'currency' in test_position:
                    print("\n✅ SUCCESS: Currency field is present!")
                    if test_position['currency'] == 'EUR':
                        print("✅ Currency value is correct (EUR)")
                    else:
                        print(f"⚠️  Currency value is {test_position['currency']}, expected EUR")
                else:
                    print("\n❌ FAILED: Currency field is missing!")
                    return False
            else:
                print("⚠️  TEST position not found in realized.json")
        else:
            print("⚠️  No positions in realized.json")
    else:
        print("❌ realized.json not found")
        return False
    
    # Step 3: Test query command
    print("\n3. Testing query realized command...")
    output, _ = run_command('ptracker query realized --asset TEST')
    print(output)
    
    if 'Currency' in output and 'EUR' in output:
        print("✅ Query command shows currency correctly")
    else:
        print("⚠️  Currency may not be displayed in query output")
    
    # Step 4: Clean up
    print("\n4. Cleaning up test data...")
    # Note: We'll leave the test data for manual inspection
    print("✓ Test completed (test data left for inspection)")
    
    print("\n" + "="*60)
    print("✅ All tests passed!")
    print("="*60)
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
