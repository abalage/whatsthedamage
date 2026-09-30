# Instructions for AI Agents

This document enables AI coding agents to be immediately productive in the `whatsthedamage` codebase.

`whatsthedamage` processes bank transaction CSV exports, categorizes them using regular expressions or Machine Learning models, and applies statistical analysis.

## Quick Start Guide

### User Interactions
- Ask questions if unsure about implementation details or design choices
- Answer in the same language as the question
- Use English for generated content (code, comments, documentation)
- Do not create summary Markdown files unless it is explicitly asked for.
- Local terminal uses ZSH and not BASH.
- In case you need a temporary directory create one in project root instead of using /tmp directory.
- Never commit to git.

### Project Overview
- **Git**: monorepository.
- **Decoupled architecture**: Backend and frontend are independent, communicating via REST API v2
- **Backend**: Python (Flask) located in `src/whatsthedamage/` - API-only, no server-side templates
- **Frontend**: Vue 3 SPA with TypeScript, located in `frontend/` at project root
- **Interfaces**: CLI, REST API v2, and independent Frontend SPA
- **Persistence**: Relational database via SQLAlchemy 2.0 (default SQLite, configurable via `WHATSTHEDAMAGE_DATABASE_URI`), schema managed by Alembic migrations in `migrations/`
- **Authentication**: User accounts with Argon2 password hashing, DB-backed sessions, CSRF protection, and rate limiting; all transaction data is scoped to the authenticated user

## Project Structure

```
whatsthedamage/
├── config/                  # Configuration files
├── frontend/                # Vue 3 SPA Frontend (independent of backend)
│   ├── src/                 # Frontend sources (TypeScript/Vue)
│   │   ├── components/      # Reusable Vue components (auth, charts, data, layout)
│   │   ├── composables/     # Vue 3 composable functions
│   │   ├── config/          # Frontend configuration (auth, highlight)
│   │   ├── directives/      # Vue directives (popover)
│   │   ├── locales/         # gettext translation catalogs (.po/.mo)
│   │   ├── pages/           # Page-level components (routes)
│   │   ├── stores/          # Pinia state management
│   │   ├── router/          # Vue Router configuration (with auth guards)
│   │   ├── js/              # Utility functions and API client
│   │   └── types/           # TypeScript type definitions
│   ├── public/              # Static content
│   ├── dist/                # Production build output
│   ├── package.json
│   ├── vite.config.js
│   └── tsconfig.json
├── migrations/              # Alembic database migrations
├── scripts/                 # Build/utility scripts (string extraction)
├── src/whatsthedamage/
│   ├── api/                 # REST API endpoints (v2 + auth blueprint, auth decorators)
│   ├── config/              # Configuration classes (app, auth, database, ML, CSV profiles)
│   ├── controllers/         # Request handling
│   │   └── frontend_routes.py # Frontend SPA catch-all routes
│   ├── models/              # Data models: api (Pydantic contracts), database (SQLAlchemy entities), repositories (data access), domain (processing logic)
│   ├── services/            # Business logic services
│   ├── static/              # Backend static assets (ML models, etc.)
│   ├── utils/               # Utility functions
│   ├── view/                # Presentation layer (legacy CLI output only)
│   │   └── static/          # Flask static files (frontend build output for integrated mode)
│   └── uploads/             # File uploads
└── tests/                   # Backend tests
```

## Architecture Patterns

- **Layered Architecture**: Clear separation of concerns with Presentation (CLI/Frontend), API, Service, Model, Persistence, Configuration, and Utility layers
- **MVC Architecture**: Model-View-Controller pattern
- **Service Layer**: Business logic isolated in services (ProcessingService, ValidationService, MLService, ResponseFormattingService, AuthenticationService, TransactionPersistenceService, CorrectionService, etc.)
- **Repository Pattern**: All database access goes through repository classes in `models/repositories/`; services never issue SQLAlchemy queries directly
- **Dependency Injection**: Services injected into controllers
  - **CLI**: Uses `ServiceContainer` from `service_container.py`
  - **Flask**: Uses `app.extensions` dictionary
- **API-First Design**: Backend exposes REST API v2 as the sole interface for frontend communication
- **SOLID Principles**: Clean OOP design
  - **Single Responsibility Principle (SRP)**: A class should have only one reason to change, meaning it should have only one job or responsibility.
  - **Open/Closed Principle (OCP)**: Software entities (classes, modules, functions) should be open for extension but closed for modification. You should be able to add new functionality without altering existing code.
  - **Liskov Substitution Principle (LSP)**: Objects of a superclass should be replaceable with objects of its subclasses without breaking the application. Subclasses should extend the behavior of the parent class, not restrict it.
  - **Interface Segregation Principle (ISP)**: Clients should not be forced to depend on interfaces they do not use. It’s better to have many small, specific interfaces than one large, general-purpose interface.
  - **Dependency Inversion Principle (DIP)**: High-level modules should not depend on low-level modules. Both should depend on abstractions (e.g., interfaces). Abstractions should not depend on details; details should depend on abstractions.
- **DRY Principle**: Don't Repeat Yourself
- **Date formatting**: System dates should be formatted using the ISO 8601 standards, be in UTC time, and have the _at suffix. The codebase uses ISO 8601 date strings (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS) for all date exchange between backend and frontend.

## Tooling & Dependencies

- **Python**: Dependencies in `pyproject.toml`, use `make compile-deps`
- **JavaScript**: Dependencies in `frontend/package.json`
- **Node.js**: Version 24+ with ESM modules
- **Database**: SQLAlchemy 2.0 ORM, Alembic for migrations (`alembic.ini`, `migrations/`)
- **Testing**: Vitest (frontend), pytest (backend)
- **Linting**: Ruff (Python), ESLint (JavaScript/TypeScript)
- **Type Checking**: mypy (Python), TypeScript compiler
- **Frontend Framework**: Vue 3 with Composition API
- **Frontend State Management**: Pinia
- **Frontend Routing**: Vue Router 5 (with auth guards)
- **Frontend Build Tool**: Vite 8
- **Data Grid**: Custom `VueDataTable.vue` component (no DataTables.net/jQuery)
- **Charts**: chart.js with vue-chartjs
- **i18n**: vue3-gettext with gettext catalogs in `frontend/src/locales/`

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
make frontend-build  # Build production frontend assets (npm run build)
make build           # Full stack build (Python + JavaScript)

# Database migrations (after changing SQLAlchemy models)
alembic upgrade head                    # Apply pending migrations
alembic revision --autogenerate -m "…"  # Create a new migration
```

### Common Commands
```bash
source .venv/bin/activate         # Activate virtual env
tox -e lint                       # Python linting from virtual env
tox -e type                       # Type checking from virtual env
pytest                            # Run backend tests from virtual env
make frontend-test                # Run frontend tests (lint, type-check, knip, vitest)
make docs                         # Generate documentation
make lang                         # Extract and compile translatable texts
```

### Deployment Modes
- **Integrated**: Backend serves frontend from `view/static/dist/` via `frontend_routes.py` catch-all route
- **Standalone**: Frontend hosted separately on static hosting; backend API must be CORS-enabled
- **Development**: Vite dev server (port 3000) with `/api` proxy to `http://localhost:5000/api/v2`

### Post-Development Verification
After completing any development work, **you MUST run all quality checks and fix all reported errors before considering the task complete**. Do not stop until all errors are resolved.

Run the following commands in sequence:

```bash
# Full stack verification (recommended)
make test
```

Or run checks separately for more granular control:

```bash
# Backend quality checks
make lint             # Runs Ruff (Python linter) + mypy (type checker)
# OR individually:
tox -e lint           # Python linting with Ruff
tox -e type           # Python type checking with mypy

# Backend tests
pytest                # Run backend tests
# OR
make backend-test     # Same as above via tox

# Frontend quality checks (from frontend/ directory or via make)
make frontend-test    # Runs ESLint, TypeScript check, Knip, and Vitest
# OR individually from frontend/:
npm run lint          # ESLint for TypeScript/JavaScript/Vue
npm run type-check    # TypeScript compiler check
npm run knip          # Detect unused files and exports
npm run test          # Run Vitest tests
```

**Critical requirement**: All linter errors, type checker errors, and test failures must be fixed. Warnings should be addressed unless explicitly approved by the user. Do not proceed to commit or consider the task finished until all quality gates pass.

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
- **State Management**: Pinia stores (auth, categories, feedback, form, locale, pivot, statistical, theme)
- **Routing**: Vue Router 5 for client-side navigation with auth guards (`requiresAuth`/`requiresGuest`/`public` route meta)
- **Build Tool**: Vite 8 with ESM modules and HMR
- **Data Grid**: Use the existing `VueDataTable.vue` component; do not add DataTables.net/jQuery
- **Charts**: Use chart.js via the existing `BarChart`/`PieChart` components
- **i18n**: vue3-gettext; translatable strings go through gettext functions and catalogs in `src/locales/`
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
- **API Communication**: Use `/api/v2` base URL or `VITE_API_BASE_URL` environment variable; use the typed client in `src/js/api.ts`
- **Authentication**: Use the `auth` store for session state and CSRF tokens; do not store tokens yourself

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

- **Data Protection**: Never log account numbers, personal info, or secrets; never log passwords, session tokens, CSRF tokens, or recovery codes
- **User Isolation**: All transaction/result/correction queries must be scoped to the authenticated user (via repositories); protect state-changing endpoints with `require_authentication` / `require_auth_and_csrf` decorators
- **Passwords**: Hash with Argon2 via PasswordService; never handle plaintext passwords outside authentication flows
- **CSRF**: State-changing API requests require a CSRF token; fetch it via the auth store / `GET /api/v2/auth/csrf-token`
- **Rate Limiting**: Sensitive endpoints (login, register, reset) use RateLimitService; keep new auth endpoints rate-limited
- **Input Validation**: Validate all user and file inputs
- **Resource Management**: Close file handles and DB sessions promptly
- **Error Handling**: Don't expose internal errors or stack traces
- **File Uploads**: Validate MIME types and extensions
- **CORS**: Cross-Origin Resource Sharing enabled for frontend-backend communication; development CORS for `http://localhost:3000` and `http://127.0.0.1:3000`; production configurable via Flask-CORS
- **Model Loading**: skops provides secure model serialization with type verification

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
