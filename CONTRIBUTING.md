# Contributing to EdutainmentForge

## Coding Standards

### Naming Conventions

- **Files and Folders**: Use lowercase with underscores for multi-word names
- **Python Variables/Functions**: Use `snake_case`
- **Python Classes**: Use `PascalCase`
- **Python Constants**: Use `UPPER_SNAKE_CASE`

### Code Style

- Follow PEP 8 for Python code
- Use descriptive variable and function names
- Write docstrings for all public functions and classes
- Keep functions small and focused on a single responsibility

### Security Guidelines

- Never commit API keys or secrets to version control
- Use environment variables for configuration
- Validate all user inputs
- Use secure libraries for HTTP requests and data processing

### Testing Requirements

- Write unit tests for all new functions
- Maintain at least 80% code coverage
- Include integration tests for end-to-end workflows
- Test error conditions and edge cases

### GitHub Copilot Guidelines

When using GitHub Copilot:

1. Review all generated code for compliance with our standards
2. Ensure generated code follows our naming conventions
3. Verify security best practices are maintained
4. Test all AI-generated code thoroughly
5. Use descriptive comments to guide Copilot suggestions

### Pull Request Process

1. Create a feature branch from `main`
2. Make changes following our coding standards
3. Run tests and ensure they pass
4. Update documentation if needed
5. Submit pull request with clear description
6. Address review feedback promptly

### Development Setup

1. Install development dependencies: `pip install -r requirements-dev.txt`
2. Set up pre-commit hooks: `pre-commit install`
3. Configure your editor with our linting rules

## Architecture Guidelines

- Separate concerns into distinct modules (content, audio, ui)
- Use dependency injection for external services
- Implement proper error handling and logging
- Follow the repository's folder structure

## Questions?

Open an issue or contact the maintainers for clarification on any guidelines.
