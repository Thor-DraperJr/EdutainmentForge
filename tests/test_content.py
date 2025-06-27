"""
Tests for content fetching and processing functionality.
"""

import pytest
from unittest.mock import Mock, patch
import requests

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from content import MSLearnFetcher, ContentFetchError, ScriptProcessor, create_sample_content


class TestMSLearnFetcher:
    """Test cases for MS Learn content fetcher."""
    
    def test_init(self):
        """Test fetcher initialization."""
        fetcher = MSLearnFetcher()
        assert fetcher.base_url == "https://docs.microsoft.com"
        assert hasattr(fetcher, 'session')
    
    def test_init_custom_base_url(self):
        """Test fetcher with custom base URL."""
        custom_url = "https://example.com"
        fetcher = MSLearnFetcher(base_url=custom_url)
        assert fetcher.base_url == custom_url
    
    @patch('content.fetcher.requests.Session.get')
    def test_fetch_module_content_success(self, mock_get):
        """Test successful content fetching."""
        # Mock response
        mock_response = Mock()
        mock_response.content = b"""
        <html>
            <head><title>Test Module</title></head>
            <body>
                <h1>Introduction to Testing</h1>
                <div class="content">
                    <p>This is a test module about testing.</p>
                    <p>It covers basic testing concepts.</p>
                </div>
            </body>
        </html>
        """
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        fetcher = MSLearnFetcher()
        result = fetcher.fetch_module_content("https://example.com/test-module")
        
        assert 'title' in result
        assert 'content' in result
        assert 'url' in result
        assert "Introduction to Testing" in result['title']
        assert "test module about testing" in result['content']
    
    @patch('content.fetcher.requests.Session.get')
    def test_fetch_module_content_network_error(self, mock_get):
        """Test content fetching with network error."""
        mock_get.side_effect = requests.RequestException("Network error")
        
        fetcher = MSLearnFetcher()
        
        with pytest.raises(ContentFetchError):
            fetcher.fetch_module_content("https://example.com/test-module")
    
    def test_get_sample_modules(self):
        """Test getting sample modules."""
        fetcher = MSLearnFetcher()
        modules = fetcher.get_sample_modules()
        
        assert isinstance(modules, list)
        assert len(modules) > 0
        
        for module in modules:
            assert 'title' in module
            assert 'url' in module
            assert 'description' in module


class TestScriptProcessor:
    """Test cases for script processor."""
    
    def test_init(self):
        """Test processor initialization."""
        processor = ScriptProcessor()
        assert hasattr(processor, 'intro_phrases')
        assert hasattr(processor, 'transition_phrases')
        assert hasattr(processor, 'conclusion_phrases')
    
    def test_process_content_to_script(self, sample_content):
        """Test content to script conversion."""
        processor = ScriptProcessor()
        result = processor.process_content_to_script(sample_content)
        
        assert 'title' in result
        assert 'script' in result
        assert 'word_count' in result
        assert 'estimated_duration' in result
        assert 'source_url' in result
        
        assert result['title'] == sample_content['title']
        assert result['word_count'] > 0
        assert len(result['script']) > len(sample_content['content'])  # Script should be longer
    
    def test_clean_content(self):
        """Test content cleaning."""
        processor = ScriptProcessor()
        
        dirty_content = """
        This is   a test    with
        
        
        multiple   spaces and https://example.com URLs.
        Also has email@example.com addresses.
        ```
        code block here
        ```
        And `inline code`.
        """
        
        clean = processor._clean_content(dirty_content)
        
        assert 'https://example.com' not in clean
        assert 'email@example.com' not in clean
        assert '[code example]' in clean
        assert '[code]' in clean
        assert '   ' not in clean  # Multiple spaces should be reduced
    
    def test_estimate_duration(self):
        """Test duration estimation."""
        processor = ScriptProcessor()
        
        # Test short content
        short_duration = processor._estimate_duration(100)  # 100 words
        assert 'seconds' in short_duration
        
        # Test medium content
        medium_duration = processor._estimate_duration(500)  # 500 words
        assert 'minutes' in medium_duration
        
        # Test long content
        long_duration = processor._estimate_duration(10000)  # 10000 words
        assert 'h' in long_duration and 'm' in long_duration


def test_create_sample_content():
    """Test sample content creation."""
    content = create_sample_content()
    
    assert 'title' in content
    assert 'content' in content
    assert 'url' in content
    
    assert len(content['content']) > 0
    assert content['title'] != ""
