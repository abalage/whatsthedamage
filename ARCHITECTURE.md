# whatsthedamage Architecture Overview
This document serves as a critical, living template designed to equip agents with a rapid and comprehensive understanding of the codebase's architecture, enabling efficient navigation and effective contribution from day one. Update this document as the codebase evolves.

## 1. Project Structure
This section provides a high-level overview of the project's directory and file structure, categorised by architectural layer or major functional area. It is essential for quickly navigating the codebase, locating relevant files, and understanding the overall organization and separation of concerns.

```
whatsthedamage/
├── config/                  # Configuration files
│   └── gunicorn_conf.py     # Gunicorn production configuration
├── docs/                    # Project documentation built by Sphinx
├── frontend/                # Vue 3 SPA Frontend (independent of backend)
│   ├── src/                 # TypeScript/Vue sources — see docs/frontend-architecture.md
│   │   ├── main.ts          # Application entry point
│   │   ├── App.vue          # Root Vue component
│   │   ├── pages/           # Route-level components (one per route)
│   │   ├── components/      # Reusable components (auth/, charts/, data/, layout/)
│   │   ├── composables/     # Vue 3 composable functions
│   │   ├── stores/          # Pinia stores (auth, dataset, categories, pivot, ...)
│   │   ├── router/          # Vue Router configuration (with auth guards)
│   │   ├── js/              # API client (api/ barrel: request, auth, transactions, processing) and utilities
│   │   ├── types/           # TypeScript type definitions (api, auth, column, index)
│   │   ├── locales/         # gettext catalogs (en.po, hu.po, messages.pot, translations.json)
│   │   └── css/, directives/, config/
│   ├── public/              # Static content
│   ├── dist/                # Production build output
│   ├── package.json
│   ├── vite.config.js
│   └── tsconfig.json
├── migrations/              # Alembic database migrations
│   └── versions/            # Versioned migration scripts
├── src/whatsthedamage/      # Main source code
│   ├── app.py              # Flask application factory and setup
│   ├── api/                 # REST API endpoints
│   │   ├── auth_decorators.py # require_authentication / require_csrf decorators
│   │   ├── error_handlers.py  # API error handlers
│   │   ├── helpers.py         # API helper functions
│   │   └── middleware.py     # Blueprint auth guard, API rate limits, security headers
│   │   └── v2/              # API v2 endpoints and schemas
│   │       ├── endpoints/       # API v2 sub-blueprints by domain
│   │       │   ├── reference.py          # Categories, CSV profiles, OpenAPI spec
│   │       │   ├── processing_results.py # CSV upload processing and result listings
│   │       │   ├── transactions.py       # Transaction CRUD and drilldown aggregation
│   │       │   ├── corrections.py        # Merchant-rule correction CRUD
│   │       │   └── statistics.py         # Statistical highlight recalculation
│   │       ├── schema.py        # OpenAPI 3.0 schema generator
│   │       └── auth/
│   │           └── endpoints.py # Authentication endpoints (register/login/logout)
│   ├── config/              # Configuration classes
│   │   ├── auth_config.py   # Authentication configuration
│   │   ├── config.py        # Central configuration
│   │   ├── config.yml.default   # Default configuration template
│   │   ├── csv_profiles.py  # CSV bank-format profile definitions
│   │   ├── database_config.py # SQLAlchemy engine/session configuration
│   │   ├── exclusions.json  # ExclusionService configuration
│   │   ├── flask_config.py  # Flask-specific configuration
│   │   ├── ml_config.py     # ML configuration
│   │   └── text_config.py   # TextCorrectionService configuration
│   ├── controllers/         # Request handling
│   │   ├── cli_controller.py # CLI argument parsing
│   │   ├── ml_cli.py         # ML CLI interface
│   │   ├── routes.py        # Web routes
│   │   └── frontend_routes.py # Frontend SPA routes (catch-all for Vue SPA)
│   ├── models/              # Data models and processing
│   │   ├── api/              # API contract models
│   │   │   ├── __init__.py     # Package exports
│   │   │   ├── common.py       # Common API models (ProcessingMetadata, ErrorResponse)
│   │   │   ├── requests.py     # Request models (ProcessingRequest)
│   │   │   └── responses.py    # Response models (ResultsApiResponse, etc.)
│   │   ├── database/         # SQLAlchemy ORM models
│   │   │   ├── base.py             # Declarative base
│   │   │   ├── user.py             # User entity
│   │   │   ├── session.py          # User session entity (with CSRF token hash)
│   │   │   ├── transaction.py      # Persisted transaction entity
│   │   │   ├── processing_result.py # Persisted processing result entity
│   │   │   ├── correction.py       # User transaction correction entity
│   │   │   ├── shared_correction.py # Shared correction entity
│   │   │   └── shared_correction_contribution.py # User-to-shared-correction link (erasure/withdrawal)
│   │   ├── repositories/     # Data access layer (Repository pattern)
│   │   │   ├── base_repository.py        # Generic repository base
│   │   │   ├── user_repository.py
│   │   │   ├── session_repository.py
│   │   │   ├── transaction_repository.py
│   │   │   ├── processing_result_repository.py
│   │   │   ├── correction_repository.py
│   │   │   └── shared_correction_repository.py
│   │   └── domain/           # Domain/business models
│   │       ├── __init__.py     # Package exports
│   │       ├── account.py          # Account model
│   │       ├── csv_row.py          # Transaction row model
│   │       ├── csv_file_handler.py # CSV file parsing
│   │       ├── csv_processor.py    # CSV processing orchestrator
│   │       ├── dt_models.py        # Aggregation models (AccountResponse, etc.)
│   │       ├── dt_response_builder.py # AccountResponse builder
│   │       ├── dt_calculators.py   # Calculator pattern implementations
│   │       ├── machine_learning.py  # ML model training and inference
│   │       ├── row_enrichment.py    # Regex-based categorization
│   │       ├── row_enrichment_ml.py # ML-based categorization
│   │       ├── row_filter.py        # Date filtering
│   │       ├── rows_processor.py    # Main processing pipeline
│   │       ├── session.py          # Domain session model
│   │       ├── user.py             # Domain user model
│   │       └── statistical_algorithms.py # Statistical analysis
│   ├── services/             # Business logic services
│   │   ├── account_service.py    # Registration, login, password reset/change
│   │   ├── auth_errors.py        # Typed authentication exceptions
│   │   ├── auth_session_service.py # Session lifecycle (create/validate/revoke, CSRF)
│   │   ├── cache_service.py      # Caching service
│   │   ├── configuration_service.py # Configuration loading
│   │   ├── correction_service.py # Merchant-rule upsert and sharing opt-in
│   │   ├── csv_profile_service.py # CSV bank-format profiles
│   │   ├── csrf_service.py      # CSRF token issuance/validation
│   │   ├── data_export_service.py # GDPR data export payload
│   │   ├── deduplication_service.py # Duplicate transaction detection
│   │   ├── drilldown_response_service.py # Drilldown response building
│   │   ├── exclusion_service.py     # Exclusion handling
│   │   ├── file_upload_service.py   # File upload handling
│   │   ├── id_mapping_service.py    # ID mapping for secure URLs
│   │   ├── interfaces.py       # Service interface protocols
│   │   ├── ml_service.py        # ML business logic orchestration
│   │   ├── password_service.py   # Argon2 password hashing
│   │   ├── processing_service.py    # Core processing service
│   │   ├── rate_limit_service.py    # API rate limiting
│   │   ├── recovery_code_service.py # One-time password recovery codes
│   │   ├── retention_service.py    # Account deletion and retention purge
│   │   ├── response_formatting_service.py # Unified formatting & response building
│   │   ├── service_container.py      # Service container factory
│   │   ├── session_service.py      # DB-backed session management
│   │   ├── smote_service.py      # SMOTE synthetic data generation
│   │   ├── statistical_analysis_service.py # Statistical analysis
│   │   ├── text_correction_service.py # Text cleaning for ML
│   │   ├── token_service.py     # Session token generation/verification
│   │   ├── transaction_import_service.py # CSV import persistence via the unit of work
│   │   └── validation_service.py   # File validation
│   ├── utils/                # Utility functions
│   │   ├── data_loader.py  # Data loading utils for Machine Learning
│   │   ├── date_converter.py  # Date parsing/formatting
│   │   ├── logging.py          # Centralized logging utils
│   │   ├── validation.py      # Validation utilities
│   │   └── version.py         # Version management
│   ├── static/               # Backend static assets
│   │   ├── model-card-template.md # Jinja2 template for Model Card generation
│   ├── view/                 # Presentation layer (legacy CLI output only)
│   │   ├── metrics_renderers/ # ML metrics rendering templates
│   │   ├── static/           # Flask static files
│   │   │   └── dist/         # Frontend build output (when served from backend)
│   │   ├── row_printer.py    # Console output formatting
│   │   └── __init__.py
│   └── uploads/              # File uploads
├── tests/                    # Backend tests
│   ├── api/v2/             # API contract and endpoint tests
│   ├── models/             # Model tests (transaction, correction, request)
│   ├── repositories/       # Repository tests
│   ├── services/           # Service layer tests
│   ├── test_model_privacy.py # Privacy and security tests for ML models
│   └── ...                   # Other test files
├── .github/                  # GitHub configurations
├── .gitignore                # Git ignore patterns
├── alembic.ini               # Alembic configuration
├── API.md                    # REST API documentation
├── ARCHITECTURE.md           # This document
├── changelog.md              # Changelog
├── CONTRIBUTING.md           # Contribution guidelines
├── LICENSE                   # License information
├── Makefile                  # Build automation
├── README.md                 # Project overview
├── README_ML.md              # ML documentation
├── pyproject.toml            # Python project metadata
├── requirements.txt          # Python dependencies
├── requirements-dev.txt      # Development dependencies
├── requirements-web.txt      # Web-specific dependencies
└── tox.ini                   # tox automation configuration
```

## 2. High-Level System Diagram
Provide a simple block diagram (e.g., a C4 Model Level 1: System Context diagram, or a basic component diagram) or a clear text-based description of the major components and their interactions. Focus on how data flows, services communicate, and key architectural boundaries.

```
[User] <--> [Frontend SPA (Vue 3)] <--> [REST API v2] <--> [ProcessingService] <--> [CSVProcessor] <--> [CsvFileHandler]
                                    |                        |
                                    |                        +--> [TransactionImportService] <--> [Repositories] <--> [Database (SQLAlchemy)]
                                    +--> [Auth API] <--> [AccountService / AuthSessionService] <--> [PasswordService / CsrfService / TokenService] <--> [Repositories]
                                    |
                                    +--> [CLI Interface] <--> [ProcessingService]
```

**Frontend Deployment Options**:
1. **Integrated**: Backend serves the SPA via `frontend_routes.py` catch-all route
2. **Standalone**: Frontend hosted separately
3. **Development**: Vite dev server with API proxy to backend

The system follows a layered architecture with clear separation of concerns:
- **Presentation Layer**: CLI and independent Frontend SPA (Vue 3) only
- **API Layer**: REST API v2 interfaces (Flask) - API-only, no web templates, with authentication/CSRF decorators
- **Service Layer**: Business logic services (ProcessingService, ValidationService, AccountService, AuthSessionService, etc.)
- **Model Layer**: Data processing and domain logic (CSVProcessor, RowsProcessor, etc.)
- **Persistence Layer**: SQLAlchemy ORM models and repositories for users, sessions, transactions, processing results, and corrections
- **Configuration Layer**: Centralized configuration management
- **Utility Layer**: Cross-cutting concerns (date handling)

## 3. Core Components

### 3.1. Frontend

**Name**: Frontend SPA (Vue 3 Single Page Application)

**Description**: Completely independent frontend application for interacting with whatsthedamage. The frontend communicates with the backend exclusively through REST API v2 endpoints, enabling independent development, deployment, and scaling. Built with Vue 3, TypeScript, and modern frontend tooling. No server-side templates are used.

**Technologies**: Vue 3 (Composition API, `<script setup>`), strict TypeScript, Pinia (setup stores), Vue Router with meta-driven auth guards (`requiresAuth` / `requiresGuest` / `public`), Vite 8, Bootstrap 5 via native HTML elements + classes (no wrapper components), vue3-gettext (English/Hungarian), chart.js via vue-chartjs, and the custom `VueDataTable.vue` data grid (no DataTables.net/jQuery).

**Key Features** (summary):
- Session restored from cookies by a single global `router.beforeEach`; pages never re-initialize auth state
- CSV import flow on the `/import` page driven by backend CSV profile definitions
- Optional `resultId` query parameter filters transaction views (Categories, Transactions, Pivot, drilldowns) to a single processing result; unknown paths fall back to a catch-all NotFound route
- Transaction views share a cached full-dataset store; `fetchAllTransactions` pages `/api/v2/transactions` in 2,000-row requests up to 50,000 rows (visible truncation warning beyond)
- Inline correction of transaction attributes (category, merchant, notice) with per-transaction vs. "apply to future" merchant-rule persistence, undo (`POST /transactions/<id>/undo`), and corrected-cell highlighting
- User settings: correction-sharing opt-in, username/password change, GDPR data export, scheduled account deletion
- i18n (English/Hungarian) and multiple persisted themes

**Frontend architecture and conventions live in `docs/frontend-architecture.md`** — directory layout, the API layer (`js/api/`), stores, the three sanctioned async error/loading patterns, data grid extension via `#cell-<key>` slots, i18n/theming, build/deployment modes, and the quality gates. This document intentionally keeps only the basics above.

**Deployment**: Independent static hosting (standalone, CORS-enabled) or integrated with the backend via the Flask catch-all route (see 3.2.10).

### 3.2. Backend Services

#### 3.2.1. ProcessingService

**Name**: Processing Service

**Description**: Core business logic service that orchestrates CSV transaction processing. This service handles file parsing, transaction categorization (regex or ML), filtering, and aggregation. It provides a unified interface used by all delivery mechanisms (CLI, Web, API).

**Technologies**: Python, Flask extensions for dependency injection

**Deployment**: Part of the Flask application

#### 3.2.2. ValidationService

**Name**: Validation Service

**Description**: Handles file validation including type checking, size limits, and content integrity verification. Ensures uploaded files meet requirements before processing.

**Technologies**: Python

**Deployment**: Part of the Flask application

#### 3.2.3. ConfigurationService

**Name**: Configuration Service

**Description**: Manages loading and access to configuration settings including CSV format definitions, attribute mappings, enrichment patterns, and categories.

**Technologies**: Python, YAML parsing

**Deployment**: Part of the Flask application

#### 3.2.4. ResponseFormattingService

**Name**: Response Formatting Service

**Description**: Unified service combining data formatting and response building capabilities. Formats processed transaction data for various output targets including console, HTML, CSV, and JSON. Supports the unified AccountResponse format for web and API interfaces. This service merges the functionality of the previous DataFormattingService and ResponseBuilderService to reduce cognitive complexity and ensure consistent formatting across all interfaces.

**Technologies**: Python

**Deployment**: Part of the Flask application

**Key Features**:
- Multiple output formats: HTML tables, CSV strings, JSON, plain text
- AccountResponse formatting for web and API interfaces
- Error response building for consistent API error handling
- Account-aware formatting with secure ID handling

#### 3.2.5. IdMappingService

**Name**: ID Mapping Service

**Description**: Provides secure URL generation and mapping between internal IDs and user-facing identifiers. This service enables safe drilldown functionality by creating non-predictable URLs for accessing specific transaction details. Uses CacheService for storage to comply with existing architectural patterns.

**Technologies**: Python, Flask-Caching integration

**Deployment**: Part of the Flask application

**Key Features**:
- Secure mapping between account numbers and IDs
- Category name/ID mapping for URL safety
- Month timestamp/ID mapping for time-based drilldown
- Cache-backed storage for performance

#### 3.2.6. DrilldownResponseService

**Name**: Drilldown Response Service

**Description**: Service for building consistent drilldown API responses (get_category_months, get_month_categories, category_month_transactions) with highlight handling. Replaced the legacy DrilldownService.

**Responsibilities**:
- Building drilldown responses for category months, month categories, and category month transactions
- Aggregating highlights from parent processing results
- Resolving entity IDs for drilldown operations
- Generating drilldown URLs with ID mapping
- Filtering and caching drilldown data

#### 3.2.7. MLService

**Name**: ML Service

**Description**: Core business logic service for machine learning operations. Orchestrates model training, prediction, and evaluation. Provides a unified interface for ML operations including hyperparameter tuning, confidence calibration, and SMOTE support.

**Technologies**: Python, scikit-learn, skops

**Deployment**: Part of the Flask application

#### 3.2.8. SmoteService

**Name**: SMOTE Service

**Description**: Handles synthetic data generation for rare categories using Synthetic Minority Oversampling Technique. Identifies imbalanced classes and generates synthetic samples to improve model performance on underrepresented categories.

**Technologies**: Python, imbalanced-learn

**Deployment**: Part of the Flask application

**Key Features**:
- Automatic detection of imbalanced classes
- Configurable SMOTE parameters via ML configuration
- Integration with MLService for model training
- Support for rare category enhancement

#### 3.2.9. TextCorrectionService

**Name**: Text Correction Service

**Description**: Provides ML-specific text cleaning and preprocessing for partner field values. Ensures consistent text normalization between training and inference phases, including unicode normalization, payment provider removal, and suffix cleaning.

**Technologies**: Python, regex

**Deployment**: Part of the Flask application

#### 3.2.10. FrontendRoutes Service

**Name**: Frontend Routes Service

**Description**: Serves the Vue 3 frontend SPA for all non-API routes. Provides a catch-all route (`/` and `/<path:path>`) that delivers the frontend's `index.html`, enabling client-side routing via Vue Router, direct URL access, and bookmarking of drilldown pages. This service allows the backend to serve the frontend in integrated deployment scenarios.

**Technologies**: Python, Flask, static file serving

**Deployment**: Part of the Flask application (in `controllers/frontend_routes.py`)

**Key Features**:
- Catch-all route for all non-API paths
- Serves pre-built frontend from `view/static/dist/`
- Refuses `.map` requests with 404 even when a stray source map file exists in the dist folder
- Enables Vue Router client-side navigation
- Supports direct URL access to drilldown pages (e.g., `/results?resultId=abc123`)
- Supports opening links in new tabs
- Supports browser refresh on drilldown pages
- Fallback to API error if frontend not built

**Registration Note**: The catch-all route must be registered **AFTER** all API blueprints to ensure API routes take precedence.

#### 3.2.11. AccountService / AuthSessionService

**Name**: Account and Session Services

**Description**: AccountService orchestrates user registration, login, password reset/change, and account-deletion scheduling. AuthSessionService owns the session lifecycle (create/validate/revoke) and CSRF token minting — every mint rotates the stored hash, so a newly issued token invalidates the previously issued one. Together they coordinate PasswordService, TokenService, CsrfService, RecoveryCodeService, and the user/session repositories.

**Technologies**: Python

**Deployment**: Part of the Flask application

#### 3.2.12. PasswordService

**Name**: Password Service

**Description**: Password hashing and verification using Argon2 (via argon2-cffi). Handles password strength requirements and secure rehashing on login.

**Technologies**: Python, argon2-cffi

**Deployment**: Part of the Flask application

#### 3.2.13. TokenService

**Name**: Token Service

**Description**: Session token generation and verification using Python's `secrets` module. Tokens are stored hashed (SHA-256) in DB session entities; the browser holds the opaque token in an HttpOnly, Secure, SameSite=Lax (all configurable) cookie.

**Technologies**: Python

**Deployment**: Part of the Flask application

#### 3.2.14. CsrfService

**Name**: CSRF Service

**Description**: Issues and validates CSRF tokens for state-changing requests. The token is delivered to the SPA as a readable (deliberately not HttpOnly) `csrf_token` cookie, set by login, register, getMe, and `GET /api/v2/auth/csrf-token`, and cleared on logout; the SPA echoes it in the `X-CSRF-Token` header. Only the SHA-256 hash is stored server-side, and each mint rotates it (invalidating previously issued tokens). CSRF 403 responses carry machine-readable `code` values (`CSRF_SESSION_REQUIRED`, `CSRF_TOKEN_MISSING`, `CSRF_TOKEN_NOT_SET`, `CSRF_TOKEN_INVALID`) that the frontend's automatic retry branches on.

**Technologies**: Python

**Deployment**: Part of the Flask application

#### 3.2.15. RateLimitService

**Name**: Rate Limit Service

**Description**: Rate limiting for sensitive operations (login, registration, password reset) plus a general per-IP API limit and a stricter bucket for expensive endpoints (upload processing, statistics recalculation). Configurable via `config/auth_config.py` and `config/flask_config.py`.

**Technologies**: Python

**Deployment**: Part of the Flask application

#### 3.2.16. RecoveryCodeService

**Name**: Recovery Code Service

**Description**: One-time recovery codes for password reset. Codes are issued at registration/recovery setup and consumed once during password recovery.

**Technologies**: Python

**Deployment**: Part of the Flask application

#### 3.2.17. DeduplicationService

**Name**: Deduplication Service

**Description**: Detects duplicate transactions on import (same account, date, partner, amount) so re-uploaded CSV exports do not create double entries.

**Technologies**: Python

**Deployment**: Part of the Flask application

#### 3.2.18. CsvProfileService

**Name**: CSV Profile Service

**Description**: Serves CSV bank-format profile definitions (column mappings, date formats) exposed via the `/api/v2/csv-profiles` endpoints and used by the frontend import flow.

**Technologies**: Python

**Deployment**: Part of the Flask application

#### 3.2.19. RetentionService

**Name**: Retention Service

**Description**: Implements the data retention policy (`docs/retention-policy.md`). Schedules account deletion requests (`DELETE /api/v2/auth/account`: password confirmation, 7-day grace period during which login cancels the deletion) and runs the periodic purge (`flask --app whatsthedamage.app retention-purge`): permanently deletes accounts whose grace period has elapsed and the accounts of users inactive for longer than the retention window (6 months by default), together with all their personal data. Anonymized shared corrections are never deleted.

**Technologies**: Python

**Deployment**: Part of the Flask application

#### 3.2.20. Repository Layer

**Name**: Repositories (Data Access Layer)

**Description**: Data access objects in `src/whatsthedamage/models/repositories/` encapsulating all SQLAlchemy queries. A generic `BaseRepository` provides shared CRUD operations; specialized repositories cover users, sessions, transactions, processing results, corrections, and shared corrections. Services depend on repositories rather than issuing queries directly.

**Technologies**: Python, SQLAlchemy 2.0

**Deployment**: Part of the Flask application

## 4. Data Stores

### 4.1. Relational Database

**Name**: Application Database

**Type**: Relational database via SQLAlchemy 2.0 ORM

**Purpose**: Durable, per-user persistence of accounts, sessions, imported transactions, processing results, and corrections. Introduced on the `user-persistence-support` branch; replaces the previous cache-only handling of processing results.

**Configuration**:
- Database URI configurable via the `WHATSTHEDAMAGE_DATABASE_URI` environment variable, defaulting to `sqlite:///app.db`
- Schema managed by Alembic migrations in `migrations/versions/` (configured via `alembic.ini`)
- Entities in `src/whatsthedamage/models/database/`: User, Session, Transaction, ProcessingResult, Correction, SharedCorrection
- On CSV import, the importing user's merchant rules (partner and category only; notices are per-transaction) are applied to the newly stored transactions via a case-insensitive exact match on the original partner name; the deduplication hash is always computed from the original row, so rules never alter the deduplication key. Transactions store their raw pre-correction category and notice in the `original_category_id`/`original_notice` columns for original-vs-corrected display and undo
- Correction sharing (opt-in, default off): when a user opts in via the Settings page (`PUT /api/v2/auth/me`), merchant rules (partner + category, never notices, amounts, dates, or user data) written at any merchant-rule site (`POST`/`PUT /api/v2/corrections`, rule-mode `POST`/`PUT /api/v2/transactions/<id>`) are contributed to the anonymized `shared_corrections` table keyed by a SHA-256 hash of the lowercase partner name. The opt-in flag is evaluated per write, so revoking it (US-8) stops future contributions immediately; previously shared rows are retained permanently and are not linked to any user, so they survive account deletion by design
- All data access goes through the repository layer (`src/whatsthedamage/models/repositories/`)

### 4.2. File-based Storage

**Name**: File Uploads

**Type**: File system storage

**Purpose**: Stores uploaded CSV files and ML model assets. Uploaded files are handled temporarily during processing; processed results are persisted to the database, not the cache.

**Key Files/Directories**:
- `src/whatsthedamage/uploads/`: Temporary file uploads
- `src/whatsthedamage/static/`: ML models and metadata
- CacheService still used for short-lived data (e.g., ID mappings)

### 4.3. Frontend Assets

**Name**: Frontend Build Artifacts

**Type**: Static file storage

**Purpose**: Stores compiled frontend assets (JavaScript, CSS, HTML) for production deployment. The frontend is now completely decoupled from the backend and can be deployed independently.

**Key Files/Directories**:
- `frontend/dist/`: Production-ready frontend build (when deployed standalone)
- `frontend/src/`: Frontend source code (TypeScript/Vue components)
- Build artifacts are excluded from Git via `.gitignore`

### 4.4. Session Storage

**Name**: Web Session Management

**Type**: Database-backed session entities with cookie tokens

**Purpose**: Manages authenticated user sessions between requests. Sessions are stored as `Session` entities in the database (including a CSRF token hash); the browser holds the opaque session token in an HttpOnly, Secure, SameSite=Lax cookie and the CSRF token in a readable `csrf_token` cookie (see 3.2.14). No Flask session-based state is used for user identity.

## 5. External Integrations / APIs

### 5.1. Machine Learning Model

**Service Name**: Random Forest Model with Confidence Calibration

**Purpose**: Provides ML-based transaction categorization as an alternative to regex-based categorization. The model is trained on historical transaction data and includes advanced features like confidence calibration, SMOTE for rare categories, multi-CPU training support, and privacy-preserving text feature extraction.

**Integration Method**: skops model loading (secure serialization with type verification)

**Key Features**:
- Random Forest classifier with 200 estimators
- Confidence calibration using CalibratedClassifierCV
- SMOTE support for handling imbalanced datasets
- Multi-CPU parallel processing
- Confidence threshold for categorization
- Comprehensive metrics and evaluation
- HashingVectorizer for text features (no vocabulary storage)
- Secure serialization with skops.io

### 5.2. Localization

Removed.

### 5.3. REST API v2

**Service Name**: What's the Damage REST API v2

**Purpose**: Provides HTTP API for user authentication, CSV transaction import, transaction CRUD, corrections, aggregation/drilldown, and statistical analysis. All transaction data is scoped to the authenticated user.

**Integration Method**: Flask REST API with Pydantic models and session-cookie authentication

**Architecture:**
- **API-First Design**: Contract defined via Pydantic models in `src/whatsthedamage/models/api/responses.py` and the OpenAPI 3.0 schema served at `/api/v2/openapi.json`
- **Type Safety**: Backend Pydantic models mirror frontend TypeScript interfaces
- **Validation**: Requests validated before processing; responses validated with Pydantic where models exist (e.g., `RecalculateApiResponse`), otherwise serialized via `jsonify`
- **Service Layer**: Business logic delegated to services (ProcessingService, TransactionImportService, CorrectionService, StatisticalAnalysisService, DrilldownResponseService, AccountService, AuthSessionService)
- **Dependency Injection**: Services injected via Flask extensions
- **Authentication**: `require_authentication` / `optional_authentication` / `require_csrf` / `require_auth_and_csrf` decorators in `api/auth_decorators.py`

**Key Components:**
- `src/whatsthedamage/api/v2/endpoints/`: API v2 sub-blueprints by domain — `reference.py`, `processing_results.py`, `transactions.py`, `corrections.py`, `statistics.py`
- `src/whatsthedamage/api/v2/auth/endpoints.py`: Authentication route handlers (auth blueprint, prefix `/api/v2/auth`)
- `src/whatsthedamage/api/v2/schema.py`: OpenAPI 3.0 schema generator
- `src/whatsthedamage/models/api/responses.py`: Pydantic response DTOs
- `src/whatsthedamage/api/helpers.py`: Request validation and the shared error-response helpers (`create_error_response` / `json_error_response`)
- `frontend/src/js/api.ts`: barrel re-exporting the API modules in `frontend/src/js/api/` (transport `request.ts`, plus `auth.ts`, `transactions.ts`, `processing.ts`)
- `frontend/src/types/api.ts` / `frontend/src/types/auth.ts`: TypeScript interfaces

**Endpoints:**
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v2/auth/register` | Register a new user account |
| POST | `/api/v2/auth/login` | Authenticate user, create session |
| POST | `/api/v2/auth/logout` | Terminate the current session |
| GET | `/api/v2/auth/me` | Current user information |
| PUT | `/api/v2/auth/me` | Update user settings (correction sharing opt-in) |
| PUT | `/api/v2/auth/me/password` | Change password (current password required) |
| GET | `/api/v2/auth/me/export` | GDPR data export (machine-readable document) |
| DELETE | `/api/v2/auth/account` | Schedule account deletion (password confirmation, 7-day grace period) |
| POST | `/api/v2/auth/reset-password` | Reset password using a recovery code |
| GET | `/api/v2/auth/csrf-token` | Mint a fresh CSRF token (delivered as a readable cookie) |
| POST | `/api/v2/processing-results` | Process and import CSV transactions |
| GET | `/api/v2/processing-results` | List processing results |
| GET | `/api/v2/processing-results/<result_id>` | Processing result metadata |
| GET | `/api/v2/transactions` | List user transactions (paginated, filterable) |
| POST | `/api/v2/transactions` | Create a transaction |
| GET | `/api/v2/transactions/<id>` | Retrieve a single transaction |
| PUT | `/api/v2/transactions/<id>` | Update a transaction |
| POST | `/api/v2/transactions/<id>/undo` | Undo corrections of a transaction (restore original values, delete its merchant rule) |
| DELETE | `/api/v2/transactions/<id>` | Delete a transaction |
| GET | `/api/v2/transactions/aggregate` | Aggregate transactions by category/month/account (drilldown) |
| GET | `/api/v2/corrections` | List transaction corrections |
| POST | `/api/v2/corrections` | Create a correction |
| GET | `/api/v2/corrections/<id>` | Retrieve a correction |
| PUT | `/api/v2/corrections/<id>` | Update a correction |
| DELETE | `/api/v2/corrections/<id>` | Delete a correction |
| GET | `/api/v2/categories` | Category definitions |
| GET | `/api/v2/categories/cost-of-living` | Cost-of-living category subset |
| GET | `/api/v2/csv-profiles` | Available CSV bank-format profiles |
| GET | `/api/v2/csv-profiles/<profile_id>` | A single CSV profile |
| POST | `/api/v2/recalculate-statistics` | Recalculate statistical highlights (`RecalculateApiResponse`) |
| GET | `/api/v2/openapi.json` | OpenAPI 3.0 specification |

The legacy drilldown endpoints (`/processing-results/<id>/accounts/...`) were removed and replaced by `GET /api/v2/transactions/aggregate`, which supports grouping by category, month, and account.

**Statistical Highlights Contract:**
- `POST /api/v2/recalculate-statistics` computes highlights from persisted
  `Transaction` entities. `result_id` is optional (omitted = all of the user's
  transactions). Highlights are keyed by matrix-view cell ID:
  `{account}|{month}|{category}` (month as `YYYY-MM`, category as `category_id`
  or `uncategorized`).
- `GET /api/v2/transactions/aggregate` accepts `algorithms` (comma-separated)
  and `direction` (`columns`|`rows`) query parameters and returns highlights
  keyed by the same `group_key` values as its `groups` — view-relative cell IDs,
  consistent with the parent matrix analysis scope.

**Pagination:**
- `GET /api/v2/transactions` supports `limit`/`offset` (defaults 100/0) plus filtering by date range, category, account, partner, transaction type, month, amount range, and `result_id`, with `sort_by`/`sort_order`

**API Contract Standardization:**
- Responses use validated Pydantic models where models exist; new endpoints should prefer the standard response envelope (`ApiEnvelope<T>`)
- Frontend TypeScript interfaces match backend models 1:1
- Contract tests verify response schema compliance
- Error responses use the shared `{error, code?, retry_after?}` shape produced by `api/helpers.py`; the machine-readable `code` lets the frontend branch without parsing messages (e.g. the automatic CSRF retry on `CSRF_TOKEN_INVALID`)

**Contract Testing:**
- 15 contract tests in `tests/api/v2/test_contract.py`
- Endpoint tests in `tests/api/v2/test_transaction_endpoints.py` and `tests/test_api_v2_endpoints.py`
- `make api-contract` dumps the OpenAPI component schemas to `frontend/test/fixtures/api-contract-schemas.json`; a backend pytest fails when the fixture goes stale, and `frontend/test/apiContract.test.ts` asserts the mirrored TypeScript types against it — backend contract changes surface at frontend gate time

**Documentation:**
- [API-First Architecture](docs/api-first-architecture.md)
- [API Style Guide](docs/api-style-guide.md)
- OpenAPI schema at `/api/v2/openapi.json`

## 6. Deployment & Infrastructure

**Cloud Provider**: Self-hosted or any cloud provider

**Key Services Used**:
- Flask development server for local development
- Gunicorn for production deployment (backend)
- Relational database via SQLAlchemy 2.0 (default SQLite `app.db`; configurable with `WHATSTHEDAMAGE_DATABASE_URI`, e.g., PostgreSQL for production)
- Alembic for database schema migrations
- Vite for frontend bundling and optimization
- npm for frontend dependency management
- **ML Dependencies**: scikit-learn, skops (v0.14.0) for secure model serialization, imbalanced-learn for SMOTE
- **Auth Dependencies**: argon2-cffi for password hashing

**Database Setup**:
- Configure the database URI via `WHATSTHEDAMAGE_DATABASE_URI` (defaults to `sqlite:///app.db`)
- Apply migrations with Alembic (`alembic upgrade head`, configured via `alembic.ini`)
- Sessions, users, transactions, processing results, and corrections live in the database; back it up accordingly

**CI/CD Pipeline**: Makefile-based automation with commands like:
- `make dev`: Set up development environment (Python venv + npm dependencies)
- `make test`: Run tests
- `make backend`: Run Flask development server
- `make frontend`: Start Vite development server
- `make frontend-build`: Build frontend assets (`npm run build:prod` from `frontend/` for the production bundle)
- `make api-contract`: Regenerate the API contract fixture for the frontend contract tests
- `make build`: Full stack build (Python + JavaScript)

**Frontend Deployment Options**:
1. **Standalone Deployment**: Frontend built with `npm run build:prod` and `dist/` directory hosted on static hosting. Backend API must be accessible via CORS.
2. **Development Mode**: Vite dev server runs on port 3000 with the `/api/v2` proxy to `http://localhost:5000`. Backend Flask server runs separately on port 5000.

**Production Security Configuration**:
- CORS must remain restricted to the actual frontend origin in production
- Rate limits and session lifetimes are configured in `config/auth_config.py`
- CSRF protection applies to all state-changing API endpoints; ensure the frontend origin is allowed so tokens validate

**CORS Configuration**:
- Development: CORS enabled for `http://localhost:3000` and `http://127.0.0.1:3000`
- Production: Configurable via Flask-CORS settings in `app.py`
- Required for standalone frontend deployment

**Monitoring & Logging**:
- **Structured Logging System**: Comprehensive logging with configurable levels (DEBUG, INFO, WARN, ERROR), output destinations (stdout or file), and formats (text or JSON)
- **CLI Configuration**: Command line arguments `--log-level`, `--log-output`, and `--log-format` for runtime logging configuration
- **Default Configuration**: WARN level logging to stdout for both CLI and web interfaces
- **Context Support**: Structured logging with contextual information support via LoggerAdapter
- **File Output**: Optional file-based logging with automatic fallback to stdout on errors

## 7. Security Considerations

**Authentication**: Username/password accounts with Argon2 password hashing (`password_service.py`, argon2-cffi). Sessions are DB-backed entities identified by an opaque token stored in a cookie. Password reset uses one-time recovery codes. Rate limiting protects sensitive endpoints (login, registration, password reset).

**Authorization**: Per-user data isolation. All transaction, processing result, and correction endpoints scope queries to the authenticated user via the repository layer. Enforcement is layered: blueprint-level middleware in `api/middleware.py` requires a valid session on every `/api/v2/*` route (except an explicit public allowlist of reference-data endpoints), and `api/auth_decorators.py` (`require_authentication`, `require_auth_and_csrf`, `require_csrf`) provides per-route defense in depth.

**Data Encryption**: Passwords are stored as Argon2 hashes; session tokens and CSRF tokens are hashed at rest in the `Session` entity. Transport encryption should be provided by the deployment (reverse proxy/TLS).

**Key Security Tools/Practices**:
- Argon2 password hashing with automatic rehash on login
- CSRF tokens delivered to the SPA as readable cookies (set on login/register/getMe/`GET /api/v2/auth/csrf-token`, rotated on every mint, cleared on logout) with server-side hash verification on all state-changing requests
- Blueprint-level authentication middleware on all `/api/v2/*` routes with an explicit public allowlist (`api/middleware.py`)
- Security headers on every response: CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, and `Cache-Control: no-store` on API responses (`api/middleware.py`)
- Rate limiting for login/registration/password reset plus general and heavy-endpoint API limits (`rate_limit_service.py`, configured in `config/auth_config.py` and `config/flask_config.py`)
- Configurable CORS origins via `WHATSTHEDAMAGE_CORS_ORIGINS` (defaults to the Vite dev server)
- Input validation for all user and file inputs
- File type and content verification
- Secure file handling with proper cleanup
- Never logging sensitive data (account numbers, personal info, passwords, tokens)
- Resource management with prompt file handle closing
- Error handling without exposing internal errors

**Known Security Issues**:
- File uploads require validation of MIME types and extensions
- Default SQLite database file should be protected from direct download by the web server

## 8. Development & Testing Environment

**Local Setup Instructions**: See CONTRIBUTING.md or README.md

**Testing Frameworks**:
- pytest for backend unit and integration tests
- Vitest for frontend tests

**Code Quality Tools**:
- ruff for Python linting and formatting
- mypy for Python type checking
- ESLint for JavaScript/TypeScript linting

**Build Tools**:
- Makefile for workflow automation
- Vite for frontend bundling
- npm for frontend dependency management
- Vue Router for client-side routing
- Pinia for state management
- TypeScript compiler for type checking

## 9. Future Considerations / Roadmap

**Known Architectural Debts**:
- Complete migration to separate backend and frontend repositories (completed: frontend decoupled at root level, can be split into separate repo)

**Planned Major Changes**:
- Retire remaining CacheService usages in favor of database persistence where durability is required
- Enhance ML model management and security
- Improve error handling and user feedback
- Add more statistical analysis features
- Support additional CSV formats and banks (via the CSV profile system)

**Significant Future Features**:
- Event-driven architecture for real-time updates
- Enhanced API capabilities for third-party integrations
- Mobile application support
- Additional localization languages

**Recent Architectural Improvements**:
- **Frontend Security Remediation (2026-10)**: CSRF tokens moved from localStorage to readable cookies with per-mint rotation; machine-readable error `code` values on all CSRF 403s; formula-injection-prone CSV/XLS export and the `v-html` table rendering removed (replaced by escaped `formatValue`); sourcemaps excluded from production builds and refused by the backend catch-all
- **Frontend Refactor (2026-10)**: VueDataTable decomposed into `useTable*` composables with `#cell-<key>` slot-based cell extension; `useApiData`/`useAsyncAction` error contracts standardized (three sanctioned async patterns); global Vue error handler (console-only); API contract fixture tests via `make api-contract`
- **User Persistence Support**: Introduced SQLAlchemy 2.0 ORM with Alembic migrations. Users, sessions, transactions, processing results, and corrections are persisted in a relational database (default SQLite, configurable via `WHATSTHEDAMAGE_DATABASE_URI`), replacing cache-only processing results.
- **Repository Pattern**: Added a dedicated data access layer (`models/repositories/`) with a generic `BaseRepository` and per-entity repositories; services no longer issue queries directly.
- **Authentication & Authorization**: User registration, login, logout, and password reset with one-time recovery codes. Argon2 password hashing, DB-backed sessions, CSRF token verification, and per-endpoint rate limiting. Frontend gained auth pages (Login, Register, ForgotPassword), an auth Pinia store, and router guards.
- **Transaction CRUD & Corrections**: Transactions are first-class persisted entities with full REST CRUD, filtering, and pagination; users can correct transaction metadata and share corrections.
- **New Date Protocol**: Transaction dates stored as datetime; months addressed as `YYYY-MM` in API contracts and drilldown keys.
- **Drilldown Rework**: Removed the per-processing-result drilldown endpoints in favor of `GET /api/v2/transactions/aggregate` with view-relative group keys; `result_id` became an optional filter across transaction views.
- **Pagination Support**: `GET /api/v2/transactions` supports limit/offset pagination and rich filtering; the frontend fetches large datasets in 2,000-row pages (capped at 50,000).
- **CSV Profiles**: Bank-format profiles (`config/csv_profiles.py`, `/api/v2/csv-profiles` endpoints) decouple CSV parsing from configuration; frontend gained a dedicated Import page.
- **Data Grid Replacement**: Removed DataTables.net and jQuery; transactions and pivot views use a custom `VueDataTable.vue` component, and charts use chart.js/vue-chartjs.
- **i18n Migration**: Switched from JSON translation files to vue3-gettext with gettext catalogs (`.po`/`.mo`) in `frontend/src/locales/`.
- **Frontend-Backend Decoupling**: Migrated from Jinja2 server-side templates to standalone Vue 3 SPA with complete API-only communication. Frontend moved from `src/whatsthedamage/view/frontend/` to project root `frontend/`. All web templates removed. Added `frontend_routes.py` for integrated deployment support.
- **Frontend Modernization**: Adopted Vue 3 with Composition API, Vue Router, Pinia for state management, TypeScript 5.x, and Vite 8 for building
- **Removed Wrapper Components**: Eliminated ButtonComponent and CardComponent that added unnecessary abstraction over Bootstrap's native classes. All usages replaced with native HTML elements + Bootstrap classes, improving code clarity and reducing maintenance burden.
- **Simplified Composables**: Refactored useDrilldownData from a monolithic 375-line file into focused, single-responsibility composables (useRouteParams, useApiData, useBreadcrumbs, usePageTitle) that can be composed together, improving maintainability and testability. Removed deprecated buildEndpoint pattern.
- **Code Cleanup**: Removed duplicate theme initialization from Layout.vue (theme store already auto-initializes), deleted unused utils.ts file with showNotification function.
- **Service consolidation**: Merged DataFormattingService and ResponseBuilderService into unified ResponseFormattingService
- **ML Serialization Migration**: Complete migration from joblib to skops.io for secure model serialization with type verification. Added comprehensive privacy protections for distribution-ready models.
- **CLI Distribution Mode**: Added `--distribution` flag to ML CLI for creating privacy-protected, public-ready models with HashingVectorizer and no test data.
- **Privacy-Enhanced ML**: Implemented HashingVectorizer for text features (no vocabulary storage), distribution mode for public-ready models, and HuggingFace Model Card standardization with privacy guarantees.
- **Model Card Generation**: Added Jinja2-based Model Card generation from HuggingFace official template with comprehensive metadata and privacy information.
- **Comprehensive Privacy Testing**: Added test suite (`test_model_privacy.py`) verifying no vocabulary storage, no private paths exposure, secure serialization, and distribution mode compliance.
- Improved dependency injection patterns with standardized service container
- Enhanced IdMappingService to use CacheService for consistency
- Simplified service registration and usage across CLI and web contexts
- Added CORS support for frontend-backend communication
- Added FrontendRoutes Service for serving Vue SPA in integrated deployment mode

## 10. Project Identification

**Project Name**: whatsthedamage

**Repository URL**: https://github.com/abalage/whatsthedamage

**Primary Contact/Team**: Balage Abalage

**Date of Last Update**: 2026-10-24

## 11. Glossary / Acronyms

**CLI**: Command Line Interface - The command-line tool for processing transactions

**CSV**: Comma-Separated Values - The file format used for bank transaction exports

**ML**: Machine Learning - Production-ready feature for transaction categorization using Random Forest with confidence calibration and SMOTE support

**AccountResponse**: Unified response format containing processed transaction data with aggregation by category and time period

**Calculator Pattern**: Extensibility pattern allowing custom transaction calculations beyond built-in categorization

**SPA**: Single Page Application - The Vue 3-based frontend that communicates with the backend via REST API

**Vue**: Progressive JavaScript framework used for the frontend SPA

**Pinia**: State management library for Vue applications, used for managing auth, dataset cache, categories, feedback, form, locale, pivot, statistical preferences, and theme state

**Vite**: Modern build tool for frontend development with HMR (Hot Module Replacement)

**Vue Router**: Client-side routing library for Vue applications, enabling navigation without page reloads

**TypeScript**: Typed superset of JavaScript used for frontend development

**CORS**: Cross-Origin Resource Sharing - Mechanism enabling frontend-backend communication across different origins

**SQLAlchemy**: Python SQL toolkit and ORM used for database models and queries

**Alembic**: Database migration tool for SQLAlchemy, managing schema changes in `migrations/`

**Repository Pattern**: Data access layer encapsulating SQLAlchemy queries behind per-entity repository classes

**CSRF**: Cross-Site Request Forgery - Attack mitigated by per-session tokens required on state-changing API requests

**Argon2**: Password hashing algorithm used for storing user password hashes securely

**Rate Limiting**: Restricting the number of requests per time window for sensitive endpoints (login, registration, password reset)

**Recovery Code**: One-time code allowing a user to reset their password without an email flow

**CSV Profile**: Definition of a bank's CSV export format (column mappings, date formats) used by the import flow