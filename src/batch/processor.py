"""
Batch processing service for handling multiple Microsoft Learn URLs.

Processes entire learning paths or multiple units into podcasts.
"""

import asyncio
import uuid
from pathlib import Path
from typing import Dict, List, Callable, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from content.fetcher import MSLearnFetcher
from content.processor import ScriptProcessor
from audio import create_best_multivoice_tts_service
from utils.logger import get_logger

logger = get_logger(__name__)


class BatchProcessor:
    """Handles batch processing of Microsoft Learn URLs."""
    
    def __init__(self, config: Dict, progress_callback: Callable = None):
        """
        Initialize batch processor.
        
        Args:
            config: Configuration dictionary
            progress_callback: Optional callback for progress updates
        """
        self.config = config
        self.progress_callback = progress_callback
        
        # Initialize services (premium or standard)
        self.fetcher = MSLearnFetcher()
        self.processor = ScriptProcessor()
        self.tts_service = create_best_multivoice_tts_service(config)
        
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
    
    def process_urls_batch(self, urls: List[str], batch_name: str = None) -> Dict:
        """
        Process a batch of URLs into podcasts.
        
        Args:
            urls: List of Microsoft Learn URLs
            batch_name: Optional name for this batch
            
        Returns:
            Dictionary with batch results and individual podcast info
        """
        batch_id = str(uuid.uuid4())
        batch_name = batch_name or f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Starting batch processing: {batch_id}, URLs: {len(urls)}")
        
        # Initialize batch status
        batch_status = {
            'batch_id': batch_id,
            'batch_name': batch_name,
            'total_urls': len(urls),
            'status': 'processing',
            'progress': 0,
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'podcasts': [],
            'errors': [],
            'started_at': datetime.now().isoformat(),
        }
        
        # Progress callback for batch start
        if self.progress_callback:
            self.progress_callback(batch_status)
        
        # Process URLs with limited concurrency
        max_workers = min(3, len(urls))  # Limit concurrent processing
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(self._process_single_url, url, i, len(urls)): url 
                for i, url in enumerate(urls)
            }
            
            # Process completed tasks
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                
                try:
                    result = future.result()
                    
                    if result['success']:
                        batch_status['successful'] += 1
                        batch_status['podcasts'].append(result)
                        logger.info(f"Successfully processed: {url}")
                    else:
                        batch_status['failed'] += 1
                        batch_status['errors'].append({
                            'url': url,
                            'error': result.get('error', 'Unknown error')
                        })
                        logger.error(f"Failed to process: {url} - {result.get('error')}")
                
                except Exception as e:
                    batch_status['failed'] += 1
                    batch_status['errors'].append({
                        'url': url,
                        'error': str(e)
                    })
                    logger.error(f"Exception processing {url}: {e}")
                
                # Update progress
                batch_status['processed'] += 1
                batch_status['progress'] = int((batch_status['processed'] / len(urls)) * 100)
                
                # Progress callback for each completion
                if self.progress_callback:
                    self.progress_callback(batch_status)
        
        # Mark batch as completed
        batch_status['status'] = 'completed'
        batch_status['completed_at'] = datetime.now().isoformat()
        
        logger.info(f"Batch processing completed: {batch_status['successful']} successful, {batch_status['failed']} failed")
        
        # Final progress callback
        if self.progress_callback:
            self.progress_callback(batch_status)
        
        return batch_status
    
    def _process_single_url(self, url: str, index: int, total: int) -> Dict:
        """
        Process a single URL into a podcast.
        
        Args:
            url: Microsoft Learn URL
            index: Index in batch (for naming)
            total: Total number of URLs in batch
            
        Returns:
            Dictionary with processing result
        """
        try:
            logger.info(f"Processing URL {index + 1}/{total}: {url}")
            
            # Fetch content
            content = self.fetcher.fetch_module_content(url)
            
            if not content or not content.get('title') or not content.get('content'):
                return {
                    'success': False,
                    'url': url,
                    'error': 'Failed to fetch content or content is empty'
                }
            
            # Process into script
            script_result = self.processor.process_content_to_script(content)
            script = script_result.get('script', '')
            
            if not script:
                return {
                    'success': False,
                    'url': url,
                    'error': 'Failed to generate script'
                }
            
            # Generate safe filename
            safe_title = self._make_safe_filename(content['title'])
            output_name = f"{index+1:02d}_{safe_title}"
            
            # Save script
            script_path = self.output_dir / f"{output_name}_script.txt"
            script_path.write_text(script)
            
            # Generate audio
            audio_path = self.output_dir / f"{output_name}.wav"
            success = self.tts_service.synthesize_text(script, audio_path)
            
            if not success or not audio_path.exists():
                return {
                    'success': False,
                    'url': url,
                    'error': 'Failed to generate audio'
                }
            
            # Prepare podcast metadata
            podcast_metadata = {
                'title': content['title'],
                'source_url': url,
                'duration': script_result.get('estimated_duration', ''),
                'word_count': script_result.get('word_count', 0),
                'index': index + 1,
                'total': total
            }
            
            # Upload to Azure Blob Storage if available
            blob_info = None
            if self.blob_storage:
                try:
                    blob_info = self.blob_storage.upload_podcast(audio_path, podcast_metadata)
                    logger.info(f"Uploaded to Azure Blob Storage: {blob_info['blob_name']}")
                except Exception as e:
                    logger.warning(f"Failed to upload to blob storage: {e}")
            
            return {
                'success': True,
                'url': url,
                'title': content['title'],
                'local_audio_path': str(audio_path),
                'local_script_path': str(script_path),
                'word_count': script_result.get('word_count', 0),
                'estimated_duration': script_result.get('estimated_duration', ''),
                'file_size': audio_path.stat().st_size if audio_path.exists() else 0,
                'blob_info': blob_info,
                'index': index + 1
            }
            
        except Exception as e:
            logger.error(f"Error processing URL {url}: {e}")
            return {
                'success': False,
                'url': url,
                'error': str(e)
            }
    
    def extract_learning_path_urls(self, learning_path_url: str) -> List[str]:
        """
        Extract individual unit URLs from a learning path URL.
        
        Args:
            learning_path_url: URL of the learning path
            
        Returns:
            List of individual unit URLs
        """
        try:
            # This is a simplified implementation
            # In a real scenario, you'd need to parse the learning path page
            # to extract all unit URLs
            
            logger.info(f"Extracting URLs from learning path: {learning_path_url}")
            
            # For now, just return the provided URL
            # TODO: Implement actual learning path parsing
            if '/modules/' in learning_path_url:
                return [learning_path_url]
            
            # If it's a learning path, we'd need to scrape the page
            # and find all unit links
            return []
            
        except Exception as e:
            logger.error(f"Failed to extract learning path URLs: {e}")
            return []
    
    def _make_safe_filename(self, title: str) -> str:
        """Convert title to safe filename."""
        # Remove or replace unsafe characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_ "
        safe_title = "".join(c if c in safe_chars else "_" for c in title)
        
        # Replace spaces with underscores and limit length
        safe_title = safe_title.replace(' ', '_')[:50]
        
        # Remove consecutive underscores
        import re
        safe_title = re.sub(r'_{2,}', '_', safe_title)
        safe_title = safe_title.strip('_')
        
        return safe_title or "podcast"


def create_batch_processor(config: Dict, progress_callback: Callable = None) -> BatchProcessor:
    """
    Factory function to create batch processor.
    
    Args:
        config: Configuration dictionary
        progress_callback: Optional progress callback function
        
    Returns:
        Configured BatchProcessor instance
    """
    return BatchProcessor(config, progress_callback)
