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
            # FOR DEVELOPMENT: Always use fallback data for consistent experience
            # TODO: Re-enable API calls once MS Learn API is stable
            logger.info("Using fallback data for development")
            return self._get_fallback_results(query, content_type, product, role, topic)
            
            # Build query parameters (disabled for development)
            # params = {
            #     'locale': locale,
            #     'type': content_type,
            #     '$top': limit
            # }
            
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
            
            logger.info(f"Found {len(results['results'])} results from API")
            
            # If API returned no results, use fallback data for better user experience
            if len(results['results']) == 0:
                logger.info("API returned no results, using fallback data")
                return self._get_fallback_results(query, content_type, product, role, topic)
            
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
    
    def get_certification_tracks(self) -> Dict[str, Dict]:
        """Get organized certification tracks grouped by role."""
        logger.info("Retrieving certification tracks organized by role")
        
        return {
            'security_engineer': {
                'name': 'Security Engineer',
                'description': 'Design and implement security solutions',
                'certifications': {
                    'SC-100': {
                        'name': 'Microsoft Cybersecurity Architect',
                        'description': 'Design solutions that align with security best practices and priorities',
                        'modules': [
                            {
                                'id': 'security-governance-risk-compliance',
                                'title': 'Design governance Risk and Compliance strategies',
                                'url': 'https://learn.microsoft.com/en-us/training/modules/design-governance-risk-compliance-strategies/',
                                'duration': '45 min',
                                'level': 'Advanced'
                            },
                            {
                                'id': 'design-security-operations-strategy',
                                'title': 'Design security operations strategy',
                                'url': 'https://learn.microsoft.com/en-us/training/modules/design-security-operations-strategy/',
                                'duration': '50 min',
                                'level': 'Advanced'
                            }
                        ]
                    },
                    'SC-300': {
                        'name': 'Microsoft Identity and Access Administrator',
                        'description': 'Implement, configure, and manage identity and access management systems',
                        'modules': [
                            {
                                'id': 'explore-zero-trust-guiding-principles',
                                'title': 'Explore Zero Trust guiding principles',
                                'url': 'https://learn.microsoft.com/en-us/training/modules/explore-zero-trust-guiding-principles/',
                                'duration': '30 min',
                                'level': 'Intermediate'
                            },
                            {
                                'id': 'explore-authentication-capabilities',
                                'title': 'Explore authentication capabilities',
                                'url': 'https://learn.microsoft.com/en-us/training/modules/explore-authentication-capabilities/',
                                'duration': '35 min',
                                'level': 'Intermediate'
                            }
                        ]
                    }
                }
            },
            'azure_administrator': {
                'name': 'Azure Administrator',
                'description': 'Manage Azure subscriptions, secure identities, administer infrastructure',
                'certifications': {
                    'AZ-104': {
                        'name': 'Microsoft Azure Administrator',
                        'description': 'Implement, manage, and monitor identity, governance, storage, compute, and virtual networks',
                        'modules': [
                            {
                                'id': 'configure-subscriptions',
                                'title': 'Configure Azure subscriptions',
                                'url': 'https://learn.microsoft.com/en-us/training/modules/configure-subscriptions/',
                                'duration': '30 min',
                                'level': 'Intermediate'
                            },
                            {
                                'id': 'configure-azure-policy',
                                'title': 'Configure Azure Policy',
                                'url': 'https://learn.microsoft.com/en-us/training/modules/configure-azure-policy/',
                                'duration': '45 min',
                                'level': 'Intermediate'
                            }
                        ]
                    },
                    'AZ-900': {
                        'name': 'Microsoft Azure Fundamentals',
                        'description': 'Demonstrate foundational knowledge of cloud services and Azure',
                        'modules': [
                            {
                                'id': 'describe-cloud-computing',
                                'title': 'Describe cloud computing',
                                'url': 'https://learn.microsoft.com/en-us/training/modules/describe-cloud-computing/',
                                'duration': '25 min',
                                'level': 'Beginner'
                            },
                            {
                                'id': 'azure-architecture-services',
                                'title': 'Describe Azure architecture and services',
                                'url': 'https://learn.microsoft.com/en-us/training/modules/describe-azure-architecture-services/',
                                'duration': '40 min',
                                'level': 'Beginner'
                            }
                        ]
                    }
                }
            },
            'azure_developer': {
                'name': 'Azure Developer',
                'description': 'Design, build, test, and maintain cloud applications and services',
                'certifications': {
                    'AZ-204': {
                        'name': 'Developing Solutions for Microsoft Azure',
                        'description': 'Develop Azure compute solutions, storage, security, and monitoring',
                        'modules': [
                            {
                                'id': 'create-azure-app-service-web-apps',
                                'title': 'Create Azure App Service Web Apps',
                                'url': 'https://learn.microsoft.com/en-us/training/modules/create-azure-app-service-web-apps/',
                                'duration': '55 min',
                                'level': 'Intermediate'
                            },
                            {
                                'id': 'develop-solutions-blob-storage',
                                'title': 'Develop solutions that use Blob storage',
                                'url': 'https://learn.microsoft.com/en-us/training/modules/develop-solutions-blob-storage/',
                                'duration': '50 min',
                                'level': 'Intermediate'
                            }
                        ]
                    }
                }
            },
            'azure_solutions_architect': {
                'name': 'Azure Solutions Architect',
                'description': 'Design and implement solutions that run on Azure',
                'certifications': {
                    'AZ-305': {
                        'name': 'Designing Microsoft Azure Infrastructure Solutions',
                        'description': 'Design identity, governance, monitoring, data storage, business continuity, and infrastructure solutions',
                        'modules': [
                            {
                                'id': 'design-governance-solution',
                                'title': 'Design a governance solution',
                                'url': 'https://learn.microsoft.com/en-us/training/modules/design-governance-solution/',
                                'duration': '45 min',
                                'level': 'Advanced'
                            },
                            {
                                'id': 'design-authentication-authorization-solution',
                                'title': 'Design authentication and authorization solutions',
                                'url': 'https://learn.microsoft.com/en-us/training/modules/design-authentication-authorization-solutions/',
                                'duration': '55 min',
                                'level': 'Advanced'
                            }
                        ]
                    }
                }
            },
            'data_engineer': {
                'name': 'Data Engineer', 
                'description': 'Design and implement data solutions and data processing systems',
                'certifications': {
                    'DP-900': {
                        'name': 'Microsoft Azure Data Fundamentals',
                        'description': 'Demonstrate foundational knowledge of core data concepts and services',
                        'modules': [
                            {
                                'id': 'explore-core-data-concepts',
                                'title': 'Explore core data concepts',
                                'url': 'https://learn.microsoft.com/en-us/training/modules/explore-core-data-concepts/',
                                'duration': '35 min',
                                'level': 'Beginner'
                            },
                            {
                                'id': 'explore-relational-data-azure',
                                'title': 'Explore relational data in Azure',
                                'url': 'https://learn.microsoft.com/en-us/training/modules/explore-relational-data-azure/',
                                'duration': '40 min',
                                'level': 'Beginner'
                            }
                        ]
                    },
                    'DP-203': {
                        'name': 'Data Engineering on Microsoft Azure',
                        'description': 'Implement data storage solutions, manage and develop data processing, monitor and optimize data solutions',
                        'modules': [
                            {
                                'id': 'data-engineering-lakehouse-architecture',
                                'title': 'Introduction to data engineering on Azure',
                                'url': 'https://learn.microsoft.com/en-us/training/modules/introduction-to-data-engineering-azure/',
                                'duration': '45 min',
                                'level': 'Intermediate'
                            }
                        ]
                    }
                }
            },
            'power_platform_developer': {
                'name': 'Power Platform Developer',
                'description': 'Design and develop Power Platform solutions',
                'certifications': {
                    'PL-900': {
                        'name': 'Microsoft Power Platform Fundamentals',
                        'description': 'Demonstrate foundational knowledge of Power Platform components',
                        'modules': [
                            {
                                'id': 'introduction-power-platform',
                                'title': 'Introduction to Microsoft Power Platform',
                                'url': 'https://learn.microsoft.com/en-us/training/modules/introduction-power-platform/',
                                'duration': '30 min',
                                'level': 'Beginner'
                            },
                            {
                                'id': 'introduction-power-apps',
                                'title': 'Introduction to Power Apps',
                                'url': 'https://learn.microsoft.com/en-us/training/modules/introduction-power-apps/',
                                'duration': '35 min',
                                'level': 'Beginner'
                            }
                        ]
                    },
                    'PL-400': {
                        'name': 'Microsoft Power Platform Developer',
                        'description': 'Design, develop, secure, and troubleshoot Power Platform solutions',
                        'modules': [
                            {
                                'id': 'power-platform-architecture',
                                'title': 'Power Platform architecture',
                                'url': 'https://learn.microsoft.com/en-us/training/modules/power-platform-architecture/',
                                'duration': '50 min',
                                'level': 'Advanced'
                            }
                        ]
                    }
                }
            },
            'microsoft_365_administrator': {
                'name': 'Microsoft 365 Administrator',
                'description': 'Plan, deploy, configure, and manage Microsoft 365 services',
                'certifications': {
                    'MS-900': {
                        'name': 'Microsoft 365 Fundamentals',
                        'description': 'Demonstrate foundational knowledge of Microsoft 365 services',
                        'modules': [
                            {
                                'id': 'microsoft-365-productivity-teamwork-solutions',
                                'title': 'Describe Microsoft 365 productivity and teamwork solutions',
                                'url': 'https://learn.microsoft.com/en-us/training/modules/microsoft-365-productivity-teamwork-solutions/',
                                'duration': '40 min',
                                'level': 'Beginner'
                            }
                        ]
                    },
                    'MS-100': {
                        'name': 'Microsoft 365 Identity and Services',
                        'description': 'Design and implement Microsoft 365 services',
                        'modules': [
                            {
                                'id': 'plan-your-premises-infrastructure-microsoft-365',
                                'title': 'Plan your on-premises infrastructure for Microsoft 365',
                                'url': 'https://learn.microsoft.com/en-us/training/modules/plan-your-premises-infrastructure-microsoft-365/',
                                'duration': '45 min',
                                'level': 'Advanced'
                            }
                        ]
                    }
                }
            }
        }

    def _get_fallback_content(self) -> List[Dict]:
        """Provide fallback content when the Microsoft Learn API is unavailable."""
        logger.info("Using fallback content - comprehensive Microsoft certification catalog")
        
        # Get structured certification data
        cert_tracks = self.get_certification_tracks()
        
        # Flatten into module list for search compatibility
        modules = []
        for role_id, role_data in cert_tracks.items():
            for cert_id, cert_data in role_data['certifications'].items():
                for module in cert_data['modules']:
                    # Enhanced module data with certification context
                    enhanced_module = {
                        'uid': module['id'],
                        'title': module['title'],
                        'url': module['url'],
                        'summary': f"Part of {cert_data['name']} ({cert_id}) certification path. {cert_data['description']}",
                        'duration_in_minutes': int(module['duration'].split()[0]) if 'min' in module['duration'] else 45,
                        'rating': 4.5,
                        'icon_url': f"https://learn.microsoft.com/en-us/media/learn/certification/{cert_id.lower()}.svg",
                        'last_modified': '2024-07-15T10:00:00Z',
                        'locale': 'en-us',
                        'certification': cert_id,
                        'certification_name': cert_data['name'],
                        'role': role_data['name'],
                        'role_id': role_id,
                        'level': module['level'],
                        'products': self._get_products_for_role(role_id),
                        'roles': [role_data['name']],
                        'subjects': self._get_subjects_for_certification(cert_id)
                    }
                    modules.append(enhanced_module)
        
        return modules

    def _get_products_for_role(self, role_id: str) -> List[str]:
        """Get relevant products for a role."""
        role_products = {
            'security_engineer': ['Azure', 'Microsoft 365', 'Microsoft Entra ID'],
            'azure_administrator': ['Azure'],
            'azure_developer': ['Azure', 'Visual Studio'],
            'azure_solutions_architect': ['Azure'],
            'data_engineer': ['Azure', 'Power BI', 'SQL Server'],
            'power_platform_developer': ['Power Platform', 'Power Apps', 'Power Automate'],
            'microsoft_365_administrator': ['Microsoft 365', 'Microsoft Teams', 'SharePoint']
        }
        return role_products.get(role_id, ['Azure'])

    def _get_subjects_for_certification(self, cert_id: str) -> List[str]:
        """Get relevant subjects for a certification."""
        cert_subjects = {
            'SC-100': ['Security', 'Architecture', 'Governance'],
            'SC-300': ['Security', 'Identity', 'Access Management'],
            'AZ-104': ['Administration', 'Cloud', 'Infrastructure'],
            'AZ-900': ['Fundamentals', 'Cloud', 'Azure Basics'],
            'AZ-204': ['Development', 'Cloud', 'Applications'],
            'AZ-305': ['Architecture', 'Solutions Design', 'Infrastructure'],
            'DP-900': ['Data', 'Fundamentals', 'Analytics'],
            'DP-203': ['Data Engineering', 'Analytics', 'Storage'],
            'PL-900': ['Power Platform', 'Fundamentals', 'Low-code'],
            'PL-400': ['Power Platform', 'Development', 'Applications'],
            'MS-900': ['Microsoft 365', 'Fundamentals', 'Productivity'],
            'MS-100': ['Microsoft 365', 'Administration', 'Identity']
        }
        return cert_subjects.get(cert_id, ['General'])

        # Comprehensive catalog covering all major Microsoft certification paths
        return [
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
            },
            # Azure Fundamentals (AZ-900)
            {
                'id': 'az-900-cloud-concepts',
                'title': 'AZ-900: Describe cloud concepts',
                'summary': 'Learn fundamental cloud concepts including high availability, scalability, and cloud service types',
                'url': 'https://learn.microsoft.com/en-us/training/paths/microsoft-azure-fundamentals-describe-cloud-concepts/',
                'type': 'learning-path',
                'duration_minutes': 180,
                'products': ['azure'],
                'roles': ['administrator', 'developer', 'engineer'],
                'subjects': ['cloud', 'fundamentals'],
                'levels': ['beginner'],
                'rating': 4.8,
                'last_modified': '2024-07-15T00:00:00Z',
                'icon_url': ''
            },
            {
                'id': 'az-900-azure-architecture',
                'title': 'AZ-900: Describe Azure architecture and services',
                'summary': 'Explore core Azure architectural components and services including compute, networking, and storage',
                'url': 'https://learn.microsoft.com/en-us/training/paths/azure-fundamentals-describe-azure-architecture-services/',
                'type': 'learning-path',
                'duration_minutes': 240,
                'products': ['azure'],
                'roles': ['administrator', 'developer', 'engineer'],
                'subjects': ['cloud', 'fundamentals', 'architecture'],
                'levels': ['beginner'],
                'rating': 4.7,
                'last_modified': '2024-07-10T00:00:00Z',
                'icon_url': ''
            },
            # Azure Administrator (AZ-104)
            {
                'id': 'az-104-manage-identities-governance',
                'title': 'AZ-104: Manage Azure identities and governance',
                'summary': 'Configure Azure AD, implement governance solutions, and manage subscriptions and resources',
                'url': 'https://learn.microsoft.com/en-us/training/paths/az-104-manage-identities-governance/',
                'type': 'learning-path',
                'duration_minutes': 360,
                'products': ['azure'],
                'roles': ['administrator'],
                'subjects': ['identity', 'governance', 'administration'],
                'levels': ['intermediate'],
                'rating': 4.6,
                'last_modified': '2024-07-05T00:00:00Z',
                'icon_url': ''
            },
            {
                'id': 'az-104-implement-manage-storage',
                'title': 'AZ-104: Implement and manage storage',
                'summary': 'Configure storage accounts, implement Azure Files, and manage data protection and backup',
                'url': 'https://learn.microsoft.com/en-us/training/paths/az-104-manage-storage/',
                'type': 'learning-path',
                'duration_minutes': 300,
                'products': ['azure'],
                'roles': ['administrator'],
                'subjects': ['storage', 'data-management', 'backup'],
                'levels': ['intermediate'],
                'rating': 4.5,
                'last_modified': '2024-07-01T00:00:00Z',
                'icon_url': ''
            },
            # Azure Developer (AZ-204)
            {
                'id': 'az-204-develop-azure-compute-solutions',
                'title': 'AZ-204: Develop Azure compute solutions',
                'summary': 'Implement solutions using Azure App Service, Azure Functions, and containerized solutions',
                'url': 'https://learn.microsoft.com/en-us/training/paths/create-azure-app-service-web-apps/',
                'type': 'learning-path',
                'duration_minutes': 420,
                'products': ['azure'],
                'roles': ['developer'],
                'subjects': ['development', 'compute', 'containers'],
                'levels': ['intermediate'],
                'rating': 4.7,
                'last_modified': '2024-06-28T00:00:00Z',
                'icon_url': ''
            },
            {
                'id': 'az-204-develop-for-azure-storage',
                'title': 'AZ-204: Develop for Azure storage',
                'summary': 'Implement solutions that use Cosmos DB, blob storage, and Azure SQL Database',
                'url': 'https://learn.microsoft.com/en-us/training/paths/develop-for-azure-storage/',
                'type': 'learning-path',
                'duration_minutes': 360,
                'products': ['azure'],
                'roles': ['developer'],
                'subjects': ['development', 'storage', 'data'],
                'levels': ['intermediate'],
                'rating': 4.6,
                'last_modified': '2024-06-25T00:00:00Z',
                'icon_url': ''
            },
            # Azure Solutions Architect (AZ-305)
            {
                'id': 'az-305-design-identity-governance-monitoring',
                'title': 'AZ-305: Design identity, governance, and monitoring solutions',
                'summary': 'Design authentication, authorization, governance, and monitoring solutions for Azure',
                'url': 'https://learn.microsoft.com/en-us/training/paths/design-identity-governance-monitor-solutions/',
                'type': 'learning-path',
                'duration_minutes': 480,
                'products': ['azure'],
                'roles': ['solution-architect'],
                'subjects': ['architecture', 'identity', 'governance', 'monitoring'],
                'levels': ['advanced'],
                'rating': 4.8,
                'last_modified': '2024-07-12T00:00:00Z',
                'icon_url': ''
            },
            {
                'id': 'az-305-design-business-continuity-solutions',
                'title': 'AZ-305: Design business continuity solutions',
                'summary': 'Design backup, disaster recovery, and high availability solutions for Azure workloads',
                'url': 'https://learn.microsoft.com/en-us/training/paths/design-business-continuity-solutions/',
                'type': 'learning-path',
                'duration_minutes': 360,
                'products': ['azure'],
                'roles': ['solution-architect'],
                'subjects': ['architecture', 'backup', 'disaster-recovery', 'availability'],
                'levels': ['advanced'],
                'rating': 4.7,
                'last_modified': '2024-07-08T00:00:00Z',
                'icon_url': ''
            },
            # Microsoft 365 Fundamentals (MS-900)
            {
                'id': 'ms-900-microsoft-365-fundamentals',
                'title': 'MS-900: Microsoft 365 fundamentals',
                'summary': 'Learn about Microsoft 365 services, security, compliance, privacy, and pricing',
                'url': 'https://learn.microsoft.com/en-us/training/paths/m365-fundamentals/',
                'type': 'learning-path',
                'duration_minutes': 300,
                'products': ['microsoft-365'],
                'roles': ['administrator', 'developer'],
                'subjects': ['fundamentals', 'productivity', 'collaboration'],
                'levels': ['beginner'],
                'rating': 4.6,
                'last_modified': '2024-07-03T00:00:00Z',
                'icon_url': ''
            },
            # Microsoft 365 Administrator (MS-102)
            {
                'id': 'ms-102-deploy-manage-microsoft-365-tenant',
                'title': 'MS-102: Deploy and manage a Microsoft 365 tenant',
                'summary': 'Configure and manage Microsoft 365 tenant settings, domains, and organizational settings',
                'url': 'https://learn.microsoft.com/en-us/training/paths/deploy-manage-microsoft-365-tenant/',
                'type': 'learning-path',
                'duration_minutes': 420,
                'products': ['microsoft-365'],
                'roles': ['administrator'],
                'subjects': ['administration', 'tenant-management', 'collaboration'],
                'levels': ['intermediate'],
                'rating': 4.5,
                'last_modified': '2024-06-30T00:00:00Z',
                'icon_url': ''
            },
            # Power Platform Fundamentals (PL-900)
            {
                'id': 'pl-900-power-platform-fundamentals',
                'title': 'PL-900: Microsoft Power Platform fundamentals',
                'summary': 'Learn about Power Apps, Power Automate, Power BI, and Power Virtual Agents capabilities',
                'url': 'https://learn.microsoft.com/en-us/training/paths/power-plat-fundamentals/',
                'type': 'learning-path',
                'duration_minutes': 240,
                'products': ['power-platform'],
                'roles': ['business-analyst', 'developer', 'administrator'],
                'subjects': ['fundamentals', 'low-code', 'automation', 'analytics'],
                'levels': ['beginner'],
                'rating': 4.7,
                'last_modified': '2024-07-01T00:00:00Z',
                'icon_url': ''
            },
            # Power Apps Developer (PL-400)
            {
                'id': 'pl-400-create-technical-designs',
                'title': 'PL-400: Create technical designs for Power Platform solutions',
                'summary': 'Design and implement complex Power Platform solutions using advanced development techniques',
                'url': 'https://learn.microsoft.com/en-us/training/paths/create-technical-designs-power-platform/',
                'type': 'learning-path',
                'duration_minutes': 360,
                'products': ['power-platform'],
                'roles': ['developer'],
                'subjects': ['development', 'low-code', 'solution-architecture'],
                'levels': ['advanced'],
                'rating': 4.6,
                'last_modified': '2024-06-28T00:00:00Z',
                'icon_url': ''
            },
            # Azure AI Fundamentals (AI-900)
            {
                'id': 'ai-900-artificial-intelligence-fundamentals',
                'title': 'AI-900: Artificial Intelligence fundamentals',
                'summary': 'Learn AI concepts, Azure AI services, and responsible AI practices',
                'url': 'https://learn.microsoft.com/en-us/training/paths/get-started-with-artificial-intelligence-on-azure/',
                'type': 'learning-path',
                'duration_minutes': 180,
                'products': ['azure'],
                'roles': ['ai-engineer', 'developer', 'data-scientist'],
                'subjects': ['artificial-intelligence', 'machine-learning', 'fundamentals'],
                'levels': ['beginner'],
                'rating': 4.8,
                'last_modified': '2024-07-10T00:00:00Z',
                'icon_url': ''
            },
            # Azure AI Engineer (AI-102)
            {
                'id': 'ai-102-design-implement-ai-solution',
                'title': 'AI-102: Design and implement an Azure AI solution',
                'summary': 'Build AI solutions using Azure Cognitive Services, Azure OpenAI, and Azure Machine Learning',
                'url': 'https://learn.microsoft.com/en-us/training/paths/design-implement-azure-ai-solution/',
                'type': 'learning-path',
                'duration_minutes': 480,
                'products': ['azure'],
                'roles': ['ai-engineer'],
                'subjects': ['artificial-intelligence', 'cognitive-services', 'machine-learning'],
                'levels': ['intermediate'],
                'rating': 4.7,
                'last_modified': '2024-07-05T00:00:00Z',
                'icon_url': ''
            },
            # Data Fundamentals (DP-900)
            {
                'id': 'dp-900-azure-data-fundamentals',
                'title': 'DP-900: Azure Data fundamentals',
                'summary': 'Learn core data concepts and Azure data services including databases, analytics, and data processing',
                'url': 'https://learn.microsoft.com/en-us/training/paths/azure-data-fundamentals-explore-core-data-concepts/',
                'type': 'learning-path',
                'duration_minutes': 240,
                'products': ['azure'],
                'roles': ['data-engineer', 'data-analyst', 'data-scientist'],
                'subjects': ['data', 'fundamentals', 'analytics', 'databases'],
                'levels': ['beginner'],
                'rating': 4.6,
                'last_modified': '2024-07-02T00:00:00Z',
                'icon_url': ''
            },
            # Azure Data Engineer (DP-203)
            {
                'id': 'dp-203-design-implement-data-storage',
                'title': 'DP-203: Design and implement data storage',
                'summary': 'Design and implement data storage solutions using Azure Data Lake, Azure Synapse, and Azure SQL',
                'url': 'https://learn.microsoft.com/en-us/training/paths/design-implement-data-storage-azure/',
                'type': 'learning-path',
                'duration_minutes': 420,
                'products': ['azure'],
                'roles': ['data-engineer'],
                'subjects': ['data-engineering', 'storage', 'analytics', 'big-data'],
                'levels': ['intermediate'],
                'rating': 4.5,
                'last_modified': '2024-06-25T00:00:00Z',
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
                title_match = query_lower in module['title'].lower()
                summary_match = query_lower in module['summary'].lower()
                subjects_match = any(query_lower in subject.lower() for subject in module['subjects'])
                products_match = any(query_lower in product.lower() for product in module['products'])
                roles_match = any(query_lower in role.lower() for role in module['roles'])
                
                if not (title_match or summary_match or subjects_match or products_match or roles_match):
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
        """Provide comprehensive fallback facets covering all major Microsoft certification paths."""
        return {
            'products': [
                {'id': 'azure', 'name': 'Azure', 'count': 180},
                {'id': 'microsoft-365', 'name': 'Microsoft 365', 'count': 95},
                {'id': 'power-platform', 'name': 'Power Platform', 'count': 45},
                {'id': 'dynamics-365', 'name': 'Dynamics 365', 'count': 35},
                {'id': 'windows', 'name': 'Windows', 'count': 25},
                {'id': 'sql-server', 'name': 'SQL Server', 'count': 20},
                {'id': 'teams', 'name': 'Microsoft Teams', 'count': 18}
            ],
            'roles': [
                {'id': 'administrator', 'name': 'Administrator', 'count': 95},
                {'id': 'developer', 'name': 'Developer', 'count': 80},
                {'id': 'engineer', 'name': 'Engineer', 'count': 65},
                {'id': 'solution-architect', 'name': 'Solutions Architect', 'count': 45},
                {'id': 'security-engineer', 'name': 'Security Engineer', 'count': 40},
                {'id': 'data-engineer', 'name': 'Data Engineer', 'count': 35},
                {'id': 'ai-engineer', 'name': 'AI Engineer', 'count': 30},
                {'id': 'identity-access-admin', 'name': 'Identity and Access Administrator', 'count': 25},
                {'id': 'data-analyst', 'name': 'Data Analyst', 'count': 22},
                {'id': 'data-scientist', 'name': 'Data Scientist', 'count': 18},
                {'id': 'business-analyst', 'name': 'Business Analyst', 'count': 15},
                {'id': 'security-architect', 'name': 'Security Architect', 'count': 12}
            ],
            'subjects': [
                {'id': 'fundamentals', 'name': 'Fundamentals', 'count': 85},
                {'id': 'cloud', 'name': 'Cloud Computing', 'count': 75},
                {'id': 'security', 'name': 'Security', 'count': 65},
                {'id': 'development', 'name': 'Development', 'count': 60},
                {'id': 'administration', 'name': 'Administration', 'count': 55},
                {'id': 'architecture', 'name': 'Architecture', 'count': 45},
                {'id': 'data', 'name': 'Data', 'count': 42},
                {'id': 'artificial-intelligence', 'name': 'Artificial Intelligence', 'count': 38},
                {'id': 'analytics', 'name': 'Analytics', 'count': 35},
                {'id': 'identity', 'name': 'Identity', 'count': 32},
                {'id': 'automation', 'name': 'Automation', 'count': 30},
                {'id': 'low-code', 'name': 'Low-code/No-code', 'count': 28},
                {'id': 'governance', 'name': 'Governance', 'count': 25},
                {'id': 'collaboration', 'name': 'Collaboration', 'count': 22},
                {'id': 'productivity', 'name': 'Productivity', 'count': 20},
                {'id': 'machine-learning', 'name': 'Machine Learning', 'count': 18},
                {'id': 'storage', 'name': 'Storage', 'count': 15},
                {'id': 'compliance', 'name': 'Compliance', 'count': 12}
            ],
            'levels': [
                {'id': 'beginner', 'name': 'Beginner', 'count': 120},
                {'id': 'intermediate', 'name': 'Intermediate', 'count': 180},
                {'id': 'advanced', 'name': 'Advanced', 'count': 95}
            ]
        }


def create_catalog_service() -> MSLearnCatalogService:
    """
    Factory function to create a catalog service instance.
    
    Returns:
        Configured MSLearnCatalogService instance
    """
    return MSLearnCatalogService()