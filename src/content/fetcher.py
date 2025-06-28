"""
Microsoft Learn content fetcher.

Handles retrieving and processing content from MS Learn modules.
"""

import requests
import re
import time
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger


logger = get_logger(__name__)


class ContentFetchError(Exception):
    """Raised when content cannot be fetched or processed."""
    pass


class MSLearnFetcher:
    """Fetches and processes Microsoft Learn content."""
    
    def __init__(self, base_url: str = "https://docs.microsoft.com"):
        """
        Initialize the MS Learn content fetcher.
        
        Args:
            base_url: Base URL for MS Learn documentation
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'EdutainmentForge/1.0 (Educational Podcast Generator)'
        })
    
    def fetch_module_content(self, module_url: str) -> Dict[str, str]:
        """
        Fetch content from a Microsoft Learn module.
        
        Args:
            module_url: URL of the MS Learn module
            
        Returns:
            Dictionary containing module content with keys:
            - title: Module title
            - content: Cleaned text content
            - url: Source URL
            
        Raises:
            ContentFetchError: If content cannot be retrieved
        """
        try:
            logger.info(f"Fetching content from: {module_url}")
            
            # Ensure URL is absolute
            if not module_url.startswith('http'):
                module_url = urljoin(self.base_url, module_url)
            
            # First, try to get the full module content by extracting all units
            full_content = self._extract_full_module_content(module_url)
            
            if full_content and len(full_content['content']) > 500:
                return full_content
            
            # Fallback to single page extraction
            response = self.session.get(module_url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = self._extract_title(soup)
            
            # Extract main content
            content = self._extract_content(soup)
            
            logger.info(f"Successfully fetched content: {title}")
            
            return {
                'title': title,
                'content': content,
                'url': module_url
            }
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch content from {module_url}: {e}")
            raise ContentFetchError(f"Network error: {e}")
        except Exception as e:
            logger.error(f"Error processing content from {module_url}: {e}")
            raise ContentFetchError(f"Content processing error: {e}")
    
    def _extract_full_module_content(self, module_url: str) -> Optional[Dict[str, str]]:
        """Extract complete module content by following all units."""
        try:
            # Get module overview
            response = self.session.get(module_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title = self._extract_title(soup)
            description = self._extract_module_description(soup)
            
            # Find all unit URLs
            unit_urls = self._find_module_units(module_url, soup)
            
            if not unit_urls:
                return None
            
            logger.info(f"Found {len(unit_urls)} units in module")
            
            # Extract content from all units
            all_content = [f"# {title}\n\n{description}\n\n"]
            
            for i, unit_info in enumerate(unit_urls, 1):
                unit_content = self._extract_unit_content(unit_info['url'])
                if unit_content and len(unit_content) > 100:
                    all_content.append(f"## Unit {i}: {unit_info['title']}\n\n{unit_content}\n\n")
                    logger.debug(f"Added unit {i}: {len(unit_content)} characters")
                
                # Be respectful to the server
                time.sleep(0.5)
            
            full_content = "\n".join(all_content)
            
            return {
                'title': title,
                'content': full_content,
                'url': module_url
            }
            
        except Exception as e:
            logger.warning(f"Failed to extract full module content: {e}")
            return None
    
    def _extract_module_description(self, soup: BeautifulSoup) -> str:
        """Extract module description."""
        description_selectors = [
            '.module-description',
            '.content .description', 
            '.overview p',
            '.module-overview p',
            'meta[name="description"]'
        ]
        
        for selector in description_selectors:
            if selector.startswith('meta'):
                element = soup.select_one(selector)
                if element:
                    return element.get('content', '').strip()
            else:
                element = soup.select_one(selector)
                if element:
                    desc = element.get_text().strip()
                    if desc and len(desc) > 20:
                        return desc
        
        return ""
    
    def _find_module_units(self, module_url: str, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Find all unit URLs in a module."""
        unit_urls = []
        
        # Strategy 1: Look for unit navigation or listing
        unit_link_selectors = [
            'a[href*="/training/modules/"][href*="/units/"]',
            'a[href*="/' + module_url.split('/')[-2] + '/"]',  # Same module different units
            '.unit-collection a', 
            '.module-units a',
            '.unit-list a'
        ]
        
        for selector in unit_link_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href and ('/units/' in href or any(num in href for num in ['1-', '2-', '3-', '4-', '5-'])):
                    # Make absolute URL
                    if href.startswith('/'):
                        href = 'https://learn.microsoft.com' + href
                    elif not href.startswith('http'):
                        base = '/'.join(module_url.split('/')[:-1])
                        href = base + '/' + href.lstrip('/')
                    
                    title = link.get_text().strip()
                    if title and href not in [u['url'] for u in unit_urls]:
                        unit_urls.append({'url': href, 'title': title})
        
        # Strategy 2: Try common unit URL patterns
        if not unit_urls:
            base_url = module_url.rstrip('/')
            common_units = [
                '1-introduction',
                '2-',  # Will be expanded
                '3-',
                '4-',
                '5-'
            ]
            
            for unit_pattern in common_units:
                if unit_pattern.endswith('-'):
                    # Try to find what comes after the number
                    continue
                    
                test_url = f"{base_url}/{unit_pattern}"
                try:
                    response = self.session.head(test_url, timeout=10)
                    if response.status_code == 200:
                        unit_urls.append({
                            'url': test_url,
                            'title': unit_pattern.replace('-', ' ').title()
                        })
                except:
                    continue
        
        # Strategy 3: If this is already a unit URL, find siblings
        if not unit_urls and ('/1-' in module_url or '/units/' in module_url):
            # This might be a direct unit URL, treat it as the only unit
            unit_urls.append({
                'url': module_url,
                'title': 'Main Content'
            })
        
        return unit_urls[:10]  # Limit to reasonable number of units
    
    def _extract_unit_content(self, unit_url: str) -> str:
        """Extract content from a specific unit page."""
        try:
            response = self.session.get(unit_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            unwanted_selectors = [
                'script', 'style', 'nav', 'header', 'footer', 'aside',
                '.breadcrumb', '.feedback', '.next-unit', '.prev-unit',
                '.completion-status', '.progress-indicator', '.site-banner',
                '.table-of-contents', '.unit-navigation', '.next-steps'
            ]
            
            for selector in unwanted_selectors:
                for element in soup.select(selector):
                    element.decompose()
            
            # Extract main content with enhanced selectors
            content_selectors = [
                '.content .content-body',
                'main .content',
                '[role="main"] .content',
                '.unit-body',
                '.lesson-content',
                '.module-content',
                'main'
            ]
            
            content_text = ""
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content_text = element.get_text(separator=' ', strip=True)
                    if len(content_text) > 200:  # Good content found
                        break
            
            # Fallback to body if needed
            if not content_text or len(content_text) < 100:
                content_text = soup.body.get_text(separator=' ', strip=True) if soup.body else ""
            
            # Clean up the text
            content_text = self._clean_extracted_text(content_text)
            
            return content_text
            
        except Exception as e:
            logger.warning(f"Failed to extract unit content from {unit_url}: {e}")
            return ""
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean extracted text content."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove common navigation and UI text
        unwanted_phrases = [
            'Skip to main content', 'Table of contents', 'In this article',
            'Next steps', 'Related articles', 'Sign in', 'Microsoft Learn',
            'Browse training', 'Your progress', 'Completed', 'Next unit',
            'Previous unit', 'Continue', 'Need help?', 'See our troubleshooting guide',
            'Was this page helpful?', 'YesNo', 'Content language selector',
            'Your Privacy Choices', 'Previous Versions', 'Blog', 'Contribute',
            'Privacy', 'Terms of Use', 'Trademarks', '© Microsoft'
        ]
        
        for phrase in unwanted_phrases:
            text = text.replace(phrase, '')
        
        # Remove URLs and email addresses
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'\S+@\S+', '', text)
        
        # Clean up whitespace again
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    def fetch_learning_path_modules(self, path_url: str) -> List[Dict[str, str]]:
        """
        Fetch all modules from a learning path.
        
        Args:
            path_url: URL of the learning path
            
        Returns:
            List of module dictionaries
        """
        try:
            logger.info(f"Fetching learning path: {path_url}")
            
            response = self.session.get(path_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            modules = []
            # Look for module links in the learning path
            module_links = soup.find_all('a', href=True)
            
            for link in module_links:
                href = link.get('href')
                if href and '/training/modules/' in href:
                    # Make absolute URL
                    if href.startswith('/'):
                        href = urljoin(self.base_url, href)
                    
                    # Get module title from link text or nearby elements
                    title = link.get_text().strip()
                    if not title:
                        # Try to find title in nearby elements
                        parent = link.parent
                        if parent:
                            title_elem = parent.find(['h3', 'h4', 'span', 'div'])
                            if title_elem:
                                title = title_elem.get_text().strip()
                    
                    if not title:
                        title = f"Module from {href.split('/')[-2] if href.endswith('/') else href.split('/')[-1]}"
                    
                    # Avoid duplicates
                    if not any(m['url'] == href for m in modules):
                        modules.append({
                            'title': title,
                            'url': href,
                            'description': f'Module from {path_url}'
                        })
            
            logger.info(f"Found {len(modules)} modules in learning path")
            return modules
            
        except Exception as e:
            logger.error(f"Failed to fetch learning path modules: {e}")
            return self.get_sample_modules()
    
    def get_sample_modules(self) -> List[Dict[str, str]]:
        """
        Get a list of sample MS Learn modules for testing.
        
        Returns:
            List of dictionaries with module info (title, url, description)
        """
        return [
            {
                'title': 'Introduction to AI concepts',
                'url': 'https://learn.microsoft.com/en-us/training/modules/get-started-ai-fundamentals/',
                'description': 'Learn about artificial intelligence fundamentals'
            },
            {
                'title': 'Introduction to machine learning concepts', 
                'url': 'https://learn.microsoft.com/en-us/training/modules/fundamentals-machine-learning/',
                'description': 'Understand machine learning basics'
            },
            {
                'title': 'Introduction to generative AI concepts',
                'url': 'https://learn.microsoft.com/en-us/training/modules/fundamentals-generative-ai/',
                'description': 'Explore generative AI fundamentals'
            }
        ]
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the module title from HTML."""
        # Try different title selectors
        title_selectors = [
            'h1.title',
            'h1',
            'title',
            '.content-header h1',
            '[data-module-title]'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text().strip()
                if title and title != "Microsoft Learn":
                    return title
        
        return "Untitled Module"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract and clean the main content from HTML."""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'aside', 'header']):
            element.decompose()
        
        # Try to find main content area
        content_selectors = [
            '.content',
            'main',
            '.main-content',
            '.docs-content',
            'article',
            '[role="main"]'
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
        
        if not content_element:
            raise ContentFetchError("Could not find content in page")
        
        # Extract text and clean it up
        text = content_element.get_text(separator=' ', strip=True)
        
        # Clean up whitespace and formatting
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single space
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Clean up line breaks
        
        # Remove common navigation text
        unwanted_phrases = [
            'Skip to main content',
            'Table of contents',
            'In this article',
            'Next steps',
            'Related articles',
            'Microsoft Learn',
            'Training',
            'Browse all'
        ]
        
        for phrase in unwanted_phrases:
            text = text.replace(phrase, '')
        
        return text.strip()


def create_sample_content() -> Dict[str, str]:
    """
    Create sample content for testing when no internet connection.
    
    Returns:
        Sample module content dictionary
    """
    return {
        'title': 'Introduction to Cloud Computing',
        'content': """
        Cloud computing is the delivery of computing services including servers, 
        storage, databases, networking, software, analytics, and intelligence over 
        the Internet to offer faster innovation, flexible resources, and economies 
        of scale.
        
        The main benefits of cloud computing include:
        
        Cost: Cloud computing eliminates the capital expense of buying hardware 
        and software and setting up and running on-site datacenters.
        
        Speed: Most cloud computing services are provided self service and on 
        demand, so even vast amounts of computing resources can be provisioned 
        in minutes.
        
        Global scale: The benefits of cloud computing services include the 
        ability to scale elastically. In cloud speak, that means delivering 
        the right amount of IT resources when they're needed.
        
        Productivity: On-site datacenters typically require a lot of racking 
        and stacking hardware setup, software patching, and other time-consuming 
        IT management chores.
        
        Performance: The biggest cloud computing services run on a worldwide 
        network of secure datacenters, which are regularly upgraded to the 
        latest generation of fast and efficient computing hardware.
        
        Reliability: Cloud computing makes data backup, disaster recovery, 
        and business continuity easier and less expensive because data can 
        be mirrored at multiple redundant sites on the cloud provider's network.
        """,
        'url': 'https://example.com/cloud-computing-intro'
    }
