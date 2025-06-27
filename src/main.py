#!/usr/bin/env python3
"""
EdutainmentForge - Main Application Entry Point

Converts Microsoft Learn content into engaging podcast episodes.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path for imports
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

from utils.config import load_config
from utils.logger import setup_logger
from ui.cli import main as cli_main


def main():
    """Main application entry point."""
    # Setup logging
    logger = setup_logger()
    logger.info("Starting EdutainmentForge application")
    
    try:
        # Load configuration
        config = load_config()
        
        # Start the CLI interface
        cli_main(config)
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
