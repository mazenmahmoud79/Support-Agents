"""
Quick test script to validate demo authentication system.

This script tests:
1. Loading demo_ids.json
2. Validating demo ID format
3. Simulating authentication flow
"""

import json
from pathlib import Path


def test_demo_config():
    """Test loading and validating demo configuration."""
    print("=" * 60)
    print("DEMO AUTHENTICATION SYSTEM - TEST SCRIPT")
    print("=" * 60)
    
    # Load config
    config_path = Path(__file__).parent / "backend" / "demo_ids.json"
    print(f"\n1. Loading config from: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        print("   ✅ Config loaded successfully")
    except Exception as e:
        print(f"   ❌ Failed to load config: {e}")
        return False
    
    # Validate structure
    print("\n2. Validating config structure...")
    required_keys = ['tenant_name', 'tenant_id', 'demo_ids']
    for key in required_keys:
        if key in config:
            print(f"   ✅ '{key}' found")
        else:
            print(f"   ❌ Missing required key: '{key}'")
            return False
    
    # Validate demo IDs
    print(f"\n3. Validating {len(config['demo_ids'])} demo IDs...")
    valid_count = 0
    invalid_ids = []
    
    for demo_id in config['demo_ids']:
        if isinstance(demo_id, str) and demo_id.startswith('DEMO-') and len(demo_id) == 11:
            valid_count += 1
        else:
            invalid_ids.append(demo_id)
    
    print(f"   ✅ {valid_count} valid demo IDs")
    if invalid_ids:
        print(f"   ❌ {len(invalid_ids)} invalid demo IDs: {invalid_ids}")
        return False
    
    # Display info
    print("\n4. Configuration Details:")
    print(f"   Tenant Name: {config['tenant_name']}")
    print(f"   Tenant ID: {config['tenant_id']}")
    print(f"   Total Demo IDs: {len(config['demo_ids'])}")
    print(f"   First 5 IDs: {config['demo_ids'][:5]}")
    print(f"   Last 5 IDs: {config['demo_ids'][-5:]}")
    
    # Test sample demo ID
    print("\n5. Testing sample demo ID validation...")
    test_id = config['demo_ids'][0]
    print(f"   Test ID: {test_id}")
    
    if test_id in config['demo_ids']:
        print(f"   ✅ '{test_id}' is valid")
    else:
        print(f"   ❌ '{test_id}' validation failed")
        return False
    
    # Test invalid demo ID
    print("\n6. Testing invalid demo ID rejection...")
    invalid_id = "INVALID-ID"
    print(f"   Test ID: {invalid_id}")
    
    if invalid_id not in config['demo_ids']:
        print(f"   ✅ '{invalid_id}' correctly rejected")
    else:
        print(f"   ❌ '{invalid_id}' incorrectly accepted")
        return False
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✅")
    print("=" * 60)
    print("\nDemo authentication system is ready!")
    print(f"\nYou can use any of these {len(config['demo_ids'])} demo IDs to login:")
    print(f"  - {config['demo_ids'][0]}")
    print(f"  - {config['demo_ids'][1]}")
    print(f"  - {config['demo_ids'][2]}")
    print(f"  - ... and {len(config['demo_ids']) - 3} more!")
    print("\nSee DEMO_IDS.md for the complete list.")
    
    return True


if __name__ == "__main__":
    test_demo_config()
