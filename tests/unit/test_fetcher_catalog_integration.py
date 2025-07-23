"""
Tests for enhanced MSLearnFetcher with catalog integration.
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from content.fetcher import MSLearnFetcher, ContentFetchError


class TestMSLearnFetcherCatalogIntegration:
    """Test the enhanced MSLearnFetcher with catalog features."""
    
    def setup_method(self):
        """Setup test instance."""
        self.fetcher = MSLearnFetcher()
    
    def test_initialization_with_catalog_service(self):
        """Test that fetcher initializes with catalog service."""
        assert hasattr(self.fetcher, 'catalog_service')
        assert self.fetcher.catalog_service is not None
    
    @patch('content.fetcher.MSLearnFetcher.fetch_module_content')
    def test_fetch_content_from_catalog_item(self, mock_fetch):
        """Test fetching content from a catalog item."""
        # Mock the base fetch_module_content method
        mock_fetch.return_value = {
            'title': 'Test Module',
            'content': 'Test content here',
            'url': 'https://learn.microsoft.com/test'
        }
        
        # Test catalog item
        catalog_item = {
            'id': 'test-module-123',
            'title': 'Test Module',
            'url': 'https://learn.microsoft.com/test',
            'duration_minutes': 30,
            'products': ['azure'],
            'roles': ['developer'],
            'subjects': ['ai'],
            'rating': 4.5
        }
        
        # Fetch content from catalog item
        result = self.fetcher.fetch_content_from_catalog_item(catalog_item)
        
        # Verify the result includes both original content and catalog metadata
        assert result['title'] == 'Test Module'
        assert result['content'] == 'Test content here'
        assert result['url'] == 'https://learn.microsoft.com/test'
        assert result['catalog_id'] == 'test-module-123'
        assert result['duration_minutes'] == 30
        assert result['products'] == ['azure']
        assert result['roles'] == ['developer']
        assert result['subjects'] == ['ai']
        assert result['rating'] == 4.5
        
        # Verify the base method was called with the URL
        mock_fetch.assert_called_once_with('https://learn.microsoft.com/test')
    
    def test_fetch_content_from_catalog_item_no_url(self):
        """Test error handling when catalog item has no URL."""
        catalog_item = {
            'id': 'test-module-123',
            'title': 'Test Module',
            # No URL provided
        }
        
        with pytest.raises(ContentFetchError) as exc_info:
            self.fetcher.fetch_content_from_catalog_item(catalog_item)
        
        assert "No URL provided" in str(exc_info.value)
    
    @patch('content.fetcher.MSLearnFetcher.fetch_content_from_catalog_item')
    def test_fetch_learning_path_content(self, mock_fetch_item):
        """Test fetching content from a learning path."""
        # Mock the catalog service to return test modules
        mock_modules = [
            {
                'id': 'module-1',
                'title': 'Module 1',
                'url': 'https://learn.microsoft.com/module-1'
            },
            {
                'id': 'module-2', 
                'title': 'Module 2',
                'url': 'https://learn.microsoft.com/module-2'
            }
        ]
        
        self.fetcher.catalog_service.get_learning_path_modules = Mock(return_value=mock_modules)
        
        # Mock fetch_content_from_catalog_item to return test content
        mock_fetch_item.side_effect = [
            {
                'title': 'Module 1',
                'content': 'Content for module 1',
                'url': 'https://learn.microsoft.com/module-1'
            },
            {
                'title': 'Module 2',
                'content': 'Content for module 2', 
                'url': 'https://learn.microsoft.com/module-2'
            }
        ]
        
        # Fetch learning path content
        results = self.fetcher.fetch_learning_path_content('test-learning-path')
        
        # Verify results
        assert len(results) == 2
        assert results[0]['title'] == 'Module 1'
        assert results[1]['title'] == 'Module 2'
        
        # Verify catalog service was called
        self.fetcher.catalog_service.get_learning_path_modules.assert_called_once_with('test-learning-path')
        
        # Verify fetch_content_from_catalog_item was called for each module
        assert mock_fetch_item.call_count == 2
    
    def test_fetch_learning_path_content_no_modules(self):
        """Test error handling when learning path has no modules."""
        # Mock catalog service to return empty list
        self.fetcher.catalog_service.get_learning_path_modules = Mock(return_value=[])
        
        with pytest.raises(ContentFetchError) as exc_info:
            self.fetcher.fetch_learning_path_content('empty-learning-path')
        
        assert "No modules found" in str(exc_info.value)
    
    @patch('content.fetcher.MSLearnFetcher.fetch_content_from_catalog_item')
    def test_fetch_learning_path_content_partial_failure(self, mock_fetch_item):
        """Test that learning path fetch continues even if some modules fail."""
        # Mock the catalog service to return test modules
        mock_modules = [
            {
                'id': 'module-1',
                'title': 'Module 1',
                'url': 'https://learn.microsoft.com/module-1'
            },
            {
                'id': 'module-2',
                'title': 'Module 2', 
                'url': 'https://learn.microsoft.com/module-2'
            },
            {
                'id': 'module-3',
                'title': 'Module 3',
                'url': 'https://learn.microsoft.com/module-3'
            }
        ]
        
        self.fetcher.catalog_service.get_learning_path_modules = Mock(return_value=mock_modules)
        
        # Mock fetch_content_from_catalog_item: first succeeds, second fails, third succeeds
        mock_fetch_item.side_effect = [
            {
                'title': 'Module 1',
                'content': 'Content for module 1',
                'url': 'https://learn.microsoft.com/module-1'
            },
            ContentFetchError("Module 2 failed"),  # This should be caught and continued
            {
                'title': 'Module 3',
                'content': 'Content for module 3',
                'url': 'https://learn.microsoft.com/module-3'
            }
        ]
        
        # Fetch learning path content
        results = self.fetcher.fetch_learning_path_content('test-learning-path')
        
        # Should get 2 successful modules despite 1 failure
        assert len(results) == 2
        assert results[0]['title'] == 'Module 1'
        assert results[1]['title'] == 'Module 3'
        
        # Verify all modules were attempted
        assert mock_fetch_item.call_count == 3
    
    @patch('content.fetcher.time.sleep')  # Mock sleep to speed up tests
    @patch('content.fetcher.MSLearnFetcher.fetch_content_from_catalog_item')
    def test_fetch_learning_path_respects_rate_limiting(self, mock_fetch_item, mock_sleep):
        """Test that learning path fetch includes rate limiting."""
        # Mock the catalog service to return test modules
        mock_modules = [
            {'id': 'module-1', 'title': 'Module 1', 'url': 'https://learn.microsoft.com/module-1'},
            {'id': 'module-2', 'title': 'Module 2', 'url': 'https://learn.microsoft.com/module-2'}
        ]
        
        self.fetcher.catalog_service.get_learning_path_modules = Mock(return_value=mock_modules)
        
        # Mock successful fetches
        mock_fetch_item.return_value = {
            'title': 'Test Module',
            'content': 'Test content',
            'url': 'https://learn.microsoft.com/test'
        }
        
        # Fetch learning path content
        results = self.fetcher.fetch_learning_path_content('test-learning-path')
        
        # Verify rate limiting sleep was called between modules
        assert mock_sleep.call_count == len(mock_modules)
        mock_sleep.assert_called_with(1)  # 1 second delay


if __name__ == "__main__":
    pytest.main([__file__])