# GitHub Copilot Instructions for EdutainmentForge

## Project Context

This project converts Microsoft Learn content into edutainment-style podcasts with AI-enhanced multi-voice narration. We use Python as our primary language with a focus on clean, maintainable code and Azure cloud services.

## Coding Standards

- **Language**: Python 3.8+
- **Style**: Follow PEP 8 strictly
- **Naming**: Use snake_case for functions/variables, PascalCase for classes
- **Documentation**: Include docstrings for all public functions
- **Error Handling**: Use proper exception handling with specific exception types

## Architecture Patterns

- Separate content fetching, audio processing, and UI logic
- Use dependency injection for external services
- Implement proper logging throughout the application
- Follow the established folder structure in src/
- Cache audio segments for performance
- Support both single and multi-voice TTS

## Security Requirements

- Never hardcode API keys or secrets
- Always load credentials from environment variables
- Validate and sanitize all user inputs
- Use secure HTTP libraries (requests with SSL verification)
- Support Azure Key Vault for production secrets
- Use Azure Managed Identity when possible

## Required Libraries & Dependencies

### Core Dependencies
- **HTTP Requests**: `requests>=2.31.0` for web scraping
- **HTML Parsing**: `beautifulsoup4>=4.12.0` for content extraction
- **Environment Config**: `python-dotenv>=1.0.0` for .env file support
- **Web Framework**: `flask>=3.0.0` for UI and APIs
- **Audio Processing**: `pydub>=0.25.1` for audio manipulation
- **Production Server**: `gunicorn>=21.2.0` for deployment

### Azure Services
- **Azure Speech**: `azure-cognitiveservices-speech>=1.34.0` for TTS
- **Azure OpenAI**: `openai>=1.12.0` for AI script enhancement
- **TTS Fallback**: `pyttsx3>=2.90` for local development

### Testing Dependencies
- **Test Framework**: `pytest>=7.4.0` for unit tests
- **Mocking**: `pytest-mock>=3.11.0` for test mocking

### Standard Library Modules (No Installation Required)
- **pathlib** - Modern path handling
- **threading** - Background processing for web interface
- **uuid** - Unique ID generation for tracking
- **argparse** - Command-line argument parsing
- **tempfile** - Temporary file management for audio processing
- **json** - Data serialization and API responses
- **re** - Regular expressions for text processing and dialogue parsing
- **hashlib** - Content hashing for caching
- **urllib.parse** - URL parsing and manipulation
- **abc** - Abstract base classes for service interfaces
- **io** - Binary stream handling for audio files
- **os** - Operating system interface
- **sys** - System-specific parameters
- **time** - Time-related functions

## Code Generation Guidelines

When generating code:
1. Include proper error handling and logging
2. Add type hints where appropriate
3. Write accompanying unit tests
4. Use our established utility functions
5. Follow the single responsibility principle
6. Support both AI-enhanced and basic dialogue modes
7. Implement proper voice mapping for multi-speaker TTS

## Testing Expectations

- Generate unit tests for all new functions
- Include edge cases and error conditions
- Use descriptive test names that explain the scenario
- Mock external dependencies appropriately

## Example Code Style

```python
def fetch_learn_content(module_id: str) -> dict:
    """
    Fetch content from Microsoft Learn module.
    
    Args:
        module_id: The MS Learn module identifier
        
    Returns:
        Dictionary containing module content
        
    Raises:
        ContentFetchError: If content cannot be retrieved
    """
    try:
        # Implementation here
        pass
    except Exception as e:
        logger.error(f"Failed to fetch content for module {module_id}: {e}")
        raise ContentFetchError(f"Content fetch failed: {e}")
```

## AI Enhancement Guidelines

When working with the AI script enhancement feature:
- Always provide fallbacks when Azure OpenAI is unavailable
- Ensure enhanced scripts maintain proper dialogue format
- Balance conversation between Sarah and Mike (50/50 split)
- Handle table content with special dialogue enhancements
- Log all AI interactions for debugging

## Multi-Voice TTS Guidelines

- Use distinct voices for each speaker (Sarah: AriaNeural, Mike: DavisNeural)
- Parse dialogue scripts with proper speaker identification
- Add appropriate pauses between speaker segments
- Cache TTS service instances to avoid recreation
- Support fallback to single voice if multi-voice fails
- Use descriptive test names that explain the scenario
- Mock external dependencies appropriately

## Example Code Style

```python
def fetch_learn_content(module_id: str) -> dict:
    """
    Fetch content from Microsoft Learn module.
    
    Args:
        module_id: The MS Learn module identifier
        
    Returns:
        Dictionary containing module content
        
    Raises:
        ContentFetchError: If content cannot be retrieved
    """
    try:
        # Implementation here
        pass
    except Exception as e:
        logger.error(f"Failed to fetch content for module {module_id}: {e}")
        raise ContentFetchError(f"Content fetch failed: {e}")
```
