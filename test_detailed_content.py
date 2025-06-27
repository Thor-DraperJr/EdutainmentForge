"""
Enhanced test script to examine content extraction in detail.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from content import MSLearnFetcher, ScriptProcessor
from utils import setup_logger

def detailed_content_test():
    """Test content extraction with detailed output."""
    logger = setup_logger()
    
    # Test specific AI-900 module
    test_url = "https://learn.microsoft.com/en-us/training/modules/get-started-ai-fundamentals/1-introduction"
    
    try:
        fetcher = MSLearnFetcher()
        processor = ScriptProcessor()
        
        print("🔍 Detailed Content Analysis")
        print("=" * 60)
        print(f"URL: {test_url}")
        
        # Fetch content
        content = fetcher.fetch_module_content(test_url)
        print(f"\n📄 Raw Content (first 500 chars):")
        print("-" * 40)
        print(content['content'][:500])
        print("-" * 40)
        print(f"Total length: {len(content['content'])} characters")
        
        # Process to script
        script_data = processor.process_content_to_script(content)
        print(f"\n🎬 Generated Script:")
        print("-" * 40)
        print(script_data['script'])
        print("-" * 40)
        
        # Save full script to file for review
        output_path = Path("output/ai900_detailed_script.txt")
        output_path.parent.mkdir(exist_ok=True)
        output_path.write_text(f"""
Title: {script_data['title']}
Word Count: {script_data['word_count']}
Duration: {script_data['estimated_duration']}
Source: {script_data['source_url']}

SCRIPT:
{script_data['script']}

RAW CONTENT:
{content['content']}
""")
        
        print(f"\n💾 Full analysis saved to: {output_path}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"Detailed test failed: {e}", exc_info=True)


if __name__ == "__main__":
    detailed_content_test()
