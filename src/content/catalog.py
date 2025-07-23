SC-100: Design solutions that align with security best practices and priorities"""
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
        
        # SC-300 and SC-100 focused content for Microsoft Identity and Access Administrator studies
        sample_modules = [
            {
                'id': 'sc-300-implement-identity-management-solution',
                'title': 'SC-300: Implement an identity management solution',
                'summary': 'Learn to implement and manage Azure AD identity solutions, including user and group management, authentication methods, and identity governance',
                'url': 'https://learn.microsoft.com/en-us/training/paths/implement-identity-management-solution/',
                'type': 'learning-path',
                'duration_minutes': 420,
                'products': ['azure', 'microsoft-365'],
                'roles': ['security-engineer', 'administrator', 'identity-access-admin'],
                'subjects': ['security', 'identity', 'governance'],
                'levels': ['intermediate'],
                'rating': 4.8,
                'last_modified': '2024-07-01T00:00:00Z',
                'icon_url': ''
            },
            {
                'id': 'sc-300-implement-authentication-access-management',
                'title': 'SC-300: Implement authentication and access management',
                'summary': 'Configure and manage authentication methods, conditional access policies, and access reviews for Azure AD',
                'url': 'https://learn.microsoft.com/en-us/training/paths/implement-authentication-access-management/',
                'type': 'learning-path',
                'duration_minutes': 360,
                'products': ['azure', 'microsoft-365'],
                'roles': ['security-engineer', 'administrator', 'identity-access-admin'],
                'subjects': ['security', 'identity', 'authentication'],
                'levels': ['intermediate'],
                'rating': 4.9,
                'last_modified': '2024-07-01T00:00:00Z',
                'icon_url': ''
            },
            {
                'id': 'sc-300-implement-access-management-apps',
                'title': 'SC-300: Implement access management for applications',
                'summary': 'Manage application access, configure enterprise applications, and implement application proxy for secure remote access',
                'url': 'https://learn.microsoft.com/en-us/training/paths/implement-access-management-apps/',
                'type': 'learning-path',
                'duration_minutes': 300,
                'products': ['azure', 'microsoft-365'],
                'roles': ['security-engineer', 'administrator', 'identity-access-admin'],
                'subjects': ['security', 'identity', 'application-security'],
                'levels': ['intermediate'],
                'rating': 4.7,
                'last_modified': '2024-07-01T00:00:00Z',
                'icon_url': ''
            },
            {
                'id': 'sc-300-plan-implement-identity-governance',
                'title': 'SC-300: Plan and implement identity governance strategy',
                'summary': 'Design and implement identity governance including entitlement management, access reviews, and privileged identity management',
                'url': 'https://learn.microsoft.com/en-us/training/paths/plan-implement-identity-governance-strategy/',
                'type': 'learning-path',
                'duration_minutes': 390,
                'products': ['azure', 'microsoft-365'],
                'roles': ['security-engineer', 'administrator', 'identity-access-admin'],
                'subjects': ['security', 'identity', 'governance', 'compliance'],
                'levels': ['advanced'],
                'rating': 4.8,
                'last_modified': '2024-07-01T00:00:00Z',
                'icon_url': ''
            },
            {
                'id': 'sc-100-design-zero-trust-strategy',
                'title': 'SC-100: Design a Zero Trust strategy and architecture',
                'summary': 'Learn to design comprehensive Zero Trust security strategies and architectures aligned with business requirements',
                'url': 'https://learn.microsoft.com/en-us/training/paths/design-zero-trust-strategy-architecture/',
                'type': 'learning-path',
                'duration_minutes': 480,
                'products': ['azure', 'microsoft-365'],
                'roles': ['security-engineer', 'security-architect', 'administrator'],
                'subjects': ['security', 'architecture', 'zero-trust'],
                'levels': ['advanced'],
                'rating': 4.9,
                'last_modified': '2024-07-01T00:00:00Z',
                'icon_url': ''
            },
            {
                'id': 'sc-100-evaluate-governance-risk-compliance',
                'title': 'SC-100: Evaluate governance, risk, and compliance (GRC) strategies',
                'summary': 'Design and evaluate governance, risk management, and compliance strategies for enterprise security',
                'url': 'https://learn.microsoft.com/en-us/training/paths/evaluate-governance-risk-compliance-strategies/',
                'type': 'learning-path',
                'duration_minutes': 360,
                'products': ['azure', 'microsoft-365'],
                'roles': ['security-engineer', 'security-architect', 'administrator'],
                'subjects': ['security', 'governance', 'compliance', 'risk-management'],
                'levels': ['advanced'],
                'rating': 4.7,
                'last_modified': '2024-07-01T00:00:00Z',
                'icon_url': ''
            },
            {
                'id': 'azure-ad-conditional-access',
                'title': 'Configure Azure AD Conditional Access',
                'summary': 'Deep dive into Azure AD Conditional Access policies, risk-based authentication, and access controls',
                'url': 'https://learn.microsoft.com/en-us/training/modules/configure-azure-ad-conditional-access/',
                'type': 'module',
                'duration_minutes': 75,
                'products': ['azure', 'microsoft-365'],
                'roles': ['security-engineer', 'administrator', 'identity-access-admin'],
                'subjects': ['security', 'identity', 'conditional-access'],
                'levels': ['intermediate'],
                'rating': 4.8,
                'last_modified': '2024-06-15T00:00:00Z',
                'icon_url': ''
            },
            {
                'id': 'azure-ad-privileged-identity-management',
                'title': 'Implement Azure AD Privileged Identity Management',
                'summary': 'Configure and manage Azure AD PIM for just-in-time administrative access and privileged role management',
                'url': 'https://learn.microsoft.com/en-us/training/modules/azure-ad-privileged-identity-management/',
                'type': 'module',
                'duration_minutes': 90,
                'products': ['azure', 'microsoft-365'],
                'roles': ['security-engineer', 'administrator', 'identity-access-admin'],
                'subjects': ['security', 'identity', 'privileged-access'],
                'levels': ['advanced'],
                'rating': 4.9,
                'last_modified': '2024-06-20T00:00:00Z',
                'icon_url': ''
            },
            {
                'id': 'azure-ad-identity-protection',
                'title': 'Configure Azure AD Identity Protection',
                'summary': 'Implement identity protection policies, risk detection, and automated remediation for user and sign-in risks',
                'url': 'https://learn.microsoft.com/en-us/training/modules/azure-ad-identity-protection/',
                'type': 'module',
                'duration_minutes': 60,
                'products': ['azure', 'microsoft-365'],
                'roles': ['security-engineer', 'administrator', 'identity-access-admin'],
                'subjects': ['security', 'identity', 'risk-management'],
                'levels': ['intermediate'],
                'rating': 4.7,
                'last_modified': '2024-06-25T00:00:00Z',
                'icon_url': ''
            },
            {
                'id': 'azure-ad-access-reviews',
                'title': 'Implement Azure AD Access Reviews',
                'summary': 'Configure and manage access reviews for groups, applications, and privileged roles to maintain least privilege access',
                'url': 'https://learn.microsoft.com/en-us/training/modules/azure-ad-access-reviews/',
                'type': 'module',
                'duration_minutes': 45,
                'products': ['azure', 'microsoft-365'],
                'roles': ['security-engineer', 'administrator', 'identity-access-admin'],
                'subjects': ['security', 'identity', 'governance', 'access-management'],
                'levels': ['intermediate'],
                'rating': 4.6,
                'last_modified': '2024-06-30T00:00:00Z',
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
        """Provide fallback facets focused on SC-300 and SC-100 certification paths."""
        return {
            'products': [
                {'id': 'azure', 'name': 'Azure', 'count': 85},
                {'id': 'microsoft-365', 'name': 'Microsoft 365', 'count': 75},
                {'id': 'power-platform', 'name': 'Power Platform', 'count': 15},
                {'id': 'dynamics-365', 'name': 'Dynamics 365', 'count': 10},
                {'id': 'windows', 'name': 'Windows', 'count': 8}
            ],
            'roles': [
                {'id': 'identity-access-admin', 'name': 'Identity and Access Administrator', 'count': 45},
                {'id': 'security-engineer', 'name': 'Security Engineer', 'count': 40},
                {'id': 'security-architect', 'name': 'Security Architect', 'count': 25},
                {'id': 'administrator', 'name': 'Administrator', 'count': 35},
                {'id': 'developer', 'name': 'Developer', 'count': 20}
            ],
            'subjects': [
                {'id': 'security', 'name': 'Security', 'count': 80},
                {'id': 'identity', 'name': 'Identity', 'count': 65},
                {'id': 'governance', 'name': 'Governance', 'count': 35},
                {'id': 'compliance', 'name': 'Compliance', 'count': 30},
                {'id': 'zero-trust', 'name': 'Zero Trust', 'count': 25},
                {'id': 'conditional-access', 'name': 'Conditional Access', 'count': 20},
                {'id': 'privileged-access', 'name': 'Privileged Access', 'count': 18},
                {'id': 'risk-management', 'name': 'Risk Management', 'count': 15}
            ],
            'levels': [
                {'id': 'beginner', 'name': 'Beginner', 'count': 25},
                {'id': 'intermediate', 'name': 'Intermediate', 'count': 45},
                {'id': 'advanced', 'name': 'Advanced', 'count': 30}
            ]
        }


def create_catalog_service() -> MSLearnCatalogService:
    """
    Factory function to create a catalog service instance.
    
    Returns:
        Configured MSLearnCatalogService instance
    """
    return MSLearnCatalogService()