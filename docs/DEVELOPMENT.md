# EdutainmentForge Development Guide

This guide covers the development environment setup and workflow for EdutainmentForge.

## Development Environment Setup

### Prerequisites

- Python 3.8+
- Azure Speech Service API key
- Azure OpenAI API key (optional)
- ffmpeg (for audio processing)

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/edutainmentforge.git
   cd edutainmentforge
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

3. **Install development dependencies**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env file with your credentials
   ```

5. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

## Development Workflow

### Quick Commands

EdutainmentForge provides a Makefile with common development tasks:

```bash
# Install development dependencies
make install-dev

# Run tests
make test

# Format code
make format

# Run linting
make lint

# Run the application
make run
```

### Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=src --cov-report=html
```

### Code Quality Tools

The project uses these tools for code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pre-commit**: Git hooks for quality assurance

## Project Structure

```
edutainmentforge/
├── src/
│   ├── edutainmentforge/     # Package entry point
│   │   ├── __init__.py       # Package metadata
│   │   └── cli.py           # CLI entry point
│   ├── content/              # Content processing modules
│   │   ├── fetcher.py        # Microsoft Learn content fetching
│   │   ├── processor.py      # Content transformation to dialogue
│   │   └── ai_enhancer.py    # Azure OpenAI script enhancement
│   ├── audio/                # Multi-voice TTS services
│   │   ├── tts.py           # Core TTS service with Azure integration
│   │   └── multivoice_tts.py # Multi-voice coordination
│   ├── batch/                # Batch processing utilities
│   │   └── processor.py      # Batch URL processing
│   └── utils/                # Core utilities
│       ├── cache.py          # Audio caching system
│       ├── config.py         # Environment & Key Vault configuration
│       ├── keyvault.py       # Azure Key Vault integration
│       └── logger.py         # Logging configuration
├── tests/                    # Comprehensive test suite
│   ├── unit/                 # Unit tests with mocking
│   └── integration/          # Integration tests (including Key Vault)
```

## Testing Guidelines

### Test Cleanup Guidelines

Always clean up resources and temporary files after tests:

```python
import tempfile
import pytest
from pathlib import Path

class TestAudioGeneration:
    def setup_method(self):
        """Setup test environment before each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = []
    
    def teardown_method(self):
        """Clean up after each test"""
        # Clean up temporary audio files
        for file_path in self.test_files:
            if Path(file_path).exists():
                Path(file_path).unlink()
        
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Clear cache if used
        from src.utils.cache import clear_test_cache
        clear_test_cache()
```

### Azure Service Testing

- **Never use production resources** in automated tests
- **Mock Azure services** using pytest-mock or similar
- **Use test doubles** for expensive operations (TTS, AI enhancement)
- **Environment isolation** - use separate test configurations

## Pull Request Guidelines

1. Ensure code passes all tests
2. Update documentation if needed
3. Follow coding standards (PEP 8)
4. Include tests for new functionality
5. Keep PRs focused on a single change
