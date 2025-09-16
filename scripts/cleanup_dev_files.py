#!/usr/bin/env python3
"""
Clean up development files before production deployment.
"""

import os
import shutil
from pathlib import Path

def cleanup_development_files():
    """Remove development-specific files and reset for production."""
    
    print("🧹 Cleaning up development files...")
    
    # Remove development audio files
    output_dir = Path("output")
    if output_dir.exists():
        dev_patterns = [
            "*azure_fundamentals*",
            "*azure_storage*", 
            "*azure_active*",
            "*azure_networking*",
            "*azure_security*"
        ]
        
        for pattern in dev_patterns:
            for file in output_dir.glob(pattern):
                print(f"  📁 Removing: {file}")
                file.unlink()
    
    # Remove development environment files
    dev_env_files = [".env", "data/feedback.json"]
    for file_path in dev_env_files:
        if os.path.exists(file_path):
            print(f"  🔧 Removing: {file_path}")
            os.remove(file_path)
    
    # Create production directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    print("✅ Development cleanup complete!")
    print("📋 Next steps:")
    print("  1. Copy .env.production.template to .env")
    print("  2. Fill in your real Azure credentials")
    print("  3. Set FLASK_ENV=production")
    print("  4. Deploy to your production environment")

if __name__ == "__main__":
    cleanup_development_files()