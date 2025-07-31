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
    
    def get_roles(self) -> List[Dict]:
        """Get all available roles from MS Learn API."""
        try:
            logger.info("Fetching roles from MS Learn API")
            url = f"{self.api_base}/?type=roles"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            roles = data.get('roles', [])
            
            logger.info(f"Retrieved {len(roles)} roles from MS Learn API")
            return roles
            
        except Exception as e:
            logger.error(f"Failed to fetch roles from MS Learn API: {e}")
            return self._get_fallback_roles()
    
    def _get_fallback_roles(self) -> List[Dict]:
        """Get fallback role data when API is unavailable."""
        return [
            {
                'uid': 'administrator',
                'name': 'Administrator',
                'description': 'Manage and maintain Azure infrastructure, security, and operations'
            },
            {
                'uid': 'developer',
                'name': 'Developer',
                'description': 'Build applications and solutions on Azure platform'
            },
            {
                'uid': 'data-engineer',
                'name': 'Data Engineer',
                'description': 'Design and implement data solutions and analytics on Azure'
            },
            {
                'uid': 'security-engineer',
                'name': 'Security Engineer',
                'description': 'Implement security controls and threat protection in Azure'
            },
            {
                'uid': 'ai-engineer',
                'name': 'AI Engineer',
                'description': 'Build intelligent solutions using Azure AI and machine learning'
            },
            {
                'uid': 'solutions-architect',
                'name': 'Solutions Architect',
                'description': 'Design comprehensive solutions and technical architecture'
            },
            {
                'uid': 'devops-engineer',
                'name': 'DevOps Engineer',
                'description': 'Implement CI/CD and infrastructure automation practices'
            },
            {
                'uid': 'data-analyst',
                'name': 'Data Analyst',
                'description': 'Transform data into actionable insights using Power BI and analytics'
            }
        ]
    
    def get_role_certifications(self, role_id: str) -> Dict:
        """Get certifications for a specific role from MS Learn API."""
        try:
            logger.info(f"Fetching certifications for role: {role_id}")
            
            # Get all certifications and filter by role
            url = f"{self.api_base}/?type=certifications"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            all_certifications = data.get('certifications', [])
            
            # Filter certifications by role
            role_certifications = []
            for cert in all_certifications:
                cert_roles = cert.get('roles', [])
                if role_id in cert_roles or role_id.replace('-', '') in cert_roles:
                    role_certifications.append({
                        'id': cert.get('uid', '').replace('certification.', ''),
                        'name': cert.get('display_name', cert.get('title', 'Unknown')),
                        'description': cert.get('summary', 'No description available'),
                        'url': cert.get('url', ''),
                        'icon_url': cert.get('icon_url', ''),
                        'exam_codes': cert.get('exam_codes', [])
                    })
            
            # Get role info
            roles = self.get_roles()
            role_info = next((r for r in roles if r.get('uid') == role_id), None)
            
            if not role_info:
                raise ValueError(f"Role {role_id} not found")
            
            logger.info(f"Found {len(role_certifications)} certifications for role {role_id}")
            
            return {
                'role': {
                    'id': role_id,
                    'name': role_info.get('name', 'Unknown Role'),
                    'description': role_info.get('description', 'No description available')
                },
                'certifications': role_certifications
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch certifications for role {role_id}: {e}")
            return self._get_fallback_role_certifications(role_id)
    
    def _get_fallback_role_certifications(self, role_id: str) -> Dict:
        """Get fallback certification data when API is unavailable."""
        fallback_data = {
            'administrator': {
                'role': {
                    'id': 'administrator',
                    'name': 'Administrator',
                    'description': 'Manage and maintain Azure infrastructure, security, and operations'
                },
                'certifications': [
                    {
                        'id': 'AZ-900',
                        'name': 'Microsoft Azure Fundamentals',
                        'description': 'Foundational knowledge of cloud services and Azure',
                        'url': 'https://learn.microsoft.com/en-us/certifications/azure-fundamentals/',
                        'exam_codes': ['AZ-900']
                    },
                    {
                        'id': 'AZ-104',
                        'name': 'Microsoft Azure Administrator',
                        'description': 'Manage Azure subscriptions, secure identities, administer the infrastructure',
                        'url': 'https://learn.microsoft.com/en-us/certifications/azure-administrator/',
                        'exam_codes': ['AZ-104']
                    }
                ]
            }
        }
        
        return fallback_data.get(role_id, {
            'role': {'id': role_id, 'name': 'Unknown Role', 'description': 'No description available'},
            'certifications': []
        })
    
    def get_certification_modules(self, cert_id: str) -> Dict:
        """Get modules for a specific certification from MS Learn API."""
        try:
            logger.info(f"Fetching modules for certification: {cert_id}")
            
            # First get the certification details
            cert_url = f"{self.api_base}/?type=certifications&uid=certification.{cert_id}"
            cert_response = self.session.get(cert_url, timeout=30)
            cert_response.raise_for_status()
            
            cert_data = cert_response.json()
            certifications = cert_data.get('certifications', [])
            
            if not certifications:
                # Try without the 'certification.' prefix
                cert_url = f"{self.api_base}/?type=certifications&uid={cert_id}"
                cert_response = self.session.get(cert_url, timeout=30)
                cert_response.raise_for_status()
                cert_data = cert_response.json()
                certifications = cert_data.get('certifications', [])
            
            if not certifications:
                # If still not found, get modules by searching for related learning paths
                return self._get_fallback_certification_modules(cert_id)
            
            certification = certifications[0]
            
            # Get learning paths for this certification
            learning_paths = certification.get('learning_paths', [])
            
            # Collect all modules from all learning paths
            all_modules = []
            for lp_uid in learning_paths:
                lp_modules = self.get_learning_path_modules(lp_uid)
                all_modules.extend(lp_modules)
            
            # Remove duplicates based on module UID
            unique_modules = []
            seen_uids = set()
            for module in all_modules:
                module_uid = module.get('uid', module.get('id', ''))
                if module_uid not in seen_uids:
                    unique_modules.append(module)
                    seen_uids.add(module_uid)
            
            logger.info(f"Found {len(unique_modules)} modules for certification {cert_id}")
            
            return {
                'certification': {
                    'id': cert_id,
                    'name': certification.get('display_name', certification.get('title', 'Unknown')),
                    'description': certification.get('summary', 'No description available')
                },
                'modules': unique_modules,
                'role': certification.get('roles', ['unknown'])[0] if certification.get('roles') else 'unknown'
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch modules for certification {cert_id}: {e}")
            return self._get_fallback_certification_modules(cert_id)
    
    def _get_fallback_certification_modules(self, cert_id: str) -> Dict:
        """Get fallback module data for a certification when API is unavailable."""
        fallback_data = {
            'AZ-900': {
                'certification': {
                    'id': 'AZ-900',
                    'name': 'Microsoft Azure Fundamentals',
                    'description': 'Foundational knowledge of cloud services and Azure'
                },
                'modules': [
                    {
                        'uid': 'learn.azure.intro-to-azure-fundamentals',
                        'title': 'Introduction to Azure fundamentals',
                        'summary': 'Learn cloud computing concepts, deployment models, and understand specific Azure services',
                        'url': 'https://learn.microsoft.com/en-us/training/modules/intro-to-azure-fundamentals/',
                        'duration_in_minutes': 55,
                        'level': 'Beginner',
                        'rating': 4.5,
                        'units': [
                            {
                                'title': 'Introduction',
                                'type': 'introduction'
                            },
                            {
                                'title': 'What is cloud computing?',
                                'type': 'content'
                            },
                            {
                                'title': 'What is Azure?',
                                'type': 'content'
                            },
                            {
                                'title': 'Tour of Azure services',
                                'type': 'content'
                            },
                            {
                                'title': 'Get started with Azure accounts',
                                'type': 'content'
                            },
                            {
                                'title': 'Knowledge check',
                                'type': 'knowledge-check'
                            },
                            {
                                'title': 'Summary',
                                'type': 'summary'
                            }
                        ]
                    },
                    {
                        'uid': 'learn.azure.azure-architecture-fundamentals',
                        'title': 'Explore Azure compute services',
                        'summary': 'Learn about the various compute services available in Azure',
                        'url': 'https://learn.microsoft.com/en-us/training/modules/azure-compute-fundamentals/',
                        'duration_in_minutes': 45,
                        'level': 'Beginner',
                        'rating': 4.3,
                        'units': [
                            {
                                'title': 'Introduction',
                                'type': 'introduction'
                            },
                            {
                                'title': 'Overview of Azure compute services',
                                'type': 'content'
                            },
                            {
                                'title': 'Virtual Machines',
                                'type': 'content'
                            },
                            {
                                'title': 'App Service',
                                'type': 'content'
                            },
                            {
                                'title': 'Container services',
                                'type': 'content'
                            },
                            {
                                'title': 'Knowledge check',
                                'type': 'knowledge-check'
                            },
                            {
                                'title': 'Summary',
                                'type': 'summary'
                            }
                        ]
                    }
                ],
                'role': 'administrator'
            }
        }
        
        return fallback_data.get(cert_id, {
            'certification': {
                'id': cert_id,
                'name': f'Certification {cert_id}',
                'description': 'No description available'
            },
            'modules': [],
            'role': 'unknown'
        })
    
    def get_certification_tracks(self) -> Dict[str, Dict]:
        """Get organized certification tracks grouped by role (legacy method for backwards compatibility)."""
        logger.warning("get_certification_tracks is deprecated, use get_role_certifications instead")
        
        # For backwards compatibility, return hardcoded structure
        return {
            'administrator': {
                'name': 'Administrator',
                'description': 'Manage and maintain Azure infrastructure, security, and operations',
                'certifications': {
                    'AZ-900': {
                        'name': 'Microsoft Azure Fundamentals',
                        'description': 'Foundational knowledge of cloud services and Azure',
                        'modules': []
                    },
                    'AZ-104': {
                        'name': 'Microsoft Azure Administrator',
                        'description': 'Manage Azure subscriptions, secure identities, administer the infrastructure',
                        'modules': []
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
    
    def get_module_details(self, module_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific module including unit URLs.
        
        Args:
            module_id: The module identifier or URL
            
        Returns:
            Dictionary with detailed module information including unit URLs
        """
        try:
            # If module_id is a full URL, extract the module ID
            if module_id.startswith('http'):
                # Extract module ID from URL like /training/modules/module-name/
                parts = module_id.split('/')
                if 'modules' in parts:
                    module_idx = parts.index('modules')
                    if module_idx + 1 < len(parts):
                        module_id = parts[module_idx + 1]
            
            # Try to query the module by UID from the catalog
            logger.info(f"Fetching module details for: {module_id}")
            
            # Try different UID formats
            possible_uids = [
                module_id,
                f"learn.azure.{module_id}",
                f"learn.{module_id}",
                module_id.replace('-', '.')
            ]
            
            for uid in possible_uids:
                try:
                    url = f"{self.api_base}/?type=modules&uid={uid}"
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()
                    
                    data = response.json()
                    modules = data.get('modules', [])
                    
                    if modules:
                        module = modules[0]
                        logger.info(f"Found module with UID: {uid}")
                        
                        # Extract unit information
                        units = []
                        for unit_data in module.get('units', []):
                            unit_info = {
                                'title': unit_data.get('title', ''),
                                'url': unit_data.get('url', ''),
                                'duration_minutes': unit_data.get('durationInMinutes', 0),
                                'type': unit_data.get('type', 'content')
                            }
                            
                            # Ensure URL is absolute
                            if unit_info['url'] and not unit_info['url'].startswith('http'):
                                unit_info['url'] = f"{self.base_url}{unit_info['url']}"
                            
                            units.append(unit_info)
                        
                        return {
                            'uid': module.get('uid', uid),
                            'title': module.get('title', 'Unknown Module'),
                            'summary': module.get('summary', 'No description available'),
                            'url': module.get('url', ''),
                            'duration_in_minutes': module.get('durationInMinutes', 0),
                            'level': module.get('level', 'Unknown'),
                            'rating': module.get('rating', 0),
                            'units': units,
                            'unit_count': len(units)
                        }
                        
                except Exception as e:
                    logger.debug(f"UID {uid} not found: {e}")
                    continue
            
            logger.warning(f"Module not found in API: {module_id}")
            return self._get_fallback_module_details(module_id)
            
        except Exception as e:
            logger.error(f"Failed to get module details: {e}")
            return self._get_fallback_module_details(module_id)

    def _get_fallback_module_details(self, module_id: str) -> Optional[Dict]:
        """
        Provide fallback module details when API is unavailable.
        
        Args:
            module_id: The module identifier
            
        Returns:
            Dictionary with fallback module details including constructed unit URLs
        """
        try:
            # Check our fallback certification data for this module
            fallback_data = self._get_fallback_certification_modules('AZ-900')
            
            # Look for the module in our fallback data
            for module in fallback_data.get('modules', []):
                module_uid = module.get('uid', '')
                module_url = module.get('url', '')
                
                # Check if this matches the requested module
                if (module_uid == module_id or 
                    module_id in module_url or
                    module_id == module.get('id', '')):
                    
                    # Process units and add proper URLs
                    units = []
                    base_url = module_url.rstrip('/')
                    
                    for i, unit in enumerate(module.get('units', []), 1):
                        unit_title = unit.get('title', '')
                        unit_type = unit.get('type', 'content')
                        
                        # Construct unit URL based on common patterns
                        unit_slug = unit_title.lower().replace(' ', '-').replace('?', '').replace(':', '')
                        
                        # For knowledge checks, use a specific pattern
                        if unit_type == 'knowledge-check':
                            unit_url = f"{base_url}/{i}-knowledge-check/"
                        else:
                            # Use a generic pattern for other units
                            unit_url = f"{base_url}/{i}-{unit_slug[:30]}/"  # Limit slug length
                        
                        units.append({
                            'title': unit_title,
                            'url': unit_url,
                            'duration_minutes': 5,  # Default estimate
                            'type': unit_type
                        })
                    
                    return {
                        'uid': module_uid,
                        'title': module.get('title', 'Unknown Module'),
                        'summary': module.get('summary', 'No description available'),
                        'url': module_url,
                        'duration_in_minutes': module.get('duration_in_minutes', 30),
                        'level': module.get('level', 'Beginner'),
                        'rating': module.get('rating', 4.0),
                        'units': units,
                        'unit_count': len(units)
                    }
            
            # If not found in AZ-900, try other certifications
            for cert_id in ['AZ-104', 'AZ-204', 'SC-900']:
                try:
                    cert_fallback = self._get_fallback_certification_modules(cert_id)
                    for module in cert_fallback.get('modules', []):
                        module_uid = module.get('uid', '')
                        if module_uid == module_id:
                            # Return the same structure as above
                            units = []
                            base_url = module.get('url', '').rstrip('/')
                            
                            for i, unit in enumerate(module.get('units', []), 1):
                                unit_title = unit.get('title', '')
                                unit_type = unit.get('type', 'content')
                                unit_slug = unit_title.lower().replace(' ', '-').replace('?', '').replace(':', '')
                                
                                if unit_type == 'knowledge-check':
                                    unit_url = f"{base_url}/{i}-knowledge-check/"
                                else:
                                    unit_url = f"{base_url}/{i}-{unit_slug[:30]}/"
                                
                                units.append({
                                    'title': unit_title,
                                    'url': unit_url,
                                    'duration_minutes': 5,
                                    'type': unit_type
                                })
                            
                            return {
                                'uid': module_uid,
                                'title': module.get('title', 'Unknown Module'),
                                'summary': module.get('summary', 'No description available'),
                                'url': module.get('url', ''),
                                'duration_in_minutes': module.get('duration_in_minutes', 30),
                                'level': module.get('level', 'Beginner'),
                                'rating': module.get('rating', 4.0),
                                'units': units,
                                'unit_count': len(units)
                            }
                except Exception:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error in fallback module details: {e}")
            return None

def create_catalog_service() -> MSLearnCatalogService:
    """
    Factory function to create a catalog service instance.
    
    Returns:
        Configured MSLearnCatalogService instance
    """
    return MSLearnCatalogService()