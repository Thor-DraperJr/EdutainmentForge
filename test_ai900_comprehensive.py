"""
Test AI-900 content extraction using the existing working fetcher.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from content import MSLearnFetcher, ScriptProcessor
from utils import setup_logger

def test_ai900_with_working_fetcher():
    """Test AI-900 content using the working fetcher approach."""
    
    logger = setup_logger()
    
    # Use the specific module URLs from AI-900 path that we know work
    ai900_modules = [
        {
            'title': 'Introduction to AI concepts',
            'url': 'https://learn.microsoft.com/en-us/training/modules/get-started-ai-fundamentals/',
            'description': 'Curious about artificial intelligence? Want to understand what all the buzz is about? This module introduces you to the world of AI.'
        },
        {
            'title': 'Introduction to machine learning concepts',
            'url': 'https://learn.microsoft.com/en-us/training/modules/fundamentals-machine-learning/',
            'description': 'Machine learning is the basis for most modern artificial intelligence solutions.'
        },
        {
            'title': 'Introduction to generative AI concepts',
            'url': 'https://learn.microsoft.com/en-us/training/modules/fundamentals-generative-ai/',
            'description': 'In this module, you explore the way in which language models enable AI applications and services to generate original content.'
        },
        {
            'title': 'Introduction to natural language processing concepts',
            'url': 'https://learn.microsoft.com/en-us/training/modules/introduction-language/',
            'description': 'Natural language processing (NLP) supports applications that can see, hear, speak with, and understand users.'
        },
        {
            'title': 'Introduction to computer vision concepts',
            'url': 'https://learn.microsoft.com/en-us/training/modules/introduction-computer-vision/',
            'description': 'Computer vision is a core area of artificial intelligence that enables software to understand visual content.'
        }
    ]
    
    print("🎯 AI-900 Content Extraction Test")
    print("=" * 60)
    print(f"Testing {len(ai900_modules)} AI-900 modules")
    print()
    
    fetcher = MSLearnFetcher()
    processor = ScriptProcessor()
    
    total_content = 0
    successful_modules = 0
    
    for i, module in enumerate(ai900_modules, 1):
        print(f"📖 Module {i}: {module['title']}")
        print(f"   URL: {module['url']}")
        
        try:
            # Fetch content
            content = fetcher.fetch_module_content(module['url'])
            content_length = len(content['content'])
            total_content += content_length
            successful_modules += 1
            
            print(f"   ✅ Content fetched: {content_length:,} characters")
            
            # Process to script
            script_data = processor.process_content_to_script(content)
            
            print(f"   🎬 Script generated: {script_data['word_count']} words")
            print(f"   ⏱️  Estimated duration: {script_data['estimated_duration']}")
            
            # Show content preview
            preview = content['content'][:200] + "..." if len(content['content']) > 200 else content['content']
            print(f"   📄 Content preview: {preview}")
            
            # Show script preview
            script_preview = script_data['script'][:150] + "..." if len(script_data['script']) > 150 else script_data['script']
            print(f"   🎙️  Script preview: {script_preview}")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            logger.error(f"Module {module['title']} failed: {e}")
        
        print()
    
    print("📊 Summary:")
    print(f"Successful modules: {successful_modules}/{len(ai900_modules)}")
    print(f"Total content: {total_content:,} characters")
    if successful_modules > 0:
        print(f"Average per module: {total_content // successful_modules:,} characters")
    
    # Test learning path extraction
    print("\n🔍 Testing Learning Path Extraction:")
    ai900_path = "https://learn.microsoft.com/en-us/training/paths/introduction-to-ai-on-azure/"
    
    try:
        path_modules = fetcher.fetch_learning_path_modules(ai900_path)
        print(f"   ✅ Found {len(path_modules)} modules in learning path")
        
        for i, module in enumerate(path_modules[:3], 1):  # Show first 3
            print(f"   {i}. {module['title']}")
            print(f"      {module['url']}")
        
        if len(path_modules) > 3:
            print(f"   ... and {len(path_modules) - 3} more modules")
            
    except Exception as e:
        print(f"   ❌ Learning path extraction failed: {e}")


if __name__ == "__main__":
    test_ai900_with_working_fetcher()
