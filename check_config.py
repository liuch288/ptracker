#!/usr/bin/env python3
"""Check ptracker configuration directory."""

from pathlib import Path
import os

# Get home directory
home = Path.home()
ptracker_dir = home / ".ptracker"

print("🔍 Checking ptracker configuration...")
print(f"\n📁 Expected directory: {ptracker_dir}")
print(f"   Absolute path: {ptracker_dir.absolute()}")

if ptracker_dir.exists():
    print(f"\n✅ Directory exists!")
    
    # List contents
    contents = list(ptracker_dir.iterdir())
    if contents:
        print(f"\n📄 Contents ({len(contents)} items):")
        for item in sorted(contents):
            if item.is_file():
                size = item.stat().st_size
                print(f"   - {item.name} ({size} bytes)")
            else:
                print(f"   - {item.name}/ (directory)")
    else:
        print("\n📭 Directory is empty")
else:
    print(f"\n❌ Directory does not exist yet")
    print(f"\n💡 To create it, you can:")
    print(f"   1. Run: ptracker init (once implemented)")
    print(f"   2. Or manually: mkdir -p {ptracker_dir}")

# Check if config file exists
config_file = ptracker_dir / "config.toml"
if config_file.exists():
    print(f"\n📝 Config file found: {config_file}")
    print(f"   Size: {config_file.stat().st_size} bytes")
    print(f"\n   Content preview:")
    with open(config_file, 'r') as f:
        content = f.read()
        print("   " + "\n   ".join(content.split('\n')[:20]))
else:
    print(f"\n📝 Config file: {config_file}")
    print(f"   Status: Not created yet")

# Check data files
data_files = ['transactions.json', 'holdings.json', 'realized.json', 'accounts.json']
print(f"\n📊 Data files:")
for filename in data_files:
    filepath = ptracker_dir / filename
    if filepath.exists():
        size = filepath.stat().st_size
        print(f"   ✅ {filename} ({size} bytes)")
    else:
        print(f"   ❌ {filename} (not created)")
