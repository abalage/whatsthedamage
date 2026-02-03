# Instructions for AI Agents

This document enables AI coding agents to be immediately productive in the `whatsthedamage` codebase.

`whatsthedamage` processes bank transaction CSV exports, categorizes them using regular expressions or Machine Learning models, and applies statistical analysis.

## Quick Start Guide

### User Interactions
- Ask questions if unsure about implementation details or design choices
- Answer in the same language as the question
- Use English for generated content (code, comments, documentation)

### Project Overview
- **Monolithic layout**: Backend and frontend in the same repository
- **Backend**: Python (Flask) located in `src/whatsthedamage/`
- **Frontend**: TypeScript served by Flask, located in `src/whatsthedamage/view/frontend/`
- **Interfaces**: CLI, Web (Flask + TypeScript), and REST API

## Project Structure

```
whatsthedamage/
├── config/                  # Configuration files
├── src/whatsthedamage/
│   ├── api/                 # REST API endpoints
│   ├── config/              # Configuration classes
│   ├── controllers/         # Request handling
│   ├── models/              # Data models and processing
│   ├── scripts/             # ML training and utilities
│   ├── services/            # Business logic services
│   ├── static/              # Backend static assets
│   ├── utils/               # Utility functions
│   ├── view/                # Presentation layer
│   │   ├── frontend/        # TypeScript frontend
│   │   │   ├── src/         # Frontend sources
│   │   │   ├── test/        # Frontend tests
│   │   ├── static/          # Frontend static assets
│   │   └── templates/       # HTML templates
│   └── uploads/             # File uploads
└── tests/                   # Backend tests
```

## Architecture Patterns

- **MVC Architecture**: Model-View-Controller pattern
- **Service Layer**: Business logic isolated in services
- **Dependency Injection**: Services injected into controllers
  - **CLI**: Uses `ServiceContainer` from `service_factory.py`
  - **Flask**: Uses `app.extensions` dictionary
- **SOLID Principles**: Clean OOP design
- **DRY Principle**: Don't Repeat Yourself

## Tooling & Dependencies

- **Python**: Dependencies in `pyproject.toml`, use `make compile-deps`
- **JavaScript**: Dependencies in `src/whatsthedamage/view/frontend/package.json`
- **Node.js**: Version 24+ with ESM modules
- **Testing**: Vitest (frontend), pytest (backend)
- **Linting**: Ruff (Python), ESLint (JavaScript)
- **Type Checking**: mypy (Python), TypeScript compiler

## Development Workflows

### Build & Run
```bash
# Web Interface
make web  # Flask development server
# Production: use gunicorn (see gunicorn_conf.py)
```

### Common Commands
```bash
source .venv/bin/activate         # Activate virtual env
ruff check --fix src tests        # Python linting from virtual env
mypy src                          # Type checking from virtual env
pytest                            # Run backend tests from virtual env
make frontend ARG=test            # Run frontend tests
make docs                         # Generate documentation
make lang                         # Extract translatable texts
```

## Coding Guidelines

### General Principles
- **Readability first**: Prioritize clear, maintainable code
- **Self-documenting**: Use descriptive names for functions/variables
- **No placeholders**: Complete implementations only
- **Error handling**: Clear exception handling with meaningful messages
- **Security**: Never log sensitive data, validate all inputs

### Python Specific
- **PEP 8**: Follow Python style guide
- **Type hints**: Use `typing` module (avoid `Any`)
- **Docstrings**: Required for all public functions/classes (Sphinx format, PEP 257 conventions)
- **Line length**: Maximum 79 characters
- **Indentation**: 4 spaces per level
- **Imports**: Group by type, separate with blank lines

### JavaScript/TypeScript
- Use modern JavaScript with ES2022 features
- Use Node.js (24+) ESM modules
- Use Node.js built-in modules and avoid external dependencies where possible
- Ask the user if you require any additional dependencies before adding them
- Always use async/await for asynchronous code, and use 'node:util' promisify function to avoid callbacks
- Keep the code simple and maintainable
- Use descriptive variable and function names
- Do not add comments unless absolutely necessary, the code should be self-explanatory
- Never use `null`, always use `undefined` for optional values
- Prefer functions over classes

## Testing Guidelines

- **Backend**: pytest, place tests in `tests/` directory. Use fixtures.
- **Frontend**: Vitest, place tests in `src/whatsthedamage/view/frontend/test/`
- **Coverage**: Write tests for all new features/bug fixes
- **Quality**: Ensure tests cover edge cases and error handling
- **Documentation**: Include docstrings explaining test cases
- The tests should cover what is implemented without being backward compatible with cases the tests currently cover.

## Documentation

- **Update**: README.md and ARCHITECTURE.md for new features or after making significant changes
- **Generate**: `make docs` for Sphinx documentation from docstrings
- **Localization**: Use `make lang` to extract translatable texts. Translataion is done manually by developer. (English, Hungarian)
- **Format**: Keep all documentation in English

## Security Considerations

- **Data Protection**: Never log account numbers, personal info, or secrets
- **Input Validation**: Validate all user and file inputs
- **Resource Management**: Close file handles promptly
- **Error Handling**: Don't expose internal errors or stack traces
- **File Uploads**: Validate MIME types and extensions

## Example Code Documentation

```python
def calculate_area(radius: float) -> float:
    """
    Calculate the area of a circle given the radius.

    Parameters:
    radius (float): The radius of the circle.

    Returns:
    float: The area of the circle, calculated as π * radius^2.
    """
    import math
    return math.pi * radius ** 2