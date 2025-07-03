#!/usr/bin/env python3
"""
Podcast Cleanup Script for EdutainmentForge

This script automatically cleans up old podcast files to manage storage costs
and keep the application running efficiently in Azure Container Apps.
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PodcastCleanup:
    """Manages cleanup of old podcast files."""
    
    def __init__(self, output_dir: str = "output", max_age_days: int = 7, max_files: int = 50):
        """
        Initialize podcast cleanup.
        
        Args:
            output_dir: Directory containing podcast files
            max_age_days: Maximum age of files to keep (in days)
            max_files: Maximum number of files to keep regardless of age
        """
        self.output_dir = Path(output_dir)
        self.max_age_days = max_age_days
        self.max_files = max_files
        self.cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        
    def get_podcast_files(self) -> List[tuple]:
        """
        Get list of podcast files with their modification times.
        
        Returns:
            List of tuples (file_path, modification_time)
        """
        files = []
        
        if not self.output_dir.exists():
            logger.warning(f"Output directory {self.output_dir} does not exist")
            return files
            
        for file_path in self.output_dir.glob("*.wav"):
            # Skip demo files and system files
            if any(skip in file_path.name.lower() for skip in ['demo_', 'test_', '.tmp']):
                continue
                
            try:
                mod_time = file_path.stat().st_mtime
                files.append((file_path, mod_time))
            except OSError as e:
                logger.warning(f"Cannot access file {file_path}: {e}")
                
        # Sort by modification time (oldest first)
        files.sort(key=lambda x: x[1])
        return files
    
    def get_old_files(self) -> List[Path]:
        """
        Get list of files older than the cutoff time.
        
        Returns:
            List of file paths to delete
        """
        files = self.get_podcast_files()
        old_files = []
        
        for file_path, mod_time in files:
            if mod_time < self.cutoff_time:
                old_files.append(file_path)
                
        return old_files
    
    def get_excess_files(self) -> List[Path]:
        """
        Get list of files that exceed the maximum file count.
        
        Returns:
            List of file paths to delete (oldest files)
        """
        files = self.get_podcast_files()
        
        if len(files) <= self.max_files:
            return []
            
        # Return the oldest files that exceed the limit
        excess_count = len(files) - self.max_files
        return [file_path for file_path, _ in files[:excess_count]]
    
    def delete_files(self, files_to_delete: List[Path]) -> int:
        """
        Delete the specified files.
        
        Args:
            files_to_delete: List of file paths to delete
            
        Returns:
            Number of files successfully deleted
        """
        deleted_count = 0
        total_size_freed = 0
        
        for file_path in files_to_delete:
            try:
                # Get file size before deletion
                file_size = file_path.stat().st_size
                
                # Delete the file
                file_path.unlink()
                
                deleted_count += 1
                total_size_freed += file_size
                
                logger.info(f"Deleted: {file_path.name} ({file_size / (1024*1024):.1f} MB)")
                
                # Also try to delete corresponding script file
                script_file = file_path.with_suffix('_script.txt')
                if script_file.exists():
                    script_file.unlink()
                    logger.info(f"Deleted script: {script_file.name}")
                    
            except OSError as e:
                logger.error(f"Failed to delete {file_path}: {e}")
                
        if deleted_count > 0:
            logger.info(f"Cleanup complete: {deleted_count} files deleted, "
                       f"{total_size_freed / (1024*1024):.1f} MB freed")
        
        return deleted_count
    
    def cleanup_by_age(self) -> int:
        """
        Clean up files older than max_age_days.
        
        Returns:
            Number of files deleted
        """
        logger.info(f"Cleaning up files older than {self.max_age_days} days")
        old_files = self.get_old_files()
        
        if not old_files:
            logger.info("No old files found")
            return 0
            
        logger.info(f"Found {len(old_files)} old files to delete")
        return self.delete_files(old_files)
    
    def cleanup_by_count(self) -> int:
        """
        Clean up excess files to stay under max_files limit.
        
        Returns:
            Number of files deleted
        """
        logger.info(f"Ensuring no more than {self.max_files} files exist")
        excess_files = self.get_excess_files()
        
        if not excess_files:
            logger.info("File count is within limits")
            return 0
            
        logger.info(f"Found {len(excess_files)} excess files to delete")
        return self.delete_files(excess_files)
    
    def get_stats(self) -> dict:
        """
        Get statistics about current podcast files.
        
        Returns:
            Dictionary with file statistics
        """
        files = self.get_podcast_files()
        
        if not files:
            return {
                'total_files': 0,
                'total_size_mb': 0,
                'oldest_file': None,
                'newest_file': None
            }
        
        total_size = sum(file_path.stat().st_size for file_path, _ in files)
        oldest_time = min(mod_time for _, mod_time in files)
        newest_time = max(mod_time for _, mod_time in files)
        
        return {
            'total_files': len(files),
            'total_size_mb': total_size / (1024 * 1024),
            'oldest_file': datetime.fromtimestamp(oldest_time).strftime('%Y-%m-%d %H:%M:%S'),
            'newest_file': datetime.fromtimestamp(newest_time).strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def run_cleanup(self, cleanup_type: str = 'both') -> dict:
        """
        Run the cleanup process.
        
        Args:
            cleanup_type: Type of cleanup ('age', 'count', or 'both')
            
        Returns:
            Dictionary with cleanup results
        """
        logger.info("Starting podcast cleanup")
        
        # Get initial stats
        initial_stats = self.get_stats()
        logger.info(f"Initial state: {initial_stats['total_files']} files, "
                   f"{initial_stats['total_size_mb']:.1f} MB")
        
        deleted_by_age = 0
        deleted_by_count = 0
        
        if cleanup_type in ['age', 'both']:
            deleted_by_age = self.cleanup_by_age()
            
        if cleanup_type in ['count', 'both']:
            deleted_by_count = self.cleanup_by_count()
            
        # Get final stats
        final_stats = self.get_stats()
        
        total_deleted = deleted_by_age + deleted_by_count
        size_freed = initial_stats['total_size_mb'] - final_stats['total_size_mb']
        
        logger.info(f"Cleanup complete: {total_deleted} files deleted, "
                   f"{size_freed:.1f} MB freed")
        logger.info(f"Final state: {final_stats['total_files']} files, "
                   f"{final_stats['total_size_mb']:.1f} MB")
        
        return {
            'deleted_by_age': deleted_by_age,
            'deleted_by_count': deleted_by_count,
            'total_deleted': total_deleted,
            'size_freed_mb': size_freed,
            'initial_stats': initial_stats,
            'final_stats': final_stats
        }


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up old podcast files')
    parser.add_argument('--output-dir', default='output',
                       help='Directory containing podcast files (default: output)')
    parser.add_argument('--max-age-days', type=int, default=7,
                       help='Maximum age of files to keep in days (default: 7)')
    parser.add_argument('--max-files', type=int, default=50,
                       help='Maximum number of files to keep (default: 50)')
    parser.add_argument('--cleanup-type', choices=['age', 'count', 'both'], default='both',
                       help='Type of cleanup to perform (default: both)')
    parser.add_argument('--stats-only', action='store_true',
                       help='Only show statistics, do not delete files')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be deleted without actually deleting')
    
    args = parser.parse_args()
    
    cleanup = PodcastCleanup(
        output_dir=args.output_dir,
        max_age_days=args.max_age_days,
        max_files=args.max_files
    )
    
    if args.stats_only:
        stats = cleanup.get_stats()
        print(f"Podcast Statistics:")
        print(f"  Total files: {stats['total_files']}")
        print(f"  Total size: {stats['total_size_mb']:.1f} MB")
        if stats['oldest_file']:
            print(f"  Oldest file: {stats['oldest_file']}")
            print(f"  Newest file: {stats['newest_file']}")
        return
    
    if args.dry_run:
        old_files = cleanup.get_old_files()
        excess_files = cleanup.get_excess_files()
        all_files_to_delete = list(set(old_files + excess_files))
        
        print(f"DRY RUN: Would delete {len(all_files_to_delete)} files:")
        for file_path in all_files_to_delete:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            print(f"  {file_path.name} ({size_mb:.1f} MB, {mod_time})")
        return
    
    # Run the actual cleanup
    results = cleanup.run_cleanup(args.cleanup_type)
    
    # Exit with error code if no files were found to process
    if results['initial_stats']['total_files'] == 0:
        logger.warning("No podcast files found")
        sys.exit(1)


if __name__ == '__main__':
    main()
