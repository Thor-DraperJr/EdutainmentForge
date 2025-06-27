# GitHub Copilot Instructions for EdutainmentForge

## Project Context

This project converts Microsoft Learn content into edutainment-style podcasts. We use Python as our primary language with a focus on clean, maintainable code.

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

## Security Requirements

- Never hardcode API keys or secrets
- Always load credentials from environment variables
- Validate and sanitize all user inputs
- Use secure HTTP libraries (requests with SSL verification)

## Preferred Libraries

- **HTTP Requests**: `requests` library
- **Audio Processing**: `pydub` for audio manipulation
- **Text-to-Speech**: Azure Cognitive Services or similar
- **Web Framework**: `Flask` for simple APIs
- **Testing**: `pytest` for all tests
- **Environment**: `python-dotenv` for configuration

## Code Generation Guidelines

When generating code:
1. Include proper error handling and logging
2. Add type hints where appropriate
3. Write accompanying unit tests
4. Use our established utility functions
5. Follow the single responsibility principle

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
