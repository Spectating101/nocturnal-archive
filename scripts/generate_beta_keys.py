#!/usr/bin/env python3
"""
Beta License Key Generator
Generates license keys for beta testers
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from nocturnal_archive.auth import AuthManager

def generate_beta_keys(count=15, days=90):
    """Generate beta license keys"""
    auth = AuthManager()
    
    print("\n" + "="*70)
    print("🔑 Nocturnal Archive - Beta License Key Generator")
    print("="*70 + "\n")
    
    print(f"Generating {count} beta license keys (valid for {days} days)...\n")
    
    keys = []
    for i in range(1, count + 1):
        email = f"beta{i}@nocturnal.dev"
        key = auth.generate_license_key(email, days=days)
        keys.append((email, key))
        print(f"{i:2d}. Email: {email:<30} | Key: {key}")
    
    print("\n" + "="*70)
    print(f"✅ Generated {count} license keys")
    print("="*70 + "\n")
    
    # Save to file
    output_file = Path(__file__).parent / "beta_keys.txt"
    with open(output_file, 'w') as f:
        f.write("Nocturnal Archive - Beta License Keys\n")
        f.write("="*70 + "\n\n")
        for i, (email, key) in enumerate(keys, 1):
            f.write(f"{i}. {email}\n")
            f.write(f"   License Key: {key}\n\n")
    
    print(f"📄 Keys saved to: {output_file}")
    print()
    
    return keys

def generate_custom_key():
    """Generate a custom license key"""
    auth = AuthManager()
    
    print("\n" + "="*70)
    print("🔑 Custom License Key Generator")
    print("="*70 + "\n")
    
    email = input("Enter email address: ").strip()
    days = input("Enter validity period (days) [default: 90]: ").strip()
    days = int(days) if days else 90
    
    key = auth.generate_license_key(email, days=days)
    
    print(f"\n✅ License Key Generated:")
    print(f"   Email: {email}")
    print(f"   Valid for: {days} days")
    print(f"   Key: {key}")
    print()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate beta license keys")
    parser.add_argument(
        '--count',
        type=int,
        default=15,
        help='Number of keys to generate (default: 15)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=90,
        help='Validity period in days (default: 90)'
    )
    parser.add_argument(
        '--custom',
        action='store_true',
        help='Generate a custom key for a specific email'
    )
    
    args = parser.parse_args()
    
    if args.custom:
        generate_custom_key()
    else:
        generate_beta_keys(args.count, args.days)
