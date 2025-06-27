"""
Test script for EdutainmentForge with AI-900 content.

Tests content fetching and processing for the AI-900 training path.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from content import MSLearnFetcher, ScriptProcessor, create_sample_content
from utils import load_config, setup_logger

def test_ai900_content():
    """Test fetching and processing AI-900 content."""
    logger = setup_logger()
    
    # AI-900 URLs to test
    ai_900_urls = [
        "https://learn.microsoft.com/en-us/training/modules/get-started-ai-fundamentals/",
        "https://learn.microsoft.com/en-us/training/modules/fundamentals-machine-learning/",
        "https://learn.microsoft.com/en-us/training/modules/fundamentals-generative-ai/"
    ]
    
    try:
        config = load_config()
        fetcher = MSLearnFetcher()
        processor = ScriptProcessor()
        
        print("🎯 Testing EdutainmentForge with AI-900 Content")
        print("=" * 60)
        
        for i, url in enumerate(ai_900_urls, 1):
            print(f"\n📚 Module {i}: {url}")
            
            try:
                # Fetch content
                content = fetcher.fetch_module_content(url)
                print(f"✅ Fetched: {content['title']}")
                print(f"   Content length: {len(content['content'])} characters")
                
                # Process to script
                script_data = processor.process_content_to_script(content)
                print(f"🎬 Script generated: {script_data['word_count']} words")
                print(f"   Estimated duration: {script_data['estimated_duration']}")
                
                # Show preview
                preview = script_data['script'][:150] + "..."
                print(f"   Preview: {preview}")
                
            except Exception as e:
                print(f"❌ Error processing {url}: {e}")
                logger.error(f"Module processing failed: {e}")
        
        print(f"\n🎉 AI-900 Content Test Complete!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"Test failed: {e}")


if __name__ == "__main__":
    test_ai900_content()
