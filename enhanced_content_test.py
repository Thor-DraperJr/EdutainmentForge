"""
Enhanced AI-900 Content Extraction

Extracts the full module content including all units/lessons, not just the overview.
"""

import sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils import setup_logger

def get_module_units(module_url: str):
    """Get all unit URLs from a module landing page."""
    logger = setup_logger()
    
    try:
        response = requests.get(module_url, headers={
            'User-Agent': 'EdutainmentForge/1.0 (Educational Content Analyzer)'
        })
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find unit links in the module
        unit_links = []
        
        # Strategy 1: Look for unit list links
        unit_selectors = [
            'a[href*="/training/modules/"][href*="/units/"]',  # Direct unit links
            '.unit-collection a[href*="/units/"]',            # Unit collection
            '.module-units a[href*="/units/"]',               # Module units
            '.unit-list a[href*="/units/"]'                   # Unit list
        ]
        
        for selector in unit_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href and '/units/' in href:
                    # Make absolute URL
                    if href.startswith('/'):
                        href = 'https://learn.microsoft.com' + href
                    elif not href.startswith('http'):
                        href = module_url.rstrip('/') + '/' + href.lstrip('/')
                    
                    title = link.get_text().strip()
                    unit_links.append({
                        'url': href,
                        'title': title
                    })
        
        # Strategy 2: If no units found, try to find the first unit
        if not unit_links:
            # Common pattern: module URL + first unit
            base_url = module_url.rstrip('/')
            potential_first_unit = f"{base_url}/1-introduction"
            
            # Test if this URL exists
            test_response = requests.head(potential_first_unit)
            if test_response.status_code == 200:
                unit_links.append({
                    'url': potential_first_unit,
                    'title': 'Introduction'
                })
        
        logger.info(f"Found {len(unit_links)} units in module")
        return unit_links
        
    except Exception as e:
        logger.error(f"Failed to get module units: {e}")
        return []

def extract_unit_content(unit_url: str):
    """Extract content from a specific unit/lesson page."""
    logger = setup_logger()
    
    try:
        response = requests.get(unit_url, headers={
            'User-Agent': 'EdutainmentForge/1.0 (Educational Content Analyzer)'
        })
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements
        unwanted_selectors = [
            'script', 'style', 'nav', 'header', 'footer', 'aside',
            '.breadcrumb', '.feedback', '.next-unit', '.prev-unit',
            '.completion-status', '.progress-indicator', '.site-banner',
            '.table-of-contents', '.unit-navigation'
        ]
        
        for selector in unwanted_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        # Extract main content
        content_selectors = [
            '.content .content-body',    # Main content body
            '.unit-body',                # Unit content
            'main .content',             # Main content
            '[role="main"] .content',    # Main role content
            '.lesson-content',           # Lesson content
            '.module-content'            # Module content
        ]
        
        content_text = ""
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                content_text = element.get_text(separator=' ', strip=True)
                break
        
        # Fallback to main element
        if not content_text:
            main_element = soup.find('main') or soup.select_one('[role="main"]')
            if main_element:
                content_text = main_element.get_text(separator=' ', strip=True)
        
        # Final fallback to body
        if not content_text:
            content_text = soup.body.get_text(separator=' ', strip=True) if soup.body else ""
        
        # Clean up the text
        import re
        content_text = re.sub(r'\s+', ' ', content_text)
        content_text = re.sub(r'\n\s*\n', '\n\n', content_text)
        
        # Remove common navigation text
        unwanted_phrases = [
            'Skip to main content', 'Table of contents', 'In this article',
            'Next steps', 'Related articles', 'Sign in', 'Microsoft Learn',
            'Browse training', 'Your progress', 'Completed', 'Next unit',
            'Previous unit', 'Continue'
        ]
        
        for phrase in unwanted_phrases:
            content_text = content_text.replace(phrase, '')
        
        content_text = content_text.strip()
        
        logger.info(f"Extracted {len(content_text)} characters from unit")
        return content_text
        
    except Exception as e:
        logger.error(f"Failed to extract unit content: {e}")
        return ""

def get_full_module_content(module_url: str):
    """Get complete module content by combining all units."""
    logger = setup_logger()
    
    print(f"\n🎯 EXTRACTING FULL CONTENT FROM: {module_url}")
    print("=" * 80)
    
    # Get module overview first
    try:
        response = requests.get(module_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title_element = soup.find('h1')
        module_title = title_element.get_text().strip() if title_element else "Unknown Module"
        
        description_element = soup.select_one('.module-description, .content p, .description')
        module_description = description_element.get_text().strip() if description_element else ""
        
        print(f"📚 Module: {module_title}")
        print(f"📝 Description: {module_description}")
        
    except Exception as e:
        print(f"❌ Failed to get module overview: {e}")
        module_title = "Unknown Module"
        module_description = ""
    
    # Get all units
    units = get_module_units(module_url)
    print(f"🔍 Found {len(units)} units to process")
    
    if not units:
        print("⚠️  No units found, trying direct content extraction...")
        content = extract_unit_content(module_url)
        return {
            'title': module_title,
            'description': module_description,
            'content': content,
            'units': [],
            'total_length': len(content)
        }
    
    # Extract content from each unit
    all_content = []
    all_content.append(f"# {module_title}\n\n{module_description}\n\n")
    
    for i, unit in enumerate(units, 1):
        print(f"📖 Processing Unit {i}: {unit['title']}")
        
        unit_content = extract_unit_content(unit['url'])
        
        if unit_content and len(unit_content) > 100:  # Only include substantial content
            all_content.append(f"## Unit {i}: {unit['title']}\n\n{unit_content}\n\n")
            print(f"   ✅ Added {len(unit_content)} characters")
        else:
            print(f"   ⚠️  Skipped (insufficient content: {len(unit_content)} chars)")
        
        # Be respectful to the server
        time.sleep(1)
    
    full_content = "\n".join(all_content)
    
    return {
        'title': module_title,
        'description': module_description,
        'content': full_content,
        'units': units,
        'total_length': len(full_content)
    }

def main():
    """Test full content extraction for AI-900 modules."""
    
    test_urls = [
        "https://learn.microsoft.com/en-us/training/modules/get-started-ai-fundamentals/",
        "https://learn.microsoft.com/en-us/training/modules/fundamentals-machine-learning/"
    ]
    
    print("🚀 EdutainmentForge Enhanced Content Extraction")
    print("Testing full module content extraction for AI-900")
    print("=" * 80)
    
    for url in test_urls:
        result = get_full_module_content(url)
        
        print(f"\n📊 RESULTS:")
        print(f"   Title: {result['title']}")
        print(f"   Units Found: {len(result['units'])}")
        print(f"   Total Content: {result['total_length']} characters")
        print(f"   Content Preview (first 300 chars):")
        print(f"   {result['content'][:300]}...")
        
        print("\n" + "="*80)
    
    print("\n✅ Enhanced content extraction test complete!")

if __name__ == "__main__":
    main()
