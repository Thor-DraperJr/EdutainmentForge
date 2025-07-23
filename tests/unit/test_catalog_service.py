"""
Tests for Microsoft Learn Catalog Service integration.
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from content.catalog import MSLearnCatalogService, CatalogAPIError


class TestMSLearnCatalogService:
    """Test the Microsoft Learn Catalog Service."""
    
    def setup_method(self):
        """Setup test instance."""
        self.service = MSLearnCatalogService()
    
    def test_initialization(self):
        """Test service initialization."""
        assert self.service.base_url == "https://learn.microsoft.com"
        assert self.service.api_base == "https://learn.microsoft.com/api/catalog"
        assert self.service.session is not None
    
    @patch('content.catalog.requests.Session.get')
    def test_search_content_success(self, mock_get):
        """Test successful content search."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'count': 2,
            'modules': [
                {
                    'uid': 'test-module-1',
                    'title': 'Test Module 1',
                    'summary': 'Test summary 1',
                    'url': '/training/modules/test-1',
                    'type': 'module',
                    'durationInMinutes': 30,
                    'products': ['azure'],
                    'roles': ['developer'],
                    'subjects': ['ai'],
                    'levels': ['beginner']
                },
                {
                    'uid': 'test-module-2',
                    'title': 'Test Module 2',
                    'summary': 'Test summary 2',
                    'url': '/training/modules/test-2',
                    'type': 'module',
                    'durationInMinutes': 45,
                    'products': ['azure'],
                    'roles': ['developer'],
                    'subjects': ['ai'],
                    'levels': ['intermediate']
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Test search
        results = self.service.search_content(query="test", product="azure")
        
        # Verify results
        assert results['total_count'] == 2
        assert len(results['results']) == 2
        assert results['results'][0]['title'] == 'Test Module 1'
        assert results['results'][0]['url'] == 'https://learn.microsoft.com/training/modules/test-1'
        assert results['query_info']['query'] == 'test'
        assert results['query_info']['filters']['product'] == 'azure'
    
    @patch('content.catalog.requests.Session.get')
    def test_search_content_api_failure_uses_fallback(self, mock_get):
        """Test that API failure uses fallback results."""
        # Mock API failure
        mock_get.side_effect = Exception("API Error")
        
        # Test search - should use fallback
        results = self.service.search_content(query="ai")
        
        # Verify fallback results are returned
        assert 'total_count' in results
        assert 'results' in results
        assert len(results['results']) > 0
        # Should find AI-related modules in fallback
        ai_modules = [r for r in results['results'] if 'ai' in r['title'].lower()]
        assert len(ai_modules) > 0
    
    def test_search_content_with_filters(self):
        """Test search with various filters using fallback."""
        # Test with product filter
        results = self.service.search_content(product="azure")
        assert all('azure' in item['products'] for item in results['results'])
        
        # Test with role filter
        results = self.service.search_content(role="ai-engineer")
        assert all('ai-engineer' in item['roles'] for item in results['results'])
        
        # Test with topic filter
        results = self.service.search_content(topic="artificial-intelligence")
        assert all('artificial-intelligence' in item['subjects'] for item in results['results'])
    
    def test_get_learning_path_modules_fallback(self):
        """Test getting learning path modules using fallback."""
        modules = self.service.get_learning_path_modules("test-path-123")
        
        # Should return fallback modules
        assert isinstance(modules, list)
        assert len(modules) > 0
        assert all('title' in module for module in modules)
        assert all('url' in module for module in modules)
    
    def test_get_catalog_facets_fallback(self):
        """Test getting catalog facets using fallback."""
        facets = self.service.get_catalog_facets()
        
        # Verify fallback facets structure
        assert 'products' in facets
        assert 'roles' in facets
        assert 'subjects' in facets
        assert 'levels' in facets
        
        # Verify each facet has expected structure
        for facet_type in ['products', 'roles', 'subjects', 'levels']:
            assert isinstance(facets[facet_type], list)
            if facets[facet_type]:
                assert 'id' in facets[facet_type][0]
                assert 'name' in facets[facet_type][0]
                assert 'count' in facets[facet_type][0]
    
    def test_process_catalog_item(self):
        """Test processing a catalog item."""
        test_item = {
            'uid': 'test-123',
            'title': 'Test Module',
            'summary': 'Test summary',
            'url': '/training/modules/test',
            'type': 'module',
            'durationInMinutes': 30,
            'products': ['azure'],
            'roles': ['developer'],
            'subjects': ['ai'],
            'levels': ['beginner'],
            'rating': {'average': 4.5},
            'lastModified': '2024-01-01T00:00:00Z'
        }
        
        processed = self.service._process_catalog_item(test_item)
        
        assert processed['id'] == 'test-123'
        assert processed['title'] == 'Test Module'
        assert processed['url'] == 'https://learn.microsoft.com/training/modules/test'
        assert processed['duration_minutes'] == 30
        assert processed['products'] == ['azure']
        assert processed['rating'] == 4.5
    
    def test_fallback_results_filtering(self):
        """Test that fallback results are properly filtered."""
        # Test query filtering
        results = self.service._get_fallback_results("machine learning", "modules", None, None, None)
        machine_learning_results = [r for r in results['results'] 
                                   if 'machine learning' in r['title'].lower() or 
                                      'machine learning' in r['summary'].lower()]
        assert len(machine_learning_results) > 0
        
        # Test product filtering
        results = self.service._get_fallback_results("", "modules", "azure", None, None)
        assert all('azure' in item['products'] for item in results['results'])
        
        # Test role filtering
        results = self.service._get_fallback_results("", "modules", None, "developer", None)
        assert all('developer' in item['roles'] for item in results['results'])


def test_create_catalog_service():
    """Test the catalog service factory function."""
    from content.catalog import create_catalog_service
    
    service = create_catalog_service()
    assert isinstance(service, MSLearnCatalogService)
    assert service.base_url == "https://learn.microsoft.com"


if __name__ == "__main__":
    pytest.main([__file__])