"""
Quick test to see what modules are in the AI-900 learning path.
"""

import requests
from bs4 import BeautifulSoup

def quick_test():
    """Quick test to see the learning path structure."""
    url = "https://learn.microsoft.com/en-us/training/paths/introduction-to-ai-on-azure/"
    
    print("🔍 Quick Learning Path Analysis")
    print("=" * 50)
    print(f"URL: {url}")
    print()
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title_elem = soup.find('h1')
        title = title_elem.get_text().strip() if title_elem else "Unknown"
        print(f"Title: {title}")
        print()
        
        # Look for module links
        print("🔗 Looking for module links...")
        module_links = soup.find_all('a', href=True)
        
        module_urls = []
        for link in module_links:
            href = link.get('href')
            if href and '/training/modules/' in href:
                # Make absolute URL
                if href.startswith('/'):
                    href = 'https://learn.microsoft.com' + href
                
                if href not in module_urls:
                    module_urls.append(href)
                    print(f"  📖 Module: {href}")
        
        print(f"\n📊 Found {len(module_urls)} modules")
        
        # Test extracting content from first module
        if module_urls:
            print(f"\n🧪 Testing content extraction from first module...")
            test_url = module_urls[0]
            
            response = requests.get(test_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove scripts, styles, nav
            for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                tag.decompose()
            
            # Get main content
            main_content = soup.find('main') or soup.find('body')
            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
                text = ' '.join(text.split())  # Clean whitespace
                
                print(f"📝 Content length: {len(text)} characters")
                print(f"📄 Preview: {text[:400]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    quick_test()
