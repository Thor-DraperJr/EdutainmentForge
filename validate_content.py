"""
Content validation script for EdutainmentForge.

Shows exactly what content is being extracted from MS Learn modules.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from content import MSLearnFetcher
from utils import setup_logger

def validate_content(url: str):
    """Validate and display extracted content."""
    logger = setup_logger()
    
    print("🔍 Content Validation for EdutainmentForge")
    print("=" * 60)
    print(f"URL: {url}")
    print()
    
    try:
        fetcher = MSLearnFetcher()
        content = fetcher.fetch_module_content(url)
        
        print(f"📝 Title: {content['title']}")
        print(f"📏 Content Length: {len(content['content'])} characters")
        print()
        
        print("📖 Extracted Content:")
        print("-" * 60)
        print(content['content'])
        print("-" * 60)
        
        # Check if it matches the expected content
        expected_intro = "You're presumably here because you want to learn more about artificial intelligence"
        
        if expected_intro in content['content']:
            print("✅ VALIDATION SUCCESS: Found expected introduction text")
        else:
            print("❌ VALIDATION WARNING: Expected introduction text not found")
            print(f"Expected to find: '{expected_intro[:50]}...'")
        
        # Show first 200 characters for comparison
        print()
        print("🔤 First 200 characters:")
        print(f"'{content['content'][:200]}...'")
        
        return content
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Content validation failed: {e}")
        return None

if __name__ == "__main__":
    # Test with the AI fundamentals introduction
    url = "https://learn.microsoft.com/en-us/training/modules/get-started-ai-fundamentals/1-introduction"
    validate_content(url)
