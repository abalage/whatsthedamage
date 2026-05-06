# Instructions for AI Agents

This document enables AI coding agents to be immediately productive in the `whatsthedamage` codebase.

`whatsthedamage` processes bank transaction CSV exports, categorizes them using regular expressions or Machine Learning models, and applies statistical analysis.

## Quick Start Guide

### User Interactions
- Ask questions if unsure about implementation details or design choices
- Answer in the same language as the question
- Use English for generated content (code, comments, documentation)
- Do not create summary Markdown files unless it is explicitly asked for.
- Local terminal uses ZSH and not BASH. Keep in mind when executing shell commands.
- In case you need a temporary directory create one in project root instead of using /tmp directory.

### Project Overview
- **Decoupled architecture**: Backend and frontend are independent, communicating via REST API v2
- **Backend**: Python (Flask) located in `src/whatsthedamage/` - API-only, no server-side templates
- **Frontend**: Vue 3 SPA with TypeScript, located in `frontend/` at project root
- **Interfaces**: CLI, REST API v2, and independent Frontend SPA

## Project Structure

```
whatsthedamage/
├── config/                  # Configuration files
├── frontend/                # Vue 3 SPA Frontend (independent of backend)
│   ├── src/                 # Frontend sources (TypeScript/Vue)
│   │   ├── components/      # Reusable Vue components
│   │   ├── pages/           # Page-level components (routes)
│   │   ├── stores/          # Pinia state management
│   │   ├── router/          # Vue Router configuration
│   │   ├── translations/    # Language translations
│   │   ├── js/              # Utility functions and API client
│   │   └── types/           # TypeScript type definitions
│   ├── public/              # Static content
│   ├── dist/                # Production build output
│   ├── package.json
│   ├── vite.config.js
│   └── tsconfig.json
├── src/whatsthedamage/
│   ├── api/                 # REST API endpoints (v2)
│   ├── config/              # Configuration classes
│   ├── controllers/         # Request handling
│   │   └── frontend_routes.py # Frontend SPA catch-all routes
│   ├── models/              # Data models and processing
│   ├── scripts/             # ML training and utilities
│   ├── services/            # Business logic services
│   ├── static/              # Backend static assets (ML models, etc.)
│   ├── utils/               # Utility functions
│   ├── view/                # Presentation layer (legacy CLI output only)
│   │   └── static/          # Flask static files (frontend build output for integrated mode)
│   └── uploads/             # File uploads
└── tests/                   # Backend tests
```

## Architecture Patterns

- **Layered Architecture**: Clear separation of concerns with Presentation (CLI/Frontend), API, Service, Model, Configuration, and Utility layers
- **MVC Architecture**: Model-View-Controller pattern
- **Service Layer**: Business logic isolated in services (ProcessingService, ValidationService, MLService, ResponseFormattingService, IdMappingService, DrilldownService, TextCorrectionService, SmoteService, etc.)
- **Dependency Injection**: Services injected into controllers
  - **CLI**: Uses `ServiceContainer` from `service_factory.py`
  - **Flask**: Uses `app.extensions` dictionary
- **API-First Design**: Backend exposes REST API v2 as the sole interface for frontend communication
- **SOLID Principles**: Clean OOP design
  - **Single Responsibility Principle (SRP)**: A class should have only one reason to change, meaning it should have only one job or responsibility.
  - **Open/Closed Principle (OCP)**: Software entities (classes, modules, functions) should be open for extension but closed for modification. You should be able to add new functionality without altering existing code.
  - **Liskov Substitution Principle (LSP)**: Objects of a superclass should be replaceable with objects of its subclasses without breaking the application. Subclasses should extend the behavior of the parent class, not restrict it.
  - **Interface Segregation Principle (ISP)**: Clients should not be forced to depend on interfaces they do not use. It’s better to have many small, specific interfaces than one large, general-purpose interface.
  - **Dependency Inversion Principle (DIP)**: High-level modules should not depend on low-level modules. Both should depend on abstractions (e.g., interfaces). Abstractions should not depend on details; details should depend on abstractions.
- **DRY Principle**: Don't Repeat Yourself

## Tooling & Dependencies

- **Python**: Dependencies in `pyproject.toml`, use `make compile-deps`
- **JavaScript**: Dependencies in `frontend/package.json`
- **Node.js**: Version 24+ with ESM modules
- **Testing**: Vitest (frontend), pytest (backend)
- **Linting**: Ruff (Python), ESLint (JavaScript/TypeScript)
- **Type Checking**: mypy (Python), TypeScript compiler
- **Frontend Framework**: Vue 3 with Composition API
- **Frontend State Management**: Pinia
- **Frontend Routing**: Vue Router 4
- **Frontend Build Tool**: Vite 8
- **Data Grid**: DataTables.net 2.3.x with Bootstrap 5 integration

## Development Workflows

### Build & Run
```bash
# Backend only
make backend  # Flask development server
# Production: use gunicorn (see gunicorn_conf.py)

# Frontend only
make frontend  # Start Vite development server

# Full stack (backend + frontend in development mode)
make dev       # Set up development environment (Python venv + npm dependencies)

# Production build
make frontend-build:prod  # Build production frontend assets
make build                 # Full stack build (Python + JavaScript)
```

### Common Commands
```bash
source .venv/bin/activate         # Activate virtual env
tox -e lint                       # Python linting from virtual env
tox -e type                       # Type checking from virtual env
pytest                            # Run backend tests from virtual env
make test-frontend                # Run frontend tests
make docs                         # Generate documentation
make lang                         # Extract translatable texts
```

### Deployment Modes
- **Integrated**: Backend serves frontend from `view/static/dist/` via `frontend_routes.py` catch-all route
- **Standalone**: Frontend hosted separately on static hosting; backend API must be CORS-enabled
- **Development**: Vite dev server (port 3000) with `/api` proxy to `http://localhost:5000/api/v2`

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
- **Trailing whitespaces**: Remove trailing whitespaces

### JavaScript/TypeScript
- **Framework**: Vue 3 with Composition API and `<script setup>` syntax
- **Type System**: TypeScript 5.x with strict mode
- **State Management**: Pinia stores (form, locale, statistical, translations, feedback)
- **Routing**: Vue Router 4 for client-side navigation
- **Build Tool**: Vite 8 with ESM modules and HMR
- **Data Grid**: DataTables.net 2.3.x with Bootstrap 5 integration
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
- **API Communication**: Use `/api/v2` base URL or `VITE_API_BASE_URL` environment variable

## Testing Guidelines

- **Backend**: pytest, place tests in `tests/` directory. Use fixtures.
- **Frontend**: Vitest, place tests in `frontend/test/`
- **Coverage**: Write tests for all new features/bug fixes
- **Quality**: Ensure tests cover edge cases and error handling
- **Documentation**: Include docstrings explaining test cases
- The tests should cover what is implemented without being backward compatible with cases the tests currently cover.

## Documentation

- **Update**: README.md and ARCHITECTURE.md for new features or after making significant changes
- **Generate**: `make docs` for Sphinx documentation from docstrings
- **Localization**: Use `make lang` to extract translatable texts. Translation is done manually by developer. (English, Hungarian)
- **Format**: Keep all documentation in English

## Security Considerations

- **Data Protection**: Never log account numbers, personal info, or secrets
- **Input Validation**: Validate all user and file inputs
- **Resource Management**: Close file handles promptly
- **Error Handling**: Don't expose internal errors or stack traces
- **File Uploads**: Validate MIME types and extensions
- **CORS**: Cross-Origin Resource Sharing enabled for frontend-backend communication; development CORS for `http://localhost:3000` and `http://127.0.0.1:3000`; production configurable via Flask-CORS
- **Model Loading**: joblib model loading can execute arbitrary code - only use trusted models

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
