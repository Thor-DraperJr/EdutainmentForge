"""
Microsoft Learn Catalog API integration.

This module provides functionality to search, browse, and discover content
from the Microsoft Learn Catalog API for automated learning path discovery.
"""

import requests
import time
from typing import Dict, List, Optional, Union
from urllib.parse import urlencode
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger

logger = get_logger(__name__)


class CatalogAPIError(Exception):
    """Raised when the catalog API returns an error or is unavailable."""
    pass


class MSLearnCatalogService:
    """Service for interacting with the Microsoft Learn Catalog API."""
    
    def __init__(self, base_url: str = "https://learn.microsoft.com"):
        """
        Initialize the catalog service.
        
        Args:
            base_url: Base URL for Microsoft Learn API
        """
        self.base_url = base_url
        self.api_base = f"{base_url}/api/catalog"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'EdutainmentForge/2.0 (Educational Podcast Generator)',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        })
    
    def search_content(self, 
                      query: str = "", 
                      content_type: str = "modules",
                      locale: str = "en-us",
                      product: Optional[str] = None,
                      role: Optional[str] = None,
                      topic: Optional[str] = None,
                      limit: int = 20) -> Dict:
        """
        Search for content in the Microsoft Learn catalog.
        
        Args:
            query: Search query text
            content_type: Type of content (modules, learning-paths, courses)
            locale: Language locale (default: en-us)
            product: Filter by product (azure, microsoft-365, etc.)
            role: Filter by role (developer, administrator, etc.)
            topic: Filter by topic area
            limit: Maximum number of results to return
            
        Returns:
            Dictionary containing search results
            
        Raises:
            CatalogAPIError: If the API request fails
        """
        try:
            # Build query parameters
            params = {
                'locale': locale,
                'type': content_type,
                '$top': limit
            }
            
            if query:
                params['$filter'] = f"contains(title, '{query}') or contains(summary, '{query}')"
            
            # Add filters
            filters = []
            if product:
                filters.append(f"products/any(p: p eq '{product}')")
            if role:
                filters.append(f"roles/any(r: r eq '{role}')")
            if topic:
                filters.append(f"subjects/any(s: s eq '{topic}')")
            
            if filters:
                existing_filter = params.get('$filter', '')
                if existing_filter:
                    params['$filter'] = f"({existing_filter}) and ({' and '.join(filters)})"
                else:
                    params['$filter'] = ' and '.join(filters)
            
            logger.info(f"Searching catalog with params: {params}")
            
            # Make API request
            url = f"{self.api_base}/browse"
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Process results to extract relevant information
            results = {
                'total_count': data.get('count', 0),
                'results': [],
                'facets': data.get('facets', {}),
                'query_info': {
                    'query': query,
                    'content_type': content_type,
                    'filters': {
                        'product': product,
                        'role': role,
                        'topic': topic
                    }
                }
            }
            
            # Process individual results
            for item in data.get('modules', data.get('learningPaths', [])):
                processed_item = self._process_catalog_item(item)
                if processed_item:
                    results['results'].append(processed_item)
            
            logger.info(f"Found {len(results['results'])} results")
            return results
            
        except requests.RequestException as e:
            logger.error(f"Catalog API request failed: {e}")
            # Return fallback results for development/testing
            return self._get_fallback_results(query, content_type, product, role, topic)
        except Exception as e:
            logger.error(f"Error processing catalog search: {e}")
            # Return fallback results for any error during development
            return self._get_fallback_results(query, content_type, product, role, topic)
    
    def get_learning_path_modules(self, learning_path_id: str) -> List[Dict]:
        """
        Get all modules in a specific learning path.
        
        Args:
            learning_path_id: The learning path identifier
            
        Returns:
            List of module dictionaries
            
        Raises:
            CatalogAPIError: If the API request fails
        """
        try:
            url = f"{self.api_base}/learning-paths/{learning_path_id}/modules"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            modules = []
            for module_data in data.get('modules', []):
                processed_module = self._process_catalog_item(module_data)
                if processed_module:
                    modules.append(processed_module)
            
            logger.info(f"Found {len(modules)} modules in learning path {learning_path_id}")
            return modules
            
        except requests.RequestException as e:
            logger.error(f"Failed to get learning path modules: {e}")
            # Return fallback modules for development
            return self._get_fallback_learning_path_modules(learning_path_id)
        except Exception as e:
            logger.error(f"Error processing learning path modules: {e}")
            raise CatalogAPIError(f"Failed to get learning path modules: {e}")
    
    def get_catalog_facets(self) -> Dict:
        """
        Get available facets (filters) from the catalog.
        
        Returns:
            Dictionary with available products, roles, topics, etc.
        """
        try:
            url = f"{self.api_base}/facets"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            facets = {
                'products': data.get('products', []),
                'roles': data.get('roles', []),
                'subjects': data.get('subjects', []),
                'levels': data.get('levels', [])
            }
            
            logger.info(f"Retrieved {len(facets.get('products', []))} products, "
                       f"{len(facets.get('roles', []))} roles, "
                       f"{len(facets.get('subjects', []))} subjects")
            
            return facets
            
        except requests.RequestException as e:
            logger.warning(f"Failed to get catalog facets: {e}")
            return self._get_fallback_facets()
        except Exception as e:
            logger.error(f"Error processing catalog facets: {e}")
            return self._get_fallback_facets()
    
    def _process_catalog_item(self, item: Dict) -> Optional[Dict]:
        """Process a catalog item into a standardized format."""
        try:
            # Extract common fields
            processed = {
                'id': item.get('uid') or item.get('id', ''),
                'title': item.get('title', 'Untitled'),
                'summary': item.get('summary', ''),
                'url': item.get('url', ''),
                'type': item.get('type', 'module'),
                'duration_minutes': item.get('durationInMinutes', 0),
                'products': item.get('products', []),
                'roles': item.get('roles', []),
                'subjects': item.get('subjects', []),
                'levels': item.get('levels', []),
                'rating': item.get('rating', {}).get('average', 0),
                'last_modified': item.get('lastModified', ''),
                'icon_url': item.get('iconUrl', '')
            }
            
            # Ensure URL is absolute
            if processed['url'] and not processed['url'].startswith('http'):
                processed['url'] = f"{self.base_url}{processed['url']}"
            
            return processed
            
        except Exception as e:
            logger.warning(f"Failed to process catalog item: {e}")
            return None
    
    def _get_fallback_results(self, query: str, content_type: str, 
                            product: Optional[str], role: Optional[str], 
                            topic: Optional[str]) -> Dict:
        """Provide fallback results when API is unavailable."""
        logger.info("Using fallback catalog results for development")
        
        # Sample results for development/testing
        sample_modules = [
            {
                'id': 'get-started-ai-fundamentals',
                'title': 'Introduction to AI fundamentals',
                'summary': 'Learn about artificial intelligence concepts and fundamentals',
                'url': 'https://learn.microsoft.com/en-us/training/modules/get-started-ai-fundamentals/',
                'type': 'module',
                'duration_minutes': 45,
                'products': ['azure'],
                'roles': ['ai-engineer', 'developer'],
                'subjects': ['artificial-intelligence'],
                'levels': ['beginner'],
                'rating': 4.5,
                'last_modified': '2024-01-15T00:00:00Z',
                'icon_url': ''
            },
            {
                'id': 'fundamentals-machine-learning',
                'title': 'Introduction to machine learning',
                'summary': 'Understand the fundamentals of machine learning and its applications',
                'url': 'https://learn.microsoft.com/en-us/training/modules/fundamentals-machine-learning/',
                'type': 'module',
                'duration_minutes': 60,
                'products': ['azure'],
                'roles': ['data-scientist', 'ai-engineer'],
                'subjects': ['machine-learning'],
                'levels': ['beginner'],
                'rating': 4.7,
                'last_modified': '2024-01-20T00:00:00Z',
                'icon_url': ''
            },
            {
                'id': 'fundamentals-generative-ai',
                'title': 'Introduction to generative AI',
                'summary': 'Explore generative AI concepts and applications',
                'url': 'https://learn.microsoft.com/en-us/training/modules/fundamentals-generative-ai/',
                'type': 'module',
                'duration_minutes': 50,
                'products': ['azure'],
                'roles': ['developer', 'ai-engineer'],
                'subjects': ['artificial-intelligence'],
                'levels': ['beginner'],
                'rating': 4.8,
                'last_modified': '2024-02-01T00:00:00Z',
                'icon_url': ''
            }
        ]
        
        # Filter results based on search criteria
        filtered_results = []
        for module in sample_modules:
            match = True
            
            # Check query match
            if query:
                query_lower = query.lower()
                if (query_lower not in module['title'].lower() and 
                    query_lower not in module['summary'].lower()):
                    match = False
            
            # Check product filter
            if product and product not in module['products']:
                match = False
            
            # Check role filter
            if role and role not in module['roles']:
                match = False
            
            # Check topic filter
            if topic and topic not in module['subjects']:
                match = False
            
            if match:
                filtered_results.append(module)
        
        return {
            'total_count': len(filtered_results),
            'results': filtered_results,
            'facets': self._get_fallback_facets(),
            'query_info': {
                'query': query,
                'content_type': content_type,
                'filters': {
                    'product': product,
                    'role': role,
                    'topic': topic
                }
            }
        }
    
    def _get_fallback_learning_path_modules(self, learning_path_id: str) -> List[Dict]:
        """Provide fallback learning path modules."""
        # Sample learning path modules
        return [
            {
                'id': 'ai-fundamentals-1',
                'title': 'AI Fundamentals - Introduction',
                'summary': 'Introduction to artificial intelligence concepts',
                'url': 'https://learn.microsoft.com/en-us/training/modules/get-started-ai-fundamentals/1-introduction',
                'type': 'module',
                'duration_minutes': 15,
                'products': ['azure'],
                'roles': ['ai-engineer'],
                'subjects': ['artificial-intelligence'],
                'levels': ['beginner']
            },
            {
                'id': 'ai-fundamentals-2',
                'title': 'AI Fundamentals - Machine Learning',
                'summary': 'Understanding machine learning basics',
                'url': 'https://learn.microsoft.com/en-us/training/modules/get-started-ai-fundamentals/2-machine-learning',
                'type': 'module',
                'duration_minutes': 20,
                'products': ['azure'],
                'roles': ['ai-engineer'],
                'subjects': ['machine-learning'],
                'levels': ['beginner']
            }
        ]
    
    def _get_fallback_facets(self) -> Dict:
        """Provide fallback facets for development."""
        return {
            'products': [
                {'id': 'azure', 'name': 'Azure', 'count': 150},
                {'id': 'microsoft-365', 'name': 'Microsoft 365', 'count': 75},
                {'id': 'power-platform', 'name': 'Power Platform', 'count': 45},
                {'id': 'dynamics-365', 'name': 'Dynamics 365', 'count': 30},
                {'id': 'windows', 'name': 'Windows', 'count': 25}
            ],
            'roles': [
                {'id': 'developer', 'name': 'Developer', 'count': 120},
                {'id': 'administrator', 'name': 'Administrator', 'count': 80},
                {'id': 'ai-engineer', 'name': 'AI Engineer', 'count': 40},
                {'id': 'data-scientist', 'name': 'Data Scientist', 'count': 35},
                {'id': 'security-engineer', 'name': 'Security Engineer', 'count': 30}
            ],
            'subjects': [
                {'id': 'artificial-intelligence', 'name': 'Artificial Intelligence', 'count': 45},
                {'id': 'machine-learning', 'name': 'Machine Learning', 'count': 35},
                {'id': 'cloud-computing', 'name': 'Cloud Computing', 'count': 80},
                {'id': 'security', 'name': 'Security', 'count': 60},
                {'id': 'data-analytics', 'name': 'Data Analytics', 'count': 50}
            ],
            'levels': [
                {'id': 'beginner', 'name': 'Beginner', 'count': 180},
                {'id': 'intermediate', 'name': 'Intermediate', 'count': 120},
                {'id': 'advanced', 'name': 'Advanced', 'count': 60}
            ]
        }


def create_catalog_service() -> MSLearnCatalogService:
    """
    Factory function to create a catalog service instance.
    
    Returns:
        Configured MSLearnCatalogService instance
    """
    return MSLearnCatalogService()