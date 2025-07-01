"""Command-line interface for EdutainmentForge."""

import sys
from pathlib import Path

# Add src to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import the existing CLI functionality
from podcast_cli import main

if __name__ == "__main__":
    main()
