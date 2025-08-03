#!/usr/bin/env python3
"""
Clean, simplified MS Learn Catalog Service.

This is the new service layer designed for stability and maintainability:
- Live MS Learn API data with smart fallbacks
- Auto-discovery for scalable certification coverage
- Simple, predictable methods
- Graceful error handling
- Pattern-based mapping for all Microsoft certifications
"""

import requests
import logging
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class Role:
    """Clean role data structure."""
    uid: str
    name: str
    description: str
    certification_count: int = 0

@dataclass
class Certification:
    """Clean certification data structure."""
    uid: str
    name: str
    description: str
    level: str
    module_count: int = 0
    exam_codes: list = None  # List of exam codes like ['AZ-500', 'SC-300']
    questionable_role_association: bool = False  # True if role association seems incorrect
    role_association_explanation: str = ''  # Explanation of why association is questionable
    
    def __post_init__(self):
        if self.exam_codes is None:
            self.exam_codes = []

@dataclass
class Module:
    """Clean module data structure."""
    uid: str
    title: str
    summary: str
    url: str
    duration_minutes: int
    level: str
    unit_count: int = 0

@dataclass
class Unit:
    """Clean unit data structure."""
    title: str
    url: str = ""
    type: str = "content"  # 'content', 'knowledge-check', 'summary', etc.
    duration_minutes: int = 5

@dataclass
class ModuleDetails:
    """Complete module information including units."""
    uid: str
    title: str
    summary: str
    url: str
    duration_minutes: int
    level: str
    rating: float
    units: List[Unit]

@dataclass
class CertificationConfig:
    """Configuration for API-driven certification discovery."""
    exam_codes: List[str]  # e.g., ['SC-300']
    learning_path_patterns: List[str]  # Regex patterns for auto-discovery
    priority: int = 1  # 1=High, 2=Medium, 3=Low
    manual_learning_paths: List[str] = None  # Fallback UIDs if needed

class MSLearnAPIService:
    """Service for fetching live data from Microsoft Learn API."""
    
    def __init__(self, cache_hours: int = 12):
        self.base_url = "https://docs.microsoft.com/api/learn/catalog"
        self.cache_duration = timedelta(hours=cache_hours)
        
        # Certification configurations for auto-discovery
        self.cert_configs = {
            # Phase 1: High Priority Security & Identity
            'certification.identity-and-access-administrator': CertificationConfig(
                exam_codes=['SC-300'],
                learning_path_patterns=[r'SC-300:.*'],
                priority=1
            ),
            'certification.security-compliance-and-identity-fundamentals': CertificationConfig(
                exam_codes=['SC-900'],
                learning_path_patterns=[r'SC-900:.*'],
                priority=1
            ),
            'certification.cybersecurity-architect-expert': CertificationConfig(
                exam_codes=['SC-100'],
                learning_path_patterns=[r'SC-100:.*'],
                priority=1
            ),
            'certification.azure-security-engineer': CertificationConfig(
                exam_codes=['AZ-500'],
                learning_path_patterns=[r'AZ-500:.*'],
                priority=1
            ),
            'certification.security-operations-analyst': CertificationConfig(
                exam_codes=['SC-200'],
                learning_path_patterns=[r'SC-200:.*'],
                priority=1
            ),
            
            # Phase 2: Azure Core
            'certification.azure-administrator': CertificationConfig(
                exam_codes=['AZ-104'],
                learning_path_patterns=[r'AZ-104:.*'],
                priority=1
            ),
            'certification.azure-solutions-architect-expert': CertificationConfig(
                exam_codes=['AZ-305'],
                learning_path_patterns=[r'AZ-305:.*'],
                priority=2
            ),
            'certification.azure-developer': CertificationConfig(
                exam_codes=['AZ-204'],
                learning_path_patterns=[r'AZ-204:.*', r'.*azure.*developer.*', r'.*developing.*azure.*'],
                priority=2
            ),
            
            # Phase 3: AI & Data
            'certification.azure-ai-engineer': CertificationConfig(
                exam_codes=['AI-102'],
                learning_path_patterns=[r'AI-102:.*', r'.*azure.*ai.*engineer.*', r'.*cognitive.*services.*'],
                priority=2
            ),
            'certification.azure-data-engineer': CertificationConfig(
                exam_codes=['DP-203'],
                learning_path_patterns=[r'DP-203:.*', r'.*azure.*data.*engineer.*', r'.*data.*engineering.*azure.*'],
                priority=2
            ),
            
            # Phase 4: Additional Certifications
            'certification.azure-fundamentals': CertificationConfig(
                exam_codes=['AZ-900'],
                learning_path_patterns=[r'AZ-900:.*', r'.*azure.*fundamentals.*'],
                priority=1
            ),
            'certification.azure-devops-engineer': CertificationConfig(
                exam_codes=['AZ-400'],
                learning_path_patterns=[r'AZ-400:.*', r'.*devops.*engineer.*'],
                priority=2
            ),
            'certification.azure-data-scientist': CertificationConfig(
                exam_codes=['DP-100'],
                learning_path_patterns=[r'DP-100:.*', r'.*data.*scientist.*'],
                priority=2
            ),
            'certification.power-platform-developer': CertificationConfig(
                exam_codes=['PL-400'],
                learning_path_patterns=[r'PL-400:.*', r'.*power.*platform.*developer.*'],
                priority=3
            ),
            'certification.power-platform-functional-consultant': CertificationConfig(
                exam_codes=['PL-200'],
                learning_path_patterns=[r'PL-200:.*', r'.*power.*platform.*functional.*'],
                priority=3
            ),
            'certification.microsoft-365-administrator': CertificationConfig(
                exam_codes=['MS-102'],
                learning_path_patterns=[r'MS-102:.*', r'.*microsoft.*365.*administrator.*'],
                priority=3
            )
        }
        
        # Cache for API responses
        self._learning_paths_cache = None
        self._cache_timestamp = None
    
    def _fetch_learning_paths(self) -> List[Dict]:
        """Fetch and cache learning paths from MS Learn API."""
        
        # Check cache validity
        if (self._learning_paths_cache and self._cache_timestamp and 
            datetime.now() - self._cache_timestamp < self.cache_duration):
            return self._learning_paths_cache
        
        try:
            logger.info("Fetching fresh learning paths from MS Learn API")
            response = requests.get(f"{self.base_url}/?type=learningPaths", timeout=30)
            response.raise_for_status()
            
            data = response.json()
            learning_paths = data.get('learningPaths', [])
            
            # Update cache
            self._learning_paths_cache = learning_paths
            self._cache_timestamp = datetime.now()
            
            logger.info(f"✓ Cached {len(learning_paths)} learning paths")
            return learning_paths
            
        except Exception as e:
            logger.error(f"Failed to fetch learning paths from API: {e}")
            return self._learning_paths_cache or []
    
    def get_modules_for_certification(self, cert_uid: str) -> List[Module]:
        """Get modules for a certification using auto-discovery."""
        
        config = self.cert_configs.get(cert_uid)
        if not config:
            logger.info(f"No API config for certification: {cert_uid}, using curated fallback")
            return []
        
        logger.info(f"Fetching API modules for {config.exam_codes}")
        
        # Fetch all learning paths
        all_paths = self._fetch_learning_paths()
        if not all_paths:
            logger.warning("No learning paths available from API")
            return []
        
        # Auto-discover learning paths using patterns
        matched_paths = []
        for path in all_paths:
            title = path.get('title', '')
            summary = path.get('summary', '')
            
            # Check each pattern
            for pattern in config.learning_path_patterns:
                if (re.search(pattern, title, re.IGNORECASE) or 
                    re.search(pattern, summary, re.IGNORECASE)):
                    matched_paths.append(path)
                    logger.info(f"✓ Matched learning path: {title}")
                    break
        
        # Add manual fallbacks if needed
        if config.manual_learning_paths:
            for manual_uid in config.manual_learning_paths:
                manual_path = next((p for p in all_paths if p.get('uid') == manual_uid), None)
                if manual_path and manual_path not in matched_paths:
                    matched_paths.append(manual_path)
                    logger.info(f"✓ Manual learning path: {manual_path.get('title')}")
        
        # Extract modules and convert to our format
        modules = []
        module_uids = []
        
        # First, collect all module UIDs from matched learning paths
        for path in matched_paths:
            path_modules = path.get('modules', [])
            for module_ref in path_modules:
                if isinstance(module_ref, str):
                    # Module is stored as UID string
                    module_uids.append(module_ref)
                elif isinstance(module_ref, dict):
                    # Module is stored as full object (rare case)
                    module_uids.append(module_ref.get('uid', ''))
            
            logger.info(f"  + {len(path_modules)} module UIDs from: {path.get('title')}")
        
        # Remove duplicates
        unique_module_uids = list(set(module_uids))
        logger.info(f"Found {len(unique_module_uids)} unique module UIDs")
        
        # Now fetch full module details for each UID
        if unique_module_uids:
            modules = self._fetch_modules_by_uids(unique_module_uids)
        
        logger.info(f"Total API modules: {len(modules)} for {config.exam_codes}")
        return modules
    
    def _fetch_modules_by_uids(self, module_uids: List[str]) -> List[Module]:
        """Fetch full module details for a list of module UIDs."""
        
        modules = []
        
        try:
            # Fetch all modules in one API call
            url = f"{self.base_url}/?type=modules"
            response = requests.get(url, timeout=60)  # Longer timeout for large response
            response.raise_for_status()
            
            data = response.json()
            all_modules = data.get('modules', [])
            
            # Create a lookup dict for faster searching
            module_lookup = {mod.get('uid'): mod for mod in all_modules if mod.get('uid')}
            
            # Convert UIDs to Module objects
            for module_uid in module_uids:
                module_data = module_lookup.get(module_uid)
                if module_data:
                    try:
                        module = Module(
                            uid=module_data.get('uid', ''),
                            title=module_data.get('title', ''),
                            summary=module_data.get('summary', ''),
                            url=module_data.get('url', ''),
                            duration_minutes=module_data.get('duration_in_minutes', 0),  # Fixed field name
                            level=module_data.get('levels', ['Beginner'])[0] if module_data.get('levels') else 'Beginner',
                            unit_count=len(module_data.get('units', []))  # Count actual units
                        )
                        modules.append(module)
                    except Exception as e:
                        logger.warning(f"Failed to parse module {module_uid}: {e}")
                        continue
                else:
                    logger.warning(f"Module UID not found in API: {module_uid}")
            
            logger.info(f"Successfully converted {len(modules)} module UIDs to full Module objects")
            
        except Exception as e:
            logger.error(f"Failed to fetch modules by UIDs: {e}")
        
        return modules

class CleanCatalogService:
    """
    Enhanced catalog service with live API integration and smart fallbacks.
    
    Design principles:
    - Live API data first, curated fallbacks second
    - Auto-discovery for scalable certification coverage  
    - Smart caching for performance
    - Pattern-based mapping for Microsoft certifications
    - Graceful error handling with fallback content
    """
    
    def __init__(self):
        self.api_base = "https://docs.microsoft.com/api/learn/catalog"
        self.base_url = "https://docs.microsoft.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'EdutainmentForge/1.0 (Educational Content Generator)'
        })
        
        # Initialize API service for live data
        self.api_service = MSLearnAPIService(cache_hours=12)
        
        # Simple in-memory cache (1 hour TTL)
        self._cache = {}
        self._cache_ttl = {}
        self._cache_duration = timedelta(hours=1)
    
    def _get_cached_or_fetch(self, cache_key: str, fetch_func) -> any:
        """Simple caching mechanism."""
        now = datetime.now()
        
        # Check if we have valid cached data
        if (cache_key in self._cache and 
            cache_key in self._cache_ttl and 
            now < self._cache_ttl[cache_key]):
            logger.info(f"Using cached data for {cache_key}")
            return self._cache[cache_key]
        
        # Fetch fresh data
        try:
            data = fetch_func()
            self._cache[cache_key] = data
            self._cache_ttl[cache_key] = now + self._cache_duration
            return data
        except Exception as e:
            # If fetch fails but we have old cached data, use it
            if cache_key in self._cache:
                logger.warning(f"API failed, using stale cache for {cache_key}: {e}")
                return self._cache[cache_key]
            raise
    
    def get_available_roles(self) -> List[Role]:
        """
        Get curated list of roles that we have ready content for.
        
        Returns:
            List of Role objects for the roles we want to showcase
        """
        def fetch_roles():
            logger.info("Building curated roles list")
            
            # CURATED ROLES: Only show roles we have excellent content for
            curated_roles = [
                {
                    'id': 'security-engineer',
                    'name': 'Security Engineer',
                    'description': 'Implement and manage security controls, threat protection, and compliance across Azure environments',
                    'expected_certs': 5  # SC-300, AZ-500, SC-200, SC-900, SC-100
                },
                {
                    'id': 'ai-engineer', 
                    'name': 'AI Engineer',
                    'description': 'Build and deploy AI solutions using Azure AI services and machine learning platforms',
                    'expected_certs': 1  # AI-102
                },
                {
                    'id': 'solution-architect',
                    'name': 'Solution Architect', 
                    'description': 'Design comprehensive Azure solutions and guide technical implementation strategies',
                    'expected_certs': 2  # AZ-305 (both associate and expert)
                },
                {
                    'id': 'administrator',
                    'name': 'Azure Administrator',
                    'description': 'Manage Azure infrastructure, core services, and fundamental cloud operations',
                    'expected_certs': 2  # AZ-900, AZ-800/801
                },
                {
                    'id': 'security-operations-analyst',
                    'name': 'Security Operations Analyst',
                    'description': 'Monitor, investigate, and respond to security threats and incidents in real-time',
                    'expected_certs': 1  # SC-200
                }
            ]
            
            # Get all certifications to count them per role
            cert_url = f"{self.api_base}/?type=certifications"
            cert_response = self.session.get(cert_url, timeout=30)
            cert_response.raise_for_status()
            cert_data = cert_response.json()
            certifications = cert_data.get('certifications', [])
            
            # Count actual ready certifications per role
            role_cert_counts = {}
            for cert in certifications:
                cert_roles = cert.get('roles', [])
                title = cert.get('title', '')
                cert_uid = cert.get('uid', '')
                
                # Only count if not retired AND ready for testing
                if not self._is_certification_retired(cert, title) and self._is_certification_ready(cert_uid):
                    for role_id in cert_roles:
                        role_cert_counts[role_id] = role_cert_counts.get(role_id, 0) + 1
            
            # Build our curated roles list
            roles = []
            for role_config in curated_roles:
                role_id = role_config['id']
                actual_cert_count = role_cert_counts.get(role_id, 0)
                
                role = Role(
                    uid=role_id,
                    name=role_config['name'],
                    description=role_config['description'],
                    certification_count=actual_cert_count
                )
                roles.append(role)
                
                logger.info(f"Added curated role: {role_config['name']} ({actual_cert_count} ready certifications)")
            
            logger.info(f"Built {len(roles)} curated roles with ready content")
            return roles
        
        try:
            return self._get_cached_or_fetch('curated_roles', fetch_roles)
        except Exception as e:
            logger.error(f"Failed to build curated roles: {e}")
            return []  # Return empty list, don't crash
    
    def _get_enhanced_role_description(self, role_name: str, role_id: str) -> str:
        """Get enhanced, helpful descriptions for roles."""
        
        # Create a mapping of role descriptions
        role_descriptions = {
            'administrator': 'Manage and maintain Azure infrastructure, security, and operations (includes Azure Fundamentals and Windows Server)',
            'ai-engineer': 'Build and deploy AI solutions using Azure AI services and machine learning',
            'ai-edge-engineer': 'Develop AI solutions that run on edge devices and IoT systems (emerging field)',
            'security-engineer': 'Implement and manage security controls, threat protection, and compliance',
            'solution-architect': 'Design comprehensive Azure solutions and guide technical implementation',
            'developer': 'Build applications and solutions on Azure platform using modern development practices',
            'data-engineer': 'Design and implement data solutions, pipelines, and analytics on Azure',
            'data-analyst': 'Analyze data and create insights using Power BI and Azure analytics services',
            'data-scientist': 'Build machine learning models and AI solutions for data-driven insights',
            'devops-engineer': 'Implement CI/CD pipelines, automation, and infrastructure as code',
            'database-administrator': 'Manage and optimize Azure SQL databases and data platforms',
            'network-engineer': 'Design and implement Azure networking solutions and connectivity',
            'security-operations-analyst': 'Monitor, investigate, and respond to security threats and incidents',
            'identity-access-admin': 'Manage user identities, access controls, and authentication systems',
            'functional-consultant': 'Configure and customize business applications to meet organizational needs',
            'auditor': 'Assess compliance, governance, and security of cloud environments',
            'business-analyst': 'Analyze business requirements and translate them into technical solutions',
            'business-owner': 'Drive digital transformation and technology adoption strategies',
            'business-user': 'Utilize Microsoft 365 and business applications for productivity',
            'ip-admin': 'Manage information protection, data classification, and compliance policies',
            'privacy-manager': 'Ensure data privacy compliance and implement privacy controls',
            'risk-practitioner': 'Assess and manage technology and compliance risks',
            'higher-ed-educator': 'Integrate technology into higher education teaching and learning',
            'k-12-educator': 'Use educational technology to enhance K-12 classroom experiences',
            'school-leader': 'Lead digital transformation in educational institutions',
            'parent-guardian': 'Support student learning through educational technology',
            'student': 'Build technology skills for academic and career success',
            'maker': 'Create custom business applications using low-code/no-code platforms',
            'startup-founder': 'Leverage cloud technology to build and scale startup ventures',
            'service-adoption-specialist': 'Drive user adoption and change management for technology services',
            'support-engineer': 'Provide technical support and troubleshooting for Azure services',
            'technology-manager': 'Lead technology teams and drive technical strategy',
            'technical-writer': 'Create technical documentation and educational content',
            'platform-engineer': 'Build and maintain development platforms and infrastructure (emerging role)'
        }
        
        # Get description from our mapping, or create a generic one
        description = role_descriptions.get(role_id, f"Technology professional specializing in {role_name.lower()} responsibilities")
        
        return description
    
    def _is_certification_retired(self, cert_data: dict, title: str) -> bool:
        """
        Check if a certification is retired or deprecated.
        
        Args:
            cert_data: The certification data from API
            title: The certification title
            
        Returns:
            True if the certification appears to be retired
        """
        # Check for explicit retirement indicators
        if cert_data.get('retirement_date') is not None:
            return True
            
        if cert_data.get('retired', False):
            return True
            
        if cert_data.get('status') == 'retired':
            return True
        
        # Check title for retirement keywords
        title_lower = title.lower()
        retirement_keywords = [
            'retired',
            'deprecated', 
            'legacy',
            'discontinued',
            'end of life',
            'eol'
        ]
        
        if any(keyword in title_lower for keyword in retirement_keywords):
            return True
        
        # Check for old technology versions that are likely retired
        old_tech_patterns = [
            'office 2013',
            'office 2016', 
            'sql server 2012',
            'sql server 2014',
            'windows server 2012',
            'windows server 2016',
            'mcsa:',  # MCSA certifications are generally retired
            'mcse:',  # MCSE certifications are generally retired  
            'mcsd:',  # MCSD certifications are generally retired
            'mta:',   # MTA certifications are generally retired
        ]
        
        if any(pattern in title_lower for pattern in old_tech_patterns):
            return True
            
        return False
    
    def _get_exam_codes_for_certification(self, cert_uid: str) -> list:
        """
        Get exam codes for a certification based on known mappings.
        
        Since the MS Learn API is missing current exam codes, we maintain
        a mapping of the most important/current certifications to their exam codes.
        
        Args:
            cert_uid: The certification UID
            
        Returns:
            List of exam codes (e.g., ['AZ-500', 'SC-300'])
        """
        # Known certification to exam code mappings
        # Based on official Microsoft documentation
        cert_exam_mapping = {
            # Azure Security certifications
            'certification.azure-security-engineer': ['AZ-500'],
            'certification.identity-and-access-administrator': ['SC-300'],
            'certification.security-operations-analyst': ['SC-200'],
            'certification.security-compliance-and-identity-fundamentals': ['SC-900'],
            'certification.cybersecurity-architect-expert': ['SC-100'],
            
            # Azure AI certifications
            'certification.azure-ai-engineer': ['AI-102'],
            'certification.ai-edge-engineer': ['AI-102', 'AZ-220'],  # Emerging field combining AI + IoT
            
            # Azure Architecture certifications
            'certification.azure-solutions-architect': ['AZ-305'],
            'certification.azure-solutions-architect-expert': ['AZ-305'],
            
            # Azure Infrastructure certifications  
            'certification.azure-administrator': ['AZ-104'],
            'certification.azure-fundamentals': ['AZ-900'],
            'certification.azure-developer': ['AZ-204'],
            'certification.azure-data-engineer': ['DP-305'],
            'certification.azure-data-scientist': ['DP-100'],
            'certification.azure-database-administrator-associate': ['DP-300'],
            'certification.azure-data-fundamentals': ['DP-900'],
            'certification.azure-ai-fundamentals': ['AI-900'],
            
            # DevOps and specialized
            'certification.devops-engineer': ['AZ-400'],
            'certification.azure-network-engineer-associate': ['AZ-700'],
            'certification.azure-virtual-desktop-specialty': ['AZ-140'],
            'certification.azure-iot-developer-specialty': ['AZ-220'],
            'certification.azure-cosmos-db-developer-specialty': ['DP-420'],
            
            # Microsoft 365 certifications
            'certification.m365-security-administrator': ['MS-500'],
            'certification.m365-messaging-administrator': ['MS-203'],
            'certification.m365-teams-administrator-associate': ['MS-700'],
            'certification.m365-enterprise-administrator': ['MS-102'],
            'certification.microsoft-365-fundamentals': ['MS-900'],
            
            # Power Platform
            'certification.power-platform-fundamentals': ['PL-900'],
            'certification.power-platform-app-maker': ['PL-100'],
            'certification.power-platform-developer-associate': ['PL-400'],
            'certification.power-platform-solution-architect-expert': ['PL-600'],
            
            # Windows Server
            'certification.windows-server-hybrid-administrator': ['AZ-800', 'AZ-801'],
        }
        
        return cert_exam_mapping.get(cert_uid, [])
    
    def _is_questionable_role_association(self, cert_uid: str, role_uid: str) -> dict:
        """
        Check if a certification's association with a role seems questionable.
        
        Args:
            cert_uid: The certification identifier
            role_uid: The role identifier
            
        Returns:
            Dict with 'is_questionable' (bool) and 'explanation' (str) if questionable
        """
        questionable_associations = {
            # Windows Server certification incorrectly tagged as security-engineer
            ('certification.windows-server-hybrid-administrator', 'security-engineer'): {
                'is_questionable': True,
                'explanation': "Microsoft's API incorrectly associates Windows Server Hybrid Administrator (AZ-800/AZ-801) with the Security Engineer role. While Windows Server administration does involve some security aspects, this certification is primarily focused on infrastructure management, Active Directory, and hybrid cloud operations rather than Azure security engineering. This certification would be more appropriately categorized under 'Azure Administrator' or 'Infrastructure Administrator' roles."
            },
            # Add more questionable associations as we discover them
            # Example: AI certifications incorrectly tagged as developer role
            ('certification.azure-ai-engineer', 'developer'): {
                'is_questionable': True,
                'explanation': "While AI Engineers do development work, this certification is specifically focused on AI/ML services and should primarily be associated with the AI Engineer role rather than general Developer role."
            },
            # Example: Data certifications tagged as general administrator
            ('certification.azure-data-engineer', 'administrator'): {
                'is_questionable': True,
                'explanation': "Data Engineering requires specialized skills in data pipelines, analytics, and big data processing that go beyond general Azure administration."
            }
        }
        
        # Check if this specific combination is questionable
        association_key = (cert_uid, role_uid)
        if association_key in questionable_associations:
            return questionable_associations[association_key]
        
        # Additional heuristic checks for common patterns
        
        # Windows Server certs should generally not be in security-engineer role
        if 'windows-server' in cert_uid and role_uid == 'security-engineer':
            return {
                'is_questionable': True,
                'explanation': f"This Windows Server certification ({cert_uid}) appears to be incorrectly categorized under Security Engineer. Windows Server certifications typically focus on infrastructure administration rather than Azure security engineering."
            }
        
        # Expert/Architect level certifications in basic administrator roles
        if ('expert' in cert_uid or 'architect' in cert_uid) and role_uid == 'administrator':
            return {
                'is_questionable': True,
                'explanation': f"This expert-level certification may be too advanced for general Administrator role. Expert and Architect certifications typically require specialized knowledge beyond basic administration."
            }
        
        # Security certifications in obviously inappropriate non-security roles
        # BUT allow security certs in architect/solution-architect roles since they need security knowledge
        if ('security' in cert_uid or 'cybersecurity' in cert_uid) and role_uid not in [
            'security-engineer', 'security-operations-analyst', 'solution-architect', 'enterprise-architect'
        ]:
            # Special case: don't warn about cybersecurity-architect in solution-architect role
            if cert_uid == 'certification.cybersecurity-architect-expert' and role_uid == 'solution-architect':
                pass  # No warning - this is appropriate
            else:
                return {
                    'is_questionable': True,
                    'explanation': f"This security-focused certification may be more appropriate for specialized security roles rather than general {role_uid.replace('-', ' ')} role."
                }
        
        # AI/ML certifications should generally not be in general developer role
        if ('ai-' in cert_uid or 'data-scientist' in cert_uid) and role_uid == 'developer':
            return {
                'is_questionable': True,
                'explanation': f"This AI/ML certification may be more appropriate for specialized AI Engineer or Data Scientist roles rather than general Developer role."
            }
        
        # Data engineering certs should generally not be in general administrator role  
        if 'data-engineer' in cert_uid and role_uid == 'administrator':
            return {
                'is_questionable': True,
                'explanation': f"This Data Engineering certification requires specialized data skills beyond general Azure administration."
            }
        
        # Architecture certifications should warn when in engineer/administrator roles, but not other architect roles
        if 'architect' in cert_uid and role_uid in ['administrator', 'developer', 'security-engineer', 'devops-engineer']:
            # Special handling for cybersecurity-architect in security-engineer role
            if cert_uid == 'certification.cybersecurity-architect-expert' and role_uid == 'security-engineer':
                return {
                    'is_questionable': True,
                    'explanation': f"This architect-level certification focuses on strategic security design and high-level architectural decisions, which may be more advanced than the hands-on implementation focus of the Security Engineer role."
                }
            else:
                return {
                    'is_questionable': True,
                    'explanation': f"This architecture certification focuses on solution design and architectural decisions, which may be more appropriate for architect-level roles."
                }
        
        return {'is_questionable': False, 'explanation': ''}
    
    def _is_certification_ready(self, cert_uid: str) -> bool:
        """
        Check if we have curated, ready-to-use content for this certification.
        
        Args:
            cert_uid: The certification identifier
            
        Returns:
            True if we have curated modules ready for this certification
        """
        ready_certifications = {
            # Security Role Certifications (Proven & Working)
            'certification.identity-and-access-administrator',  # SC-300
            'certification.azure-security-engineer',  # AZ-500
            'certification.security-operations-analyst',  # SC-200
            'certification.security-compliance-and-identity-fundamentals',  # SC-900
            'certification.cybersecurity-architect-expert',  # SC-100
            
            # AI Role Certifications (High Growth Field)
            'certification.azure-ai-engineer',  # AI-102
            'certification.ai-edge-engineer',  # AI-102 + AZ-220
            
            # Solution Architect Certifications
            'certification.azure-solutions-architect',  # AZ-305
            'certification.azure-solutions-architect-expert',  # AZ-305
            
            # Administrator Role Certifications (Select ones)
            'certification.azure-fundamentals',  # AZ-900
            'certification.windows-server-hybrid-administrator',  # AZ-800/801
            
            # Note: We intentionally exclude some popular ones like:
            # - certification.azure-administrator (AZ-104) - not ready yet
            # - certification.azure-developer (AZ-204) - not ready yet
            # These will show as "coming soon" until we add curated content
        }
        
        return cert_uid in ready_certifications
    
    def get_certifications_for_role(self, role_uid: str) -> List[Certification]:
        """
        Get certifications for a specific role.
        
        Args:
            role_uid: The role identifier from MS Learn API
            
        Returns:
            List of Certification objects, empty list if none found
        """
        def fetch_certifications():
            logger.info(f"Fetching certifications for role: {role_uid}")
            
            # First, get all roles to find the correct one
            roles = self.get_available_roles()
            role_found = any(role.uid == role_uid for role in roles)
            
            if not role_found:
                logger.warning(f"Role {role_uid} not found in available roles")
                return []
            
            # Get all certifications (API role filtering doesn't work properly)
            url = f"{self.api_base}/?type=certifications"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            all_certs_data = data.get('certifications', [])
            
            # Filter certifications that actually match this role
            certifications = []
            for cert_data in all_certs_data:
                cert_roles = cert_data.get('roles', [])
                
                # Only include certifications that have this role
                if role_uid in cert_roles:
                    # Additional filtering: exclude obvious retired/deprecated certifications
                    title = cert_data.get('title', '')
                    cert_uid = cert_data.get('uid', '')
                    
                    # NOTE: Microsoft Learn API has some questionable role associations
                    # For example, Windows Server Hybrid Administrator (AZ-800/AZ-801) 
                    # is incorrectly tagged with 'security-engineer' role
                    # We log this but trust the API data for now
                    if role_uid == 'security-engineer' and 'windows-server' in cert_uid:
                        logger.warning(f"Microsoft API associates Windows Server cert {cert_uid} with security-engineer role - this may be incorrect")
                    
                    if not self._is_certification_retired(cert_data, title):
                        # MODULAR FILTERING: Only show certifications we have ready content for
                        if self._is_certification_ready(cert_uid):
                            # Get exam codes for this certification
                            exam_codes = self._get_exam_codes_for_certification(cert_uid)
                            
                            # Check if this role association is questionable
                            questionable_info = self._is_questionable_role_association(cert_uid, role_uid)
                            
                            # Get the full description without truncation
                            description = cert_data.get('subtitle', cert_data.get('summary', 'No description available'))
                            
                            cert = Certification(
                                uid=cert_uid,
                                name=title or cert_data.get('displayName', 'Unknown Certification'),
                                description=description,
                                level=cert_data.get('certification_type', cert_data.get('level', 'Unknown')),
                                module_count=0,  # We'll calculate this on-demand when needed
                                exam_codes=exam_codes,
                                questionable_role_association=questionable_info.get('is_questionable', False),
                                role_association_explanation=questionable_info.get('explanation', '')
                            )
                            if cert.uid:
                                certifications.append(cert)
                        else:
                            logger.debug(f"Skipping {cert_uid} - not ready for testing yet")
            
            logger.info(f"Found {len(certifications)} active certifications for role {role_uid} (filtered from {len(all_certs_data)} total)")
            return certifications
        
        try:
            cache_key = f"certs_{role_uid}"
            return self._get_cached_or_fetch(cache_key, fetch_certifications)
        except Exception as e:
            logger.error(f"Failed to fetch certifications for role {role_uid}: {e}")
            return []
    
    def get_role_certifications(self, role_uid: str) -> dict:
        """
        Get certifications for a role, formatted for API response.
        Returns dictionary with role_id and certifications list.
        """
        try:
            certifications = self.get_certifications_for_role(role_uid)
            
            # Convert Certification dataclass objects to dictionaries
            cert_dicts = []
            for cert in certifications:
                cert_dict = {
                    'id': cert.uid,
                    'name': cert.name,
                    'description': cert.description,
                    'level': cert.level,
                    'exam_codes': cert.exam_codes,
                    'module_count': cert.module_count,
                    'questionable_role_association': cert.questionable_role_association,
                    'role_association_explanation': cert.role_association_explanation
                }
                cert_dicts.append(cert_dict)
            
            return {
                'role_id': role_uid,
                'certifications': cert_dicts
            }
        except Exception as e:
            logger.error(f"Failed to get role certifications for {role_uid}: {e}")
            return {'role_id': role_uid, 'certifications': []}
    
    def get_certification_full_details(self, cert_uid: str) -> dict:
        """
        Get full details for a certification including the complete, untruncated description.
        This method returns the stored full description from our certification cache.
        """
        cache_key = f"cert_details_{cert_uid}"
        
        def fetch_details():
            """Fetch certification details from API or fallback."""
            logger.info(f"Fetching full certification details for: {cert_uid}")
            
            # PHASE 1: Try to get the description from our live role-based API data
            cert_name = 'Microsoft Certification'  # Default fallback
            cert_level = 'Unknown'
            description = "No detailed description available."
            
            try:
                # Search through all roles to find this certification and get its description
                for role in self.get_available_roles():
                    certifications = self.get_certifications_for_role(role.uid)
                    for cert in certifications:
                        if cert.uid == cert_uid:
                            cert_name = cert.name
                            cert_level = cert.level
                            # Use the live API description from role-based data
                            if cert.description and cert.description.strip():
                                description = cert.description
                                logger.info(f"✅ Using live API description for {cert_uid}")
                                break
                    if description != "No detailed description available.":
                        break
            except Exception as e:
                logger.warning(f"Could not get certification details from live data: {e}")
            
            # PHASE 2: Fallback to enhanced descriptions if live API didn't work
            if description == "No detailed description available.":
                fallback_descriptions = {
                    'certification.security-compliance-and-identity-fundamentals': 
                        "This exam is targeted to you if you're looking to familiarize yourself with the fundamentals of security, compliance, and identity across cloud-based and related Microsoft services. This certification serves as a stepping stone if you're interested in advancing to role-based certifications in security operations, identity and access management, or information protection. The exam covers security, compliance, and identity concepts; capabilities of Microsoft Azure Active Directory; capabilities of Microsoft Security solutions; and capabilities of Microsoft compliance solutions.",
                    
                    'certification.azure-security-engineer':
                        "As the Azure security engineer, you implement, manage, and monitor security for resources in Azure, multi-cloud, and hybrid environments as part of an end-to-end infrastructure. You implement and manage security components and configurations by using Microsoft Defender for Cloud and other tools. You ensure that the infrastructure aligns with standards and best practices such as the Microsoft Cloud Security Benchmark (MCSB). Your responsibilities as an Azure security engineer include: Managing the security posture. Implementing threat protection. Identifying and remediating vulnerabilities. You are responsible for implementing regulatory compliance controls for Azure infrastructure including identity and access, network, compute, storage, data, applications, asset management, backup and recovery, and devops security. As an Azure security engineer, you work with architects, administrators, and developers to plan and implement solutions that meet security and compliance requirements. You may also collaborate with security operations in responding to security incidents in Azure. You should have: Practical experience in administration of Microsoft Azure and hybrid environments. Strong familiarity with Microsoft Entra ID, as well as compute, network, and storage in Azure.",
                    
                    'certification.cybersecurity-architect-expert':
                        "As a Microsoft cybersecurity architect, you translate a cybersecurity strategy into capabilities that protect the assets, business, and operations of an organization. You design, guide the implementation of, and maintain security solutions that follow Zero Trust principles and best practices, including security strategies for identity, devices, data, applications, network, infrastructure, and DevOps. You continuously collaborate with leaders and practitioners in IT security, privacy, and other roles across an organization to plan and implement a cybersecurity strategy that meets the business needs of an organization.",
                    
                    'certification.identity-and-access-administrator':
                        "As a Microsoft identity and access administrator, you design, implement, and operate an organization's identity and access management systems by using Azure Active Directory (Azure AD). You manage tasks such as providing secure authentication and authorization access to enterprise applications. You provide seamless experiences and self-service management capabilities for all users. You're responsible for configuring and managing authentication and authorization of identities for users, devices, Azure resources, and applications.",
                    
                    'certification.windows-server-hybrid-administrator':
                        "As a candidate for this certification, you're responsible for administering core and advanced Windows Server workloads and services using on-premises, hybrid, and cloud technologies. Your responsibilities include implementing, managing, and maintaining on-premises and hybrid solutions such as identity, management, compute, networking, and storage. You use administrative tools and technologies including Windows Admin Center, PowerShell, Azure Arc, and IaaS virtual machine administration. You also integrate Windows Server environments with Azure services and manage Windows Server in on-premises networks.",
                    
                    'certification.azure-solutions-architect-expert':
                        "As a Microsoft Azure solutions architect, you have subject matter expertise in designing cloud and hybrid solutions that run on Azure, including compute, network, storage, monitoring, and security. You have skills and experience operating within the following areas: Administration, Development, and DevOps. You should have expert-level skills in Azure administration and development and foundational skills in DevOps. You design solutions for the following: Compute, Network, Storage, Monitoring, and Security."
                }
                
                # Use enhanced description if available
                description = fallback_descriptions.get(cert_uid, "No detailed description available.")
                if description != "No detailed description available.":
                    logger.info(f"✅ Using fallback description for {cert_uid}")
            
            details = {
                'id': cert_uid,
                'name': cert_name,
                'description': description,
                'level': cert_level,
                'exam_codes': self._get_exam_codes_for_certification(cert_uid),
                'url': '',
                'last_updated': '',
                'icon_url': ''
            }
            
            return details
        
        try:
            # Use the existing caching mechanism
            return self._get_cached_or_fetch(cache_key, fetch_details)
        except Exception as e:
            logger.error(f"Error fetching full certification details for {cert_uid}: {e}")
            return {
                'id': cert_uid,
                'name': 'Microsoft Certification',
                'description': 'Unable to load certification details at this time.',
                'level': 'Unknown',
                'exam_codes': [],
                'url': '',
                'last_updated': '',
                'icon_url': ''
            }
    
    def get_modules_for_certification(self, cert_uid: str) -> List[Module]:
        """
        Get modules for a specific certification.
        
        🚀 ENHANCED: Now uses live MS Learn API data with smart fallbacks
        - Phase 1: Try live API with auto-discovery patterns
        - Phase 2: Fallback to curated, high-quality content
        - Scales automatically to new Microsoft certifications
        
        Args:
            cert_uid: The certification identifier
            
        Returns:
            List of Module objects, empty list if none found
        """
        def fetch_modules():
            logger.info(f"Fetching modules for certification: {cert_uid}")
            
            # PHASE 1: Try live API data first (with auto-discovery)
            try:
                api_modules = self.api_service.get_modules_for_certification(cert_uid)
                if api_modules:
                    logger.info(f"✅ Using live API data: {len(api_modules)} modules")
                    return api_modules
                else:
                    logger.info("No API modules found, falling back to curated content")
            except Exception as e:
                logger.warning(f"API fetch failed, using curated fallback: {e}")
            
            # PHASE 2: Fallback to curated, high-quality content
            logger.info(f"Using curated modules for certification: {cert_uid}")
            
            # === SECURITY ROLE CERTIFICATIONS (Proven & Working) ===
            if 'identity-and-access-administrator' in cert_uid:
                curated_modules = self._get_sc300_modules()
            elif 'azure-security-engineer' in cert_uid:
                curated_modules = self._get_azure_security_modules()
            elif 'security-operations-analyst' in cert_uid:
                curated_modules = self._get_security_operations_modules()
            elif 'security-compliance-and-identity-fundamentals' in cert_uid:
                curated_modules = self._get_sc900_modules()
            elif 'cybersecurity-architect-expert' in cert_uid:
                curated_modules = self._get_sc100_modules()
            
            # === AI ROLE CERTIFICATIONS (High Growth Field) ===
            elif 'azure-ai-engineer' in cert_uid:
                curated_modules = self._get_ai_engineer_modules()
            elif 'ai-edge-engineer' in cert_uid:
                curated_modules = self._get_ai_edge_engineer_modules()
            
            # === SOLUTION ARCHITECT CERTIFICATIONS ===
            elif 'azure-solutions-architect' in cert_uid:
                curated_modules = self._get_solution_architect_modules()
            
            # === ADMINISTRATOR ROLE CERTIFICATIONS ===
            elif 'azure-fundamentals' in cert_uid:
                curated_modules = self._get_azure_fundamentals_modules()
            elif 'azure-administrator' in cert_uid:
                curated_modules = self._get_azure_administrator_modules()
            elif 'windows-server-hybrid-administrator' in cert_uid:
                curated_modules = self._get_az800_modules()
            
            # === DEVELOPER ROLE CERTIFICATIONS ===
            elif 'azure-developer' in cert_uid:
                curated_modules = self._get_azure_developer_modules()
            # - Data Engineer (DP-203)
            # - AI Engineer (AI-102) 
            # - DevOps Engineer (AZ-400)
            # - Solution Architect (AZ-305)
            
            else:
                # For unsupported certifications, be honest about it
                logger.info(f"Certification {cert_uid} not yet supported in current modular approach")
                return self._generate_coming_soon_modules(cert_uid)
            
            if curated_modules:
                logger.info(f"Using {len(curated_modules)} curated modules for {cert_uid}")
                return curated_modules
            
            # This shouldn't happen with our modular approach
            logger.warning(f"No curated modules found for supported certification {cert_uid}")
            return self._generate_sample_modules(cert_uid)
        
        try:
            cache_key = f"modules_{cert_uid}"
            return self._get_cached_or_fetch(cache_key, fetch_modules)
        except Exception as e:
            logger.error(f"Failed to fetch modules for certification {cert_uid}: {e}")
            return []
    
    def get_module_with_units(self, module_uid: str) -> Optional[ModuleDetails]:
        """
        Get complete module details including units.
        
        Args:
            module_uid: The module identifier
            
        Returns:
            ModuleDetails object or None if not found
        """
        # Direct API call without caching to avoid hangs
        try:
            logger.info(f"Fetching module details for: {module_uid}")
            
            url = f"{self.api_base}/?type=modules&uid={module_uid}"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            modules = data.get('modules', [])
            
            # Find the specific module by UID (API returns all modules)
            target_module = None
            for module in modules:
                if module.get('uid') == module_uid:
                    target_module = module
                    break
            
            if target_module:
                # Also get the units data for proper unit details
                all_units_data = data.get('units', [])
                return self._process_module_details_simple(target_module, all_units_data)
            else:
                logger.warning(f"Module UID {module_uid} not found in API response")
                
        except Exception as e:
            logger.debug(f"API fetch failed for {module_uid}: {e}")
        
        # Fallback to curated modules
        all_curated_modules = []
        all_curated_modules.extend(self._get_azure_fundamentals_modules())
        all_curated_modules.extend(self._get_azure_security_modules())
        all_curated_modules.extend(self._get_generic_azure_modules())
        all_curated_modules.extend(self._get_sc300_modules())
        all_curated_modules.extend(self._get_sc900_modules())
        all_curated_modules.extend(self._get_sc100_modules())
        all_curated_modules.extend(self._get_az800_modules())
        all_curated_modules.extend(self._get_security_operations_modules())
        all_curated_modules.extend(self._get_ai_engineer_modules())
        all_curated_modules.extend(self._get_ai_edge_engineer_modules())
        all_curated_modules.extend(self._get_solution_architect_modules())
        
        for module in all_curated_modules:
            if module.uid == module_uid:
                return self._convert_module_to_details(module)
        
        logger.warning(f"Module details not found: {module_uid}")
        return None
    
    def _process_module_details_simple(self, module_data: dict, all_units_data: list = None) -> ModuleDetails:
        """Process module data from API into ModuleDetails object with working unit URLs."""
        
        # Get unit UIDs (they're stored as strings)
        unit_uids = module_data.get('units', [])
        units = []
        
        # Use module URL for all units since our content scraper can handle module-level content
        module_url = module_data.get('url', '')
        
        # If we have all_units_data (from API response), create a lookup
        units_lookup = {}
        if all_units_data:
            units_lookup = {unit.get('uid'): unit for unit in all_units_data if unit.get('uid')}
        
        # Process each unit UID
        for i, unit_uid in enumerate(unit_uids, 1):
            if isinstance(unit_uid, str):
                # Get unit details from lookup
                unit_details = units_lookup.get(unit_uid, {})
                
                unit = Unit(
                    title=unit_details.get('title', f'Unit {i}'),
                    url=module_url,  # Use module URL for all units
                    type=unit_details.get('type', 'content'),
                    duration_minutes=unit_details.get('duration_in_minutes', 10)
                )
                units.append(unit)
        
        return ModuleDetails(
            uid=module_data.get('uid', ''),
            title=module_data.get('title', 'Unknown Module'),
            summary=module_data.get('summary', 'No description available'),
            url=module_data.get('url', ''),
            duration_minutes=module_data.get('duration_in_minutes', 30),  # Fixed field name
            level=module_data.get('levels', ['Unknown'])[0] if module_data.get('levels') else 'Unknown',
            rating=module_data.get('rating', 0.0),
            units=units
        )
    
    def _process_module_details(self, module_data: dict, all_units_data: list = None) -> ModuleDetails:
        """Process module data from API into ModuleDetails object with proper unit URLs."""
        
        # Get unit UIDs (they're stored as strings)
        unit_uids = module_data.get('units', [])
        units = []
        
        # Use module URL for all units since our content scraper can handle module-level content
        # This is more reliable than trying to construct individual unit URLs
        module_url = module_data.get('url', '')
        
        # If we have all_units_data (from API response), create a lookup
        units_lookup = {}
        if all_units_data:
            units_lookup = {unit.get('uid'): unit for unit in all_units_data if unit.get('uid')}
        
        # Process each unit UID
        for i, unit_uid in enumerate(unit_uids, 1):
            if isinstance(unit_uid, str):
                # Get unit details from lookup
                unit_details = units_lookup.get(unit_uid, {})
                
                # Use module URL for all units - our backend can extract content from module page
                unit_url = module_url
                
                unit = Unit(
                    title=unit_details.get('title', f'Unit {i}'),
                    url=unit_url,
                    type=unit_details.get('type', 'content'),
                    duration_minutes=unit_details.get('duration_in_minutes', 10)
                )
                units.append(unit)
        
        return ModuleDetails(
            uid=module_data.get('uid', ''),
            title=module_data.get('title', 'Unknown Module'),
            summary=module_data.get('summary', 'No description available'),
            url=module_data.get('url', ''),
            duration_minutes=module_data.get('duration_in_minutes', 30),  # Fixed field name
            level=module_data.get('levels', ['Unknown'])[0] if module_data.get('levels') else 'Unknown',
            rating=module_data.get('rating', 0.0),
            units=units
        )
    
    def _extract_module_base_url(self, first_unit_url: str) -> str:
        """Extract base URL pattern from firstUnitUrl."""
        if not first_unit_url:
            return ""
        
        # Example: https://learn.microsoft.com/en-us/training/modules/deploy-device-data-protection/1-introduction/
        # Extract: https://learn.microsoft.com/en-us/training/modules/deploy-device-data-protection/
        
        if '/training/modules/' in first_unit_url:
            parts = first_unit_url.split('/training/modules/')
            if len(parts) > 1:
                module_part = parts[1].split('/')[0]  # Get module name
                return f"{parts[0]}/training/modules/{module_part}/"
        
        return ""
    
    def _construct_unit_url(self, base_url: str, unit_uid: str, unit_number: int) -> str:
        """Construct unit URL based on base URL and unit information."""
        if not base_url:
            return ""
        
        # Extract unit name from UID (e.g., learn.wwl.module.unit-name -> unit-name)
        unit_name = unit_uid.split('.')[-1] if '.' in unit_uid else unit_uid
        
        # Construct URL: base_url + number-unit-name/
        unit_url = f"{base_url}{unit_number}-{unit_name}/"
        
        return unit_url
    
    def _convert_module_to_details(self, module: Module) -> ModuleDetails:
        """Convert a Module object to ModuleDetails with generated units."""
        # Generate sample units based on the module's unit_count
        units = []
        for i in range(module.unit_count):
            unit_type = "knowledge-check" if i == module.unit_count - 1 else "content"
            # Use the module URL for all units since our backend can handle module-level content
            # The backend will extract content from the module page regardless of the specific unit
            unit = Unit(
                title=f"Unit {i+1}: {self._generate_unit_title(module.title, i+1)}",
                url=module.url,  # Use module URL instead of fake unit URLs
                type=unit_type,
                duration_minutes=max(5, module.duration_minutes // module.unit_count)
            )
            units.append(unit)
        
        return ModuleDetails(
            uid=module.uid,
            title=module.title,
            summary=module.summary,
            url=module.url,
            duration_minutes=module.duration_minutes,
            level=module.level,
            rating=4.5,  # Default good rating for curated content
            units=units
        )
    
    def _generate_unit_title(self, module_title: str, unit_number: int) -> str:
        """Generate appropriate unit titles based on module content."""
        base_titles = [
            "Introduction and Overview",
            "Core Concepts",
            "Implementation Details", 
            "Configuration and Setup",
            "Best Practices",
            "Advanced Topics",
            "Security Considerations",
            "Troubleshooting",
            "Hands-on Exercise",
            "Assessment and Review"
        ]
        
        if unit_number <= len(base_titles):
            return base_titles[unit_number - 1]
        else:
            return f"Additional Topic {unit_number - len(base_titles)}"
    
    def _get_modules_from_learning_path(self, lp_uid: str) -> List[Module]:
        """Get modules from a learning path."""
        try:
            url = f"{self.api_base}/learning-paths/{lp_uid}/modules"
            response = self.session.get(url, timeout=3)  # Very short timeout
            response.raise_for_status()
            
            data = response.json()
            modules_data = data.get('modules', [])
            
            modules = []
            for module_data in modules_data[:5]:  # Limit to first 5 modules per learning path
                module = Module(
                    uid=module_data.get('uid', ''),
                    title=module_data.get('title', 'Unknown Module'),
                    summary=module_data.get('summary', 'No description available'),
                    url=module_data.get('url', ''),
                    duration_minutes=module_data.get('durationInMinutes', 30),
                    level=module_data.get('level', 'Unknown'),
                    unit_count=len(module_data.get('units', []))
                )
                if module.uid:
                    modules.append(module)
            
            return modules
            
        except Exception as e:
            logger.debug(f"Failed to get modules from learning path {lp_uid}: {e}")
            return []
    
    def _get_modules_from_api(self, cert_uid: str) -> List[Module]:
        """
        Try to get real modules for a certification from the Microsoft Learn API.
        
        Uses a focused approach for known high-priority certifications only.
        Returns empty list if not a priority certification or if API fails.
        """
        # Only attempt API queries for specific high-priority certifications
        # to avoid overwhelming the API and causing timeouts
        priority_certifications = {
            'certification.azure-administrator',
            'certification.azure-developer', 
            'certification.azure-solutions-architect-expert',
            'certification.azure-data-engineer',
            'certification.azure-ai-engineer',
            'certification.azure-network-engineer-associate',
            'certification.azure-database-administrator-associate',
            'certification.devops-engineer',
            'certification.m365-security-administrator',
            'certification.m365-messaging-administrator',
            'certification.power-platform-fundamentals'
        }
        
        if cert_uid not in priority_certifications:
            logger.debug(f"Skipping API query for non-priority certification: {cert_uid}")
            return []
        
        modules = []
        
        try:
            # Use a more targeted learning paths approach with timeout
            logger.debug(f"Trying focused learning paths query for priority certification: {cert_uid}")
            lp_url = f"{self.api_base}/?type=learningPaths&certifications={cert_uid}"
            
            # Use very short timeout to fail fast and use fallbacks
            response = self.session.get(lp_url, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            learning_paths = data.get('learningPaths', [])
            
            # Limit to first few learning paths to avoid overwhelming the system
            for lp in learning_paths[:2]:  # Only process first 2 learning paths
                lp_modules = self._get_modules_from_learning_path(lp.get('uid', ''))
                modules.extend(lp_modules)
                
                # Stop if we have enough modules
                if len(modules) >= 10:
                    break
            
            if modules:
                logger.info(f"Found {len(modules)} modules via API for {cert_uid}")
                return modules[:15]  # Limit to 15 modules max
                
        except Exception as e:
            logger.debug(f"API query failed for {cert_uid}: {e}")
        
        logger.debug(f"API query returned no results for {cert_uid}")
        return []
    
    def _generate_sample_modules(self, cert_uid: str) -> List[Module]:
        """Generate sample modules as a fallback when no real content is available."""
        cert_name = cert_uid.replace('certification.', '').replace('-', ' ').title()
        
        base_modules = [
            Module(
                uid=f"sample-{cert_uid}-intro",
                title=f"Introduction to {cert_name}",
                summary=f"Overview of key concepts and fundamentals for {cert_name} certification",
                url=f"/sample/{cert_uid}/intro",
                duration_minutes=45,
                level="Beginner",
                unit_count=8
            ),
            Module(
                uid=f"sample-{cert_uid}-core",
                title=f"Core {cert_name} Concepts",
                summary=f"Essential topics and practical skills for {cert_name}",
                url=f"/sample/{cert_uid}/core",
                duration_minutes=60,
                level="Intermediate", 
                unit_count=10
            ),
            Module(
                uid=f"sample-{cert_uid}-advanced",
                title=f"Advanced {cert_name} Topics",
                summary=f"In-depth coverage of advanced scenarios for {cert_name}",
                url=f"/sample/{cert_uid}/advanced",
                duration_minutes=75,
                level="Advanced",
                unit_count=12
            ),
            Module(
                uid=f"sample-{cert_uid}-practice",
                title=f"{cert_name} Hands-on Practice",
                summary=f"Practical exercises and real-world scenarios for {cert_name}",
                url=f"/sample/{cert_uid}/practice",
                duration_minutes=90,
                level="Intermediate",
                unit_count=15
            )
        ]
        
        logger.info(f"Generated {len(base_modules)} sample modules for {cert_uid}")
        return base_modules

    def _get_search_terms_for_cert(self, cert_uid: str) -> str:
        """Get search terms for keyword-based module discovery."""
        cert_keywords = {
            'certification.azure-administrator': 'Azure administrator',
            'certification.azure-developer': 'Azure developer',
            'certification.azure-solutions-architect': 'Azure solutions architect',
            'certification.azure-data-engineer': 'Azure data engineer',
            'certification.azure-ai-engineer': 'Azure AI engineer',
            'certification.azure-data-scientist': 'Azure data scientist',
            'certification.devops-engineer': 'Azure DevOps',
            'certification.azure-network-engineer-associate': 'Azure networking',
            'certification.azure-database-administrator-associate': 'Azure database',
            'certification.m365-security-administrator': 'Microsoft 365 security',
            'certification.m365-messaging-administrator': 'Microsoft 365 messaging',
            'certification.m365-teams-administrator-associate': 'Microsoft Teams',
            'certification.power-platform-fundamentals': 'Power Platform',
            'certification.power-platform-app-maker': 'Power Apps',
            'certification.power-platform-developer-associate': 'Power Platform developer',
        }
        
        return cert_keywords.get(cert_uid, '')
    
    def _get_azure_fundamentals_modules(self) -> List[Module]:
        """Azure Fundamentals (AZ-900) modules."""
        return [
            Module(
                uid="learn.azure.intro-to-azure-fundamentals",
                title="Introduction to Azure fundamentals",
                summary="Learn cloud computing concepts, deployment models, and understand specific Azure services",
                url="https://learn.microsoft.com/en-us/training/modules/intro-to-azure-fundamentals/",
                duration_minutes=55,
                level="Beginner",
                unit_count=7
            ),
            Module(
                uid="learn.azure.azure-compute-fundamentals", 
                title="Explore Azure compute services",
                summary="Learn about the various compute services available in Azure",
                url="https://learn.microsoft.com/en-us/training/modules/azure-compute-fundamentals/",
                duration_minutes=45,
                level="Beginner",
                unit_count=6
            ),
            Module(
                uid="learn.azure.azure-networking-fundamentals",
                title="Explore Azure networking services", 
                summary="Learn about core Azure networking services and their capabilities",
                url="https://learn.microsoft.com/en-us/training/modules/azure-networking-fundamentals/",
                duration_minutes=60,
                level="Beginner",
                unit_count=8
            ),
            Module(
                uid="learn.azure.azure-storage-fundamentals",
                title="Explore Azure Storage services",
                summary="Learn about Azure Storage account types and storage services",
                url="https://learn.microsoft.com/en-us/training/modules/azure-storage-fundamentals/",
                duration_minutes=45,
                level="Beginner",
                unit_count=6
            ),
            Module(
                uid="learn.azure.azure-database-fundamentals",
                title="Explore Azure database and analytics services",
                summary="Learn about Azure database services and big data analytics",
                url="https://learn.microsoft.com/en-us/training/modules/azure-database-fundamentals/",
                duration_minutes=60,
                level="Beginner", 
                unit_count=7
            )
        ]
    
    def _get_azure_security_modules(self) -> List[Module]:
        """Azure Security Engineer (AZ-500) modules."""
        return [
            Module(
                uid="learn.azure.manage-identity-and-access",
                title="Manage identity and access in Azure Active Directory",
                summary="Learn to manage identities, implement secure authentication, and configure access management",
                url="https://learn.microsoft.com/en-us/training/modules/manage-identity-and-access/",
                duration_minutes=90,
                level="Intermediate",
                unit_count=10
            ),
            Module(
                uid="learn.azure.secure-network-connectivity-azure",
                title="Implement platform protection",
                summary="Learn to secure network connectivity and implement advanced network security",
                url="https://learn.microsoft.com/en-us/training/modules/secure-network-connectivity-azure/",
                duration_minutes=75,
                level="Intermediate",
                unit_count=8
            ),
            Module(
                uid="learn.azure.manage-security-operations",
                title="Manage security operations in Azure",
                summary="Learn to configure and manage threat protection using Azure Security Center",
                url="https://learn.microsoft.com/en-us/training/modules/manage-security-operations/",
                duration_minutes=85,
                level="Intermediate",
                unit_count=9
            ),
            Module(
                uid="learn.azure.secure-data-and-applications",
                title="Secure data and applications",
                summary="Learn to configure security for storage accounts, databases, and Key Vault",
                url="https://learn.microsoft.com/en-us/training/modules/secure-data-and-applications/",
                duration_minutes=80,
                level="Intermediate",
                unit_count=9
            )
        ]
    
    def _get_generic_azure_modules(self) -> List[Module]:
        """Generic Azure modules for unknown certifications."""
        return [
            Module(
                uid="learn.azure.intro-to-azure",
                title="Introduction to Azure",
                summary="Get started with Microsoft Azure cloud services",
                url="https://learn.microsoft.com/en-us/training/modules/intro-to-azure/",
                duration_minutes=30,
                level="Beginner",
                unit_count=5
            ),
            Module(
                uid="learn.azure.azure-architecture-fundamentals",
                title="Azure architecture fundamentals",
                summary="Learn core Azure architectural components and design principles",
                url="https://learn.microsoft.com/en-us/training/modules/azure-architecture-fundamentals/",
                duration_minutes=45,
                level="Beginner", 
                unit_count=6
            )
        ]
    
    def _get_sc300_modules(self) -> List[Module]:
        """SC-300 Identity and Access Administrator modules."""
        return [
            Module(
                uid="learn.azure.explore-identity-microsoft-entra-id",
                title="Explore identity in Microsoft Entra ID",
                summary="Learn about identity concepts, Microsoft Entra ID features, and identity management",
                url="https://learn.microsoft.com/en-us/training/modules/explore-identity-microsoft-entra-id/",
                duration_minutes=120,
                level="Intermediate",
                unit_count=16
            ),
            Module(
                uid="learn.azure.implement-initial-configuration-microsoft-entra-id",
                title="Implement initial configuration of Microsoft Entra ID",
                summary="Configure and customize Microsoft Entra ID for your organization",
                url="https://learn.microsoft.com/en-us/training/modules/implement-initial-configuration-microsoft-entra-id/",
                duration_minutes=90,
                level="Intermediate", 
                unit_count=12
            ),
            Module(
                uid="learn.azure.create-configure-manage-identities",
                title="Create, configure, and manage identities",
                summary="Manage user accounts, groups, and administrative units in Microsoft Entra ID",
                url="https://learn.microsoft.com/en-us/training/modules/create-configure-manage-identities/",
                duration_minutes=105,
                level="Intermediate",
                unit_count=14
            ),
            Module(
                uid="learn.azure.implement-manage-external-identities",
                title="Implement and manage external identities",
                summary="Configure guest users, external collaboration, and B2B scenarios",
                url="https://learn.microsoft.com/en-us/training/modules/implement-manage-external-identities/",
                duration_minutes=75,
                level="Intermediate",
                unit_count=10
            ),
            Module(
                uid="learn.azure.implement-manage-hybrid-identity",
                title="Implement and manage hybrid identity",
                summary="Configure Microsoft Entra Connect and hybrid identity scenarios",
                url="https://learn.microsoft.com/en-us/training/modules/implement-manage-hybrid-identity/",
                duration_minutes=85,
                level="Advanced",
                unit_count=11
            )
        ]
    
    def _get_sc900_modules(self) -> List[Module]:
        """SC-900 Security, Compliance, and Identity Fundamentals modules."""
        return [
            Module(
                uid="learn.azure.describe-security-concepts-methodologies",
                title="Describe security and compliance concepts",
                summary="Learn fundamental security concepts, methodologies, and compliance frameworks",
                url="https://learn.microsoft.com/en-us/training/modules/describe-security-concepts-methodologies/",
                duration_minutes=60,
                level="Beginner",
                unit_count=8
            ),
            Module(
                uid="learn.azure.describe-identity-concepts",
                title="Describe identity concepts",
                summary="Understand authentication, authorization, and identity management principles",
                url="https://learn.microsoft.com/en-us/training/modules/describe-identity-concepts/",
                duration_minutes=45,
                level="Beginner",
                unit_count=6
            ),
            Module(
                uid="learn.azure.describe-microsoft-entra-id-capabilities",
                title="Describe the capabilities of Microsoft Entra ID",
                summary="Explore Microsoft Entra ID features, licensing, and identity management capabilities",
                url="https://learn.microsoft.com/en-us/training/modules/describe-microsoft-entra-id-capabilities/",
                duration_minutes=75,
                level="Beginner",
                unit_count=10
            ),
            Module(
                uid="learn.azure.describe-azure-ad-identity-protection",
                title="Describe the identity protection and governance capabilities",
                summary="Learn about identity governance, Privileged Identity Management, and access reviews",
                url="https://learn.microsoft.com/en-us/training/modules/describe-azure-ad-identity-protection/",
                duration_minutes=55,
                level="Beginner",
                unit_count=7
            )
        ]
    
    def _get_sc100_modules(self) -> List[Module]:
        """SC-100 Cybersecurity Architect Expert modules."""
        return [
            Module(
                uid="learn.azure.design-solutions-security-operations",
                title="Design solutions for security operations",
                summary="Architect comprehensive security operations and monitoring solutions",
                url="https://learn.microsoft.com/en-us/training/modules/design-solutions-security-operations/",
                duration_minutes=120,
                level="Expert",
                unit_count=15
            ),
            Module(
                uid="learn.azure.design-solutions-identity-access-management",
                title="Design solutions for identity and access management",
                summary="Architect enterprise identity solutions and access management strategies",
                url="https://learn.microsoft.com/en-us/training/modules/design-solutions-identity-access-management/",
                duration_minutes=110,
                level="Expert",
                unit_count=13
            ),
            Module(
                uid="learn.azure.design-solutions-securing-privileged-access",
                title="Design solutions for securing privileged access",
                summary="Architect privileged access management and zero trust strategies",
                url="https://learn.microsoft.com/en-us/training/modules/design-solutions-securing-privileged-access/",
                duration_minutes=100,
                level="Expert",
                unit_count=12
            ),
            Module(
                uid="learn.azure.design-solutions-securing-server-workloads",
                title="Design solutions for securing server and workload infrastructure",
                summary="Architect security for hybrid and multi-cloud server workloads",
                url="https://learn.microsoft.com/en-us/training/modules/design-solutions-securing-server-workloads/",
                duration_minutes=95,
                level="Expert",
                unit_count=11
            )
        ]
    
    def _get_az800_modules(self) -> List[Module]:
        """AZ-800/801 Windows Server Hybrid Administrator modules."""
        return [
            Module(
                uid="learn.azure.deploy-configure-azure-arc-enabled-servers",
                title="Deploy and configure Azure Arc-enabled servers",
                summary="Connect and manage on-premises servers using Azure Arc",
                url="https://learn.microsoft.com/en-us/training/modules/deploy-configure-azure-arc-enabled-servers/",
                duration_minutes=90,
                level="Intermediate",
                unit_count=12
            ),
            Module(
                uid="learn.azure.implement-hybrid-network-infrastructure",
                title="Implement hybrid network infrastructure",
                summary="Configure hybrid connectivity and network infrastructure",
                url="https://learn.microsoft.com/en-us/training/modules/implement-hybrid-network-infrastructure/",
                duration_minutes=85,
                level="Intermediate",
                unit_count=11
            ),
            Module(
                uid="learn.azure.implement-hybrid-identity-windows-server",
                title="Implement hybrid identity in Windows Server",
                summary="Configure Azure AD Connect and hybrid identity scenarios",
                url="https://learn.microsoft.com/en-us/training/modules/implement-hybrid-identity-windows-server/",
                duration_minutes=80,
                level="Intermediate",
                unit_count=10
            ),
            Module(
                uid="learn.azure.implement-windows-server-high-availability",
                title="Implement Windows Server high availability",
                summary="Configure failover clustering and high availability solutions",
                url="https://learn.microsoft.com/en-us/training/modules/implement-windows-server-high-availability/",
                duration_minutes=75,
                level="Advanced",
                unit_count=9
            )
        ]
    
    def get_learning_path_modules(self, learning_path_id: str) -> List[dict]:
        """
        Get modules for a learning path (compatibility method for fetcher).
        
        Args:
            learning_path_id: The learning path identifier
            
        Returns:
            List of module dictionaries compatible with the fetcher
        """
        try:
            logger.info(f"Fetching modules for learning path: {learning_path_id}")
            
            # Try to get learning path from API
            url = f"{self.api_base}/?type=learningPaths&uid={learning_path_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            learning_paths = data.get('learningPaths', [])
            
            if not learning_paths:
                logger.warning(f"Learning path not found: {learning_path_id}")
                return []
            
            lp_data = learning_paths[0]
            modules_data = lp_data.get('modules', [])
            
            # Convert to format expected by fetcher
            modules = []
            for module_data in modules_data:
                module_dict = {
                    'uid': module_data.get('uid', ''),
                    'title': module_data.get('title', 'Unknown Module'),
                    'summary': module_data.get('summary', 'No description available'),
                    'url': module_data.get('url', ''),
                    'durationInMinutes': module_data.get('durationInMinutes', 30),
                    'level': module_data.get('level', 'Unknown'),
                    'units': module_data.get('units', [])
                }
                if module_dict['uid']:
                    modules.append(module_dict)
            
            logger.info(f"Found {len(modules)} modules in learning path {learning_path_id}")
            return modules
            
        except Exception as e:
            logger.error(f"Failed to fetch learning path modules for {learning_path_id}: {e}")
            return []
    
    def _get_security_operations_modules(self) -> List[Module]:
        """SC-200 Security Operations Analyst modules."""
        return [
            Module(
                uid="learn.azure.mitigate-threats-using-microsoft-365-defender",
                title="Mitigate threats using Microsoft 365 Defender",
                summary="Learn to investigate and respond to threats using Microsoft 365 Defender portal",
                url="https://learn.microsoft.com/en-us/training/modules/mitigate-threats-using-microsoft-365-defender/",
                duration_minutes=120,
                level="Intermediate",
                unit_count=15
            ),
            Module(
                uid="learn.azure.mitigate-threats-using-microsoft-defender-for-endpoint",
                title="Mitigate threats using Microsoft Defender for Endpoint",
                summary="Implement and manage Microsoft Defender for Endpoint for threat protection",
                url="https://learn.microsoft.com/en-us/training/modules/mitigate-threats-using-microsoft-defender-for-endpoint/",
                duration_minutes=110,
                level="Intermediate",
                unit_count=14
            ),
            Module(
                uid="learn.azure.mitigate-threats-using-microsoft-defender-for-office-365",
                title="Mitigate threats using Microsoft Defender for Office 365",
                summary="Configure and manage email and collaboration security with Defender for Office 365",
                url="https://learn.microsoft.com/en-us/training/modules/mitigate-threats-using-microsoft-defender-for-office-365/",
                duration_minutes=100,
                level="Intermediate",
                unit_count=13
            ),
            Module(
                uid="learn.azure.mitigate-threats-using-microsoft-defender-for-identity",
                title="Mitigate threats using Microsoft Defender for Identity",
                summary="Detect and investigate identity-based threats using Defender for Identity",
                url="https://learn.microsoft.com/en-us/training/modules/mitigate-threats-using-microsoft-defender-for-identity/",
                duration_minutes=90,
                level="Intermediate",
                unit_count=12
            ),
            Module(
                uid="learn.azure.mitigate-threats-using-microsoft-sentinel",
                title="Mitigate threats using Microsoft Sentinel",
                summary="Configure SIEM and SOAR capabilities with Microsoft Sentinel",
                url="https://learn.microsoft.com/en-us/training/modules/mitigate-threats-using-microsoft-sentinel/",
                duration_minutes=130,
                level="Advanced",
                unit_count=16
            )
        ]
    
    def _get_ai_engineer_modules(self) -> List[Module]:
        """AI-102 Azure AI Engineer modules."""
        return [
            Module(
                uid="learn.azure.prepare-to-develop-ai-solutions-azure",
                title="Prepare to develop AI solutions on Azure",
                summary="Introduction to AI services and cognitive services development on Azure",
                url="https://learn.microsoft.com/en-us/training/modules/prepare-to-develop-ai-solutions-azure/",
                duration_minutes=75,
                level="Intermediate",
                unit_count=10
            ),
            Module(
                uid="learn.azure.create-computer-vision-solutions-azure-cognitive-services",
                title="Create computer vision solutions with Azure Cognitive Services",
                summary="Build applications that can analyze images and videos using Computer Vision API",
                url="https://learn.microsoft.com/en-us/training/modules/create-computer-vision-solutions-azure-cognitive-services/",
                duration_minutes=120,
                level="Intermediate",
                unit_count=15
            ),
            Module(
                uid="learn.azure.develop-natural-language-processing-solutions-azure-cognitive-services",
                title="Develop natural language processing solutions",
                summary="Build NLP applications using Azure Cognitive Services Language APIs",
                url="https://learn.microsoft.com/en-us/training/modules/develop-natural-language-processing-solutions-azure-cognitive-services/",
                duration_minutes=110,
                level="Intermediate",
                unit_count=14
            ),
            Module(
                uid="learn.azure.create-speech-enabled-apps-azure-cognitive-services",
                title="Create speech-enabled apps with Azure Cognitive Services",
                summary="Integrate speech recognition and synthesis into applications",
                url="https://learn.microsoft.com/en-us/training/modules/create-speech-enabled-apps-azure-cognitive-services/",
                duration_minutes=95,
                level="Intermediate",
                unit_count=12
            ),
            Module(
                uid="learn.azure.create-language-understanding-solution",
                title="Create a Language Understanding solution",
                summary="Build conversational AI applications with LUIS and Bot Framework",
                url="https://learn.microsoft.com/en-us/training/modules/create-language-understanding-solution/",
                duration_minutes=135,
                level="Advanced",
                unit_count=17
            ),
            Module(
                uid="learn.azure.build-qna-solution",
                title="Build a QnA solution",
                summary="Create intelligent Q&A bots using QnA Maker and Azure Bot Service",
                url="https://learn.microsoft.com/en-us/training/modules/build-qna-solution/",
                duration_minutes=85,
                level="Intermediate",
                unit_count=11
            )
        ]
    
    def _get_solution_architect_modules(self) -> List[Module]:
        """AZ-305 Azure Solutions Architect Expert modules."""
        return [
            Module(
                uid="learn.azure.design-governance-solution",
                title="Design governance and compliance solutions",
                summary="Architect governance frameworks, policies, and compliance strategies for Azure environments",
                url="https://learn.microsoft.com/en-us/training/modules/design-governance-solution/",
                duration_minutes=120,
                level="Expert",
                unit_count=15
            ),
            Module(
                uid="learn.azure.design-compute-solution",
                title="Design compute solutions",
                summary="Architect scalable compute solutions using Azure VMs, containers, and serverless technologies",
                url="https://learn.microsoft.com/en-us/training/modules/design-compute-solution/",
                duration_minutes=110,
                level="Expert",
                unit_count=14
            ),
            Module(
                uid="learn.azure.design-network-solutions",
                title="Design network solutions",
                summary="Architect hybrid and cloud networking solutions for connectivity and security",
                url="https://learn.microsoft.com/en-us/training/modules/design-network-solutions/",
                duration_minutes=130,
                level="Expert",
                unit_count=16
            ),
            Module(
                uid="learn.azure.design-storage-solution",
                title="Design storage solutions",
                summary="Architect data storage solutions for different workloads and performance requirements",
                url="https://learn.microsoft.com/en-us/training/modules/design-storage-solution/",
                duration_minutes=100,
                level="Expert",
                unit_count=13
            ),
            Module(
                uid="learn.azure.design-data-integration-solution",
                title="Design data integration solutions",
                summary="Architect data pipelines, ETL processes, and data integration strategies",
                url="https://learn.microsoft.com/en-us/training/modules/design-data-integration-solution/",
                duration_minutes=115,
                level="Expert",
                unit_count=14
            ),
            Module(
                uid="learn.azure.design-authentication-authorization-solution",
                title="Design authentication and authorization solutions",
                summary="Architect identity and access management solutions for enterprise environments",
                url="https://learn.microsoft.com/en-us/training/modules/design-authentication-authorization-solution/",
                duration_minutes=95,
                level="Expert",
                unit_count=12
            ),
            Module(
                uid="learn.azure.design-logging-monitoring-solution",
                title="Design logging and monitoring solutions",
                summary="Architect comprehensive monitoring, alerting, and observability solutions",
                url="https://learn.microsoft.com/en-us/training/modules/design-logging-monitoring-solution/",
                duration_minutes=85,
                level="Expert",
                unit_count=11
            )
        ]

    def _get_ai_edge_engineer_modules(self) -> List[Module]:
        """AI Edge Engineer modules (Emerging field with IoT focus)."""
        return [
            Module(
                uid="learn.azure.introduction-to-iot-edge",
                title="Introduction to Azure IoT Edge",
                summary="Learn the fundamentals of edge computing and Azure IoT Edge platform",
                url="https://learn.microsoft.com/en-us/training/modules/introduction-to-iot-edge/",
                duration_minutes=60,
                level="Beginner",
                unit_count=8
            ),
            Module(
                uid="learn.azure.deploy-ai-models-to-iot-edge",
                title="Deploy AI models to IoT Edge devices",
                summary="Learn to deploy machine learning models at the edge using Azure IoT Edge",
                url="https://learn.microsoft.com/en-us/training/modules/deploy-ai-models-to-iot-edge/",
                duration_minutes=90,
                level="Intermediate",
                unit_count=12
            ),
            Module(
                uid="learn.azure.implement-computer-vision-iot-edge",
                title="Implement computer vision at the edge",
                summary="Build edge-based computer vision solutions for real-time processing",
                url="https://learn.microsoft.com/en-us/training/modules/implement-computer-vision-iot-edge/",
                duration_minutes=105,
                level="Intermediate",
                unit_count=14
            ),
            Module(
                uid="learn.azure.configure-iot-edge-device-management",
                title="Configure IoT Edge device management",
                summary="Manage and monitor IoT Edge devices at scale in production environments",
                url="https://learn.microsoft.com/en-us/training/modules/configure-iot-edge-device-management/",
                duration_minutes=80,
                level="Advanced",
                unit_count=10
            ),
            Module(
                uid="learn.azure.optimize-ai-performance-edge-devices",
                title="Optimize AI performance on edge devices",
                summary="Techniques for optimizing AI model performance and resource usage at the edge",
                url="https://learn.microsoft.com/en-us/training/modules/optimize-ai-performance-edge-devices/",
                duration_minutes=75,
                level="Advanced",
                unit_count=9
            )
        ]
    

    
    def _get_coming_soon_modules(self, cert_uid: str) -> List[Module]:
        """Generate 'coming soon' modules for certifications we plan to support."""
        cert_name = cert_uid.replace('certification.', '').replace('-', ' ').title()
        
        return [
            Module(
                uid=f"coming-soon-{cert_uid}",
                title=f"{cert_name} - Coming Soon!",
                summary=f"We're actively working on curated content for {cert_name}. Check back soon for high-quality, podcast-ready modules.",
                url=f"/coming-soon/{cert_uid}",
                duration_minutes=0,
                level="Info",
                unit_count=1
            )
        ]
    
    def _get_azure_administrator_modules(self) -> List[Module]:
        """AZ-104 Azure Administrator modules."""
        return [
            Module(
                uid="learn.azure.manage-azure-identities-governance",
                title="Manage Azure identities and governance",
                summary="Manage Azure Active Directory objects and role-based access control",
                url="https://learn.microsoft.com/en-us/training/modules/manage-azure-identities-governance/",
                duration_minutes=90,
                level="Intermediate",
                unit_count=12
            ),
            Module(
                uid="learn.azure.implement-manage-storage",
                title="Implement and manage storage",
                summary="Configure Azure storage accounts, blob storage, and file services",
                url="https://learn.microsoft.com/en-us/training/modules/implement-manage-storage/",
                duration_minutes=85,
                level="Intermediate",
                unit_count=11
            ),
            Module(
                uid="learn.azure.deploy-manage-azure-compute-resources",
                title="Deploy and manage Azure compute resources",
                summary="Create and configure virtual machines, containers, and web apps",
                url="https://learn.microsoft.com/en-us/training/modules/deploy-manage-azure-compute-resources/",
                duration_minutes=100,
                level="Intermediate",
                unit_count=13
            ),
            Module(
                uid="learn.azure.configure-manage-virtual-networks",
                title="Configure and manage virtual networks",
                summary="Implement virtual networks, subnets, and network security groups",
                url="https://learn.microsoft.com/en-us/training/modules/configure-manage-virtual-networks/",
                duration_minutes=95,
                level="Intermediate",
                unit_count=12
            ),
            Module(
                uid="learn.azure.monitor-backup-azure-resources",
                title="Monitor and backup Azure resources",
                summary="Configure monitoring, alerting, and backup for Azure resources",
                url="https://learn.microsoft.com/en-us/training/modules/monitor-backup-azure-resources/",
                duration_minutes=80,
                level="Intermediate",
                unit_count=10
            )
        ]
    
    def _get_azure_developer_modules(self) -> List[Module]:
        """AZ-204 Azure Developer modules."""
        return [
            Module(
                uid="learn.azure.develop-azure-compute-solutions",
                title="Develop Azure compute solutions",
                summary="Create Azure Functions, Web Apps, and container-based solutions",
                url="https://learn.microsoft.com/en-us/training/modules/develop-azure-compute-solutions/",
                duration_minutes=120,
                level="Intermediate",
                unit_count=15
            ),
            Module(
                uid="learn.azure.develop-azure-storage-solutions",
                title="Develop for Azure storage",
                summary="Implement solutions using Cosmos DB, blob storage, and Azure SQL",
                url="https://learn.microsoft.com/en-us/training/modules/develop-azure-storage-solutions/",
                duration_minutes=110,
                level="Intermediate",
                unit_count=14
            ),
            Module(
                uid="learn.azure.implement-azure-security",
                title="Implement Azure security",
                summary="Secure applications using Key Vault, Managed Identity, and authentication",
                url="https://learn.microsoft.com/en-us/training/modules/implement-azure-security/",
                duration_minutes=95,
                level="Intermediate",
                unit_count=12
            ),
            Module(
                uid="learn.azure.monitor-troubleshoot-optimize-azure-solutions",
                title="Monitor, troubleshoot, and optimize Azure solutions",
                summary="Implement logging, caching, and performance optimization",
                url="https://learn.microsoft.com/en-us/training/modules/monitor-troubleshoot-optimize-azure-solutions/",
                duration_minutes=85,
                level="Intermediate",
                unit_count=11
            ),
            Module(
                uid="learn.azure.connect-to-consume-azure-services",
                title="Connect to and consume Azure services",
                summary="Implement API Management, Event Grid, and Service Bus messaging",
                url="https://learn.microsoft.com/en-us/training/modules/connect-to-consume-azure-services/",
                duration_minutes=100,
                level="Advanced",
                unit_count=13
            )
        ]
    
    def _get_az900_basic_modules(self) -> List[Module]:
        """Basic AZ-900 modules for when API fails."""
        # Just redirect to our more comprehensive fundamentals modules
        return self._get_azure_fundamentals_modules()
    
    def _process_module_details(self, module_data: Dict) -> ModuleDetails:
        """Process module data from API into ModuleDetails."""
        units = []
        
        for unit_data in module_data.get('units', []):
            unit = Unit(
                title=unit_data.get('title', ''),
                url=unit_data.get('url', ''),
                type=unit_data.get('type', 'content'),
                duration_minutes=unit_data.get('durationInMinutes', 5)
            )
            
            # Ensure URL is absolute
            if unit.url and not unit.url.startswith('http'):
                unit.url = f"{self.base_url}{unit.url}"
            
            units.append(unit)
        
        return ModuleDetails(
            uid=module_data.get('uid', ''),
            title=module_data.get('title', 'Unknown Module'),
            summary=module_data.get('summary', 'No description available'),
            url=module_data.get('url', ''),
            duration_minutes=module_data.get('durationInMinutes', 30),
            level=module_data.get('level', 'Unknown'),
            rating=module_data.get('rating', {}).get('average', 0),
            units=units
        )
    
    def _get_basic_module_details(self, module: Module) -> ModuleDetails:
        """Create module details for basic modules."""
        # Create standard units for basic modules with knowledge checks
        units = [
            Unit(title="Introduction", url=f"{module.url}1-introduction/", type="introduction", duration_minutes=5),
            Unit(title="Core Concepts", url=f"{module.url}2-core-concepts/", type="content", duration_minutes=15),
            Unit(title="Practical Examples", url=f"{module.url}3-examples/", type="content", duration_minutes=10),
            Unit(title="Advanced Topics", url=f"{module.url}4-advanced/", type="content", duration_minutes=10),
            Unit(title="Knowledge check", url=f"{module.url}5-knowledge-check/", type="knowledge-check", duration_minutes=5),
            Unit(title="Summary", url=f"{module.url}6-summary/", type="summary", duration_minutes=5)
        ]
        
        return ModuleDetails(
            uid=module.uid,
            title=module.title,
            summary=module.summary,
            url=module.url,
            duration_minutes=module.duration_minutes,
            level=module.level,
            rating=4.2,  # Good default rating
            units=units
        )


def create_clean_catalog_service() -> CleanCatalogService:
    """Factory function to create a clean catalog service instance."""
    return CleanCatalogService()
