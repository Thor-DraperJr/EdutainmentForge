"""
Content Analysis Script for EdutainmentForge

Analyzes the content extraction from MS Learn URLs to see what we're actually getting.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from content import MSLearnFetcher
from utils import setup_logger
import requests
from bs4 import BeautifulSoup

def analyze_content_extraction(url: str):
    """Analyze what content we extract from a specific URL."""
    logger = setup_logger()
    
    print(f"\n🔍 ANALYZING CONTENT FROM: {url}")
    print("=" * 80)
    
    try:
        # Method 1: Our current fetcher
        print("\n📥 METHOD 1: Current EdutainmentForge Fetcher")
        print("-" * 50)
        
        fetcher = MSLearnFetcher()
        content = fetcher.fetch_module_content(url)
        
        print(f"Title: {content['title']}")
        print(f"Content Length: {len(content['content'])} characters")
        print(f"First 500 chars: {content['content'][:500]}...")
        
        # Method 2: Raw HTML analysis
        print(f"\n📄 METHOD 2: Raw HTML Analysis")
        print("-" * 50)
        
        response = requests.get(url, headers={
            'User-Agent': 'EdutainmentForge/1.0 (Educational Content Analyzer)'
        })
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check what content sections exist
        content_selectors = [
            ('.content', 'Main Content Area'),
            ('main', 'Main Element'),
            ('.main-content', 'Main Content Class'),
            ('.docs-content', 'Docs Content'),
            ('article', 'Article Element'),
            ('.module-content', 'Module Content'),
            ('.learn-content', 'Learn Content'),
            ('[role="main"]', 'Main Role'),
            ('.content-body', 'Content Body'),
            ('.text-content', 'Text Content')
        ]
        
        print("Available content sections:")
        for selector, description in content_selectors:
            elements = soup.select(selector)
            if elements:
                text_length = sum(len(el.get_text()) for el in elements)
                print(f"  ✅ {description} ({selector}): {len(elements)} elements, {text_length} chars")
            else:
                print(f"  ❌ {description} ({selector}): Not found")
        
        # Method 3: Try different extraction strategies
        print(f"\n🎯 METHOD 3: Enhanced Extraction Strategies")
        print("-" * 50)
        
        strategies = [
            ('Current Strategy', extract_with_current_method),
            ('Article-focused', extract_article_content),
            ('Learn-specific', extract_learn_content),
            ('Comprehensive', extract_comprehensive_content)
        ]
        
        for strategy_name, strategy_func in strategies:
            try:
                extracted = strategy_func(soup)
                print(f"{strategy_name}: {len(extracted)} chars")
                if len(extracted) > 200:
                    print(f"  Preview: {extracted[:200]}...")
            except Exception as e:
                print(f"{strategy_name}: Error - {e}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        print(f"❌ Analysis failed: {e}")

def extract_with_current_method(soup):
    """Current extraction method from our fetcher."""
    # Remove unwanted elements
    for element in soup(['script', 'style', 'nav', 'footer', 'aside']):
        element.decompose()
    
    # Try to find main content area
    content_selectors = [
        '.content',
        'main',
        '.main-content',
        '.docs-content',
        'article'
    ]
    
    content_element = None
    for selector in content_selectors:
        element = soup.select_one(selector)
        if element:
            content_element = element
            break
    
    if not content_element:
        content_element = soup.find('body')
    
    if content_element:
        return content_element.get_text(separator=' ', strip=True)
    return ""

def extract_article_content(soup):
    """Focus on article and main content areas."""
    # Remove navigation and sidebar elements
    for element in soup(['nav', 'header', 'footer', 'aside', '.sidebar', '.navigation', '.breadcrumb']):
        element.decompose()
    
    # Look for article or main content
    article = soup.find('article') or soup.find('main') or soup.select_one('[role="main"]')
    
    if article:
        # Remove table of contents and navigation within article
        for toc in article.select('.table-of-contents, .toc, .in-this-article'):
            toc.decompose()
        
        return article.get_text(separator=' ', strip=True)
    
    return soup.get_text(separator=' ', strip=True)

def extract_learn_content(soup):
    """MS Learn specific content extraction."""
    # Remove MS Learn specific navigation
    unwanted_selectors = [
        'nav', 'header', 'footer', '.site-header', '.site-footer',
        '.breadcrumb', '.table-of-contents', '.feedback-container',
        '.next-step', '.module-list', '.learning-path-header'
    ]
    
    for selector in unwanted_selectors:
        for element in soup.select(selector):
            element.decompose()
    
    # MS Learn specific content selectors
    content_selectors = [
        '.content',
        '.learn-content', 
        '.module-content',
        '.docs-content',
        'main[role="main"]',
        '.content-body'
    ]
    
    for selector in content_selectors:
        element = soup.select_one(selector)
        if element:
            # Clean up within the content
            for unwanted in element.select('.alert', '.note', '.tip', '.important'):
                # Keep the text but remove styling
                unwanted.unwrap() if unwanted else None
            
            return element.get_text(separator=' ', strip=True)
    
    # Fallback to body
    return soup.body.get_text(separator=' ', strip=True) if soup.body else ""

def extract_comprehensive_content(soup):
    """Most comprehensive extraction strategy."""
    # Remove scripts, styles, and navigation
    for element in soup(['script', 'style', 'nav', 'header', 'footer']):
        element.decompose()
    
    # Remove MS Learn specific elements that aren't content
    ms_learn_unwanted = [
        '.breadcrumb-container', '.feedback-container', '.recommendation-container',
        '.module-picker', '.unit-collection', '.next-unit', '.prev-unit',
        '.completion-status', '.progress-indicator', '.site-banner'
    ]
    
    for selector in ms_learn_unwanted:
        for element in soup.select(selector):
            element.decompose()
    
    # Get all text but clean it up
    text = soup.get_text(separator=' ', strip=True)
    
    # Remove common MS Learn navigation text
    unwanted_phrases = [
        'Skip to main content',
        'Table of contents',
        'In this article',
        'Next steps',
        'Related articles',
        'Sign in',
        'Microsoft Learn',
        'Browse training',
        'Your progress'
    ]
    
    for phrase in unwanted_phrases:
        text = text.replace(phrase, '')
    
    # Clean up whitespace
    import re
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()

def main():
    """Main function to analyze AI-900 content extraction."""
    
    # AI-900 specific URLs
    test_urls = [
        "https://learn.microsoft.com/en-us/training/modules/get-started-ai-fundamentals/",
        "https://learn.microsoft.com/en-us/training/modules/fundamentals-machine-learning/",
        "https://learn.microsoft.com/en-us/training/modules/fundamentals-generative-ai/"
    ]
    
    print("🎯 EdutainmentForge Content Analysis")
    print("Analyzing AI-900 module content extraction")
    print("=" * 80)
    
    for url in test_urls:
        analyze_content_extraction(url)
        print("\n" + "="*80)
    
    print("\n✅ Content analysis complete!")
    print("\nRecommendations will be based on the analysis above.")

if __name__ == "__main__":
    main()
