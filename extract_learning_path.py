"""
Learning Path Content Extractor for EdutainmentForge.

Extracts complete content from MS Learn learning paths by:
1. Parsing the learning path to get all modules
2. For each module, finding all units
3. Extracting content from each unit
4. Combining into comprehensive module content
"""

import sys
import time
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from content import MSLearnFetcher
from utils import setup_logger
import requests
from bs4 import BeautifulSoup


class LearningPathExtractor:
    """Extracts complete content from MS Learn learning paths."""
    
    def __init__(self):
        self.logger = setup_logger()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'EdutainmentForge/1.0 (Educational Podcast Generator)'
        })
        self.base_url = "https://learn.microsoft.com"
    
    def extract_learning_path(self, path_url: str) -> Dict:
        """
        Extract complete learning path with all modules and their content.
        
        Args:
            path_url: URL of the learning path
            
        Returns:
            Dictionary with path info and modules
        """
        self.logger.info(f"🎯 Extracting learning path: {path_url}")
        
        try:
            # Get the learning path page
            response = self.session.get(path_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract path metadata
            path_title = self._extract_path_title(soup)
            path_description = self._extract_path_description(soup)
            
            # Extract module URLs
            module_urls = self._extract_module_urls(soup)
            
            self.logger.info(f"📚 Found {len(module_urls)} modules in path: {path_title}")
            
            # Extract content from each module
            modules = []
            for i, module_url in enumerate(module_urls, 1):
                self.logger.info(f"📖 Processing module {i}/{len(module_urls)}: {module_url}")
                
                try:
                    module_data = self._extract_module_content(module_url)
                    modules.append(module_data)
                    
                    # Be respectful to the server
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.error(f"❌ Failed to extract module {module_url}: {e}")
                    continue
            
            return {
                'title': path_title,
                'description': path_description,
                'url': path_url,
                'module_count': len(modules),
                'modules': modules
            }
            
        except Exception as e:
            self.logger.error(f"Failed to extract learning path: {e}")
            raise
    
    def _extract_path_title(self, soup: BeautifulSoup) -> str:
        """Extract the learning path title."""
        selectors = [
            'h1',
            '.page-title',
            '[data-bi-name="title"]',
            '.content-title'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text().strip()
                if title and len(title) > 5:
                    return title
        
        return "Unknown Learning Path"
    
    def _extract_path_description(self, soup: BeautifulSoup) -> str:
        """Extract the learning path description."""
        selectors = [
            '.learning-path-description',
            '.content-description', 
            '.page-description',
            'meta[name="description"]'
        ]
        
        for selector in selectors:
            if selector.startswith('meta'):
                element = soup.select_one(selector)
                if element:
                    return element.get('content', '').strip()
            else:
                element = soup.select_one(selector)
                if element:
                    desc = element.get_text().strip()
                    if desc and len(desc) > 10:
                        return desc
        
        return ""
    
    def _extract_module_urls(self, soup: BeautifulSoup) -> List[str]:
        """Extract all module URLs from the learning path."""
        module_urls = []
        
        # Look for module links in various possible structures
        selectors = [
            'a[href*="/training/modules/"]',
            '.module-link a',
            '.learning-path-module a',
            '[data-module-url]'
        ]
        
        seen_urls = set()
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                if selector == '[data-module-url]':
                    url = element.get('data-module-url')
                else:
                    url = element.get('href')
                
                if url:
                    # Make URL absolute
                    if url.startswith('/'):
                        url = urljoin(self.base_url, url)
                    
                    # Only include module URLs and avoid duplicates
                    if '/training/modules/' in url and url not in seen_urls:
                        seen_urls.add(url)
                        module_urls.append(url)
        
        return module_urls
    
    def _extract_module_content(self, module_url: str) -> Dict:
        """
        Extract complete content from a module by following all units.
        
        Args:
            module_url: URL of the module
            
        Returns:
            Dictionary with module metadata and combined content
        """
        try:
            # Get the module landing page
            response = self.session.get(module_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract module metadata
            module_title = self._extract_title(soup)
            module_description = self._extract_description(soup)
            
            # Find all unit URLs in this module
            unit_urls = self._extract_unit_urls(soup, module_url)
            
            self.logger.info(f"  📝 Found {len(unit_urls)} units in module: {module_title}")
            
            # Extract content from all units
            all_content = []
            
            for unit_url in unit_urls:
                try:
                    unit_content = self._extract_unit_content(unit_url)
                    if unit_content:
                        all_content.append(unit_content)
                    time.sleep(0.5)  # Be respectful
                except Exception as e:
                    self.logger.warning(f"Failed to extract unit {unit_url}: {e}")
                    continue
            
            # Combine all unit content
            combined_content = "\n\n".join(all_content)
            
            return {
                'title': module_title,
                'description': module_description,
                'url': module_url,
                'unit_count': len(unit_urls),
                'content_length': len(combined_content),
                'content': combined_content
            }
            
        except Exception as e:
            self.logger.error(f"Failed to extract module content: {e}")
            raise
    
    def _extract_unit_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all unit URLs from a module page."""
        unit_urls = []
        
        # Look for unit navigation or content links
        selectors = [
            'a[href*="?pivots="]',  # Pivot links
            '.unit-link a',
            '.module-outline a',
            '.table-of-contents a',
            'nav a[href*="/training/modules/"]'
        ]
        
        seen_urls = set()
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                url = element.get('href')
                if url:
                    # Make URL absolute
                    if url.startswith('/'):
                        url = urljoin(self.base_url, url)
                    elif url.startswith('?'):
                        url = base_url + url
                    
                    # Only include unit URLs and avoid duplicates
                    if ('/training/modules/' in url and 
                        url != base_url and 
                        url not in seen_urls):
                        seen_urls.add(url)
                        unit_urls.append(url)
        
        # If no units found, try the main module URL as the content page
        if not unit_urls:
            unit_urls = [base_url]
        
        return unit_urls
    
    def _extract_unit_content(self, unit_url: str) -> str:
        """Extract content from a single unit page."""
        try:
            response = self.session.get(unit_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'aside', 
                               '.navigation', '.breadcrumb', '.feedback']):
                element.decompose()
            
            # Try to find main content area
            content_selectors = [
                '.content',
                'main',
                '.main-content',
                '.module-content',
                '.unit-content',
                '[role="main"]',
                '.docs-content'
            ]
            
            content_element = None
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content_element = element
                    break
            
            # Fall back to body if no content area found
            if not content_element:
                content_element = soup.find('body')
            
            if content_element:
                text = content_element.get_text(separator=' ', strip=True)
                # Clean up whitespace
                text = ' '.join(text.split())
                return text
            
            return ""
            
        except Exception as e:
            self.logger.warning(f"Failed to extract unit content from {unit_url}: {e}")
            return ""
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title from page."""
        selectors = ['h1', '.page-title', '.module-title', 'title']
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text().strip()
                if title and len(title) > 3:
                    return title
        
        return "Unknown Module"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract description from page."""
        selectors = [
            '.module-description',
            '.content-description',
            'meta[name="description"]'
        ]
        
        for selector in selectors:
            if selector.startswith('meta'):
                element = soup.select_one(selector)
                if element:
                    return element.get('content', '').strip()
            else:
                element = soup.select_one(selector)
                if element:
                    desc = element.get_text().strip()
                    if desc and len(desc) > 10:
                        return desc
        
        return ""


def test_ai900_learning_path():
    """Test the complete AI-900 learning path extraction."""
    ai900_path = "https://learn.microsoft.com/en-us/training/paths/introduction-to-ai-on-azure/"
    
    extractor = LearningPathExtractor()
    
    try:
        print("🎯 EdutainmentForge Learning Path Extractor")
        print("=" * 60)
        print(f"Extracting: {ai900_path}")
        print()
        
        path_data = extractor.extract_learning_path(ai900_path)
        
        print("📋 Learning Path Summary:")
        print(f"Title: {path_data['title']}")
        print(f"Description: {path_data['description'][:200]}...")
        print(f"Modules Found: {path_data['module_count']}")
        print()
        
        # Show details for each module
        for i, module in enumerate(path_data['modules'], 1):
            print(f"📖 Module {i}: {module['title']}")
            print(f"   Units: {module['unit_count']}")
            print(f"   Content Length: {module['content_length']:,} characters")
            print(f"   URL: {module['url']}")
            
            # Show content preview
            if module['content']:
                preview = module['content'][:300] + "..." if len(module['content']) > 300 else module['content']
                print(f"   Preview: {preview}")
            print()
        
        # Calculate totals
        total_content = sum(m['content_length'] for m in path_data['modules'])
        total_units = sum(m['unit_count'] for m in path_data['modules'])
        
        print("📊 Summary Statistics:")
        print(f"Total Content: {total_content:,} characters")
        print(f"Total Units: {total_units}")
        print(f"Average per Module: {total_content // len(path_data['modules']):,} characters")
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")


if __name__ == "__main__":
    test_ai900_learning_path()
