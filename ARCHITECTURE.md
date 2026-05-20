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
│   ├── src/
│   │   ├── main.ts          # Application entry point
│   │   ├── App.vue          # Root Vue component
│   │   ├── router/
│   │   │   └── index.ts     # Vue Router configuration
│   │   ├── components/
│   │   │   ├── Layout.vue
│   │   │   ├── ErrorDisplay.vue
│   │   │   └── ui/          # UI component library
│   │   │       ├── ButtonComponent.vue
│   │   │       ├── CardComponent.vue
│   │   │       └── StatisticalControls.vue
│   │   ├── config/
│   │   |   └── highlight-config.ts
│   │   ├── css/
│   │   │   ├── components.css
│   │   │   ├── main.css
│   │   |   └── results.css
│   │   ├── pages/           # Page-level components (routes)
│   │   │   ├── About.vue
│   │   │   ├── CategoryMonthsList.vue
│   │   │   ├── CategoryMonthTransactions.vue
│   │   │   ├── Details.vue
│   │   │   ├── Index.vue
│   │   │   ├── Legal.vue
│   │   │   ├── MonthCategoriesList.vue
│   │   │   ├── Privacy.vue
│   │   │   ├── Results.vue
│   │   │   └── Statistics.vue
│   │   ├── stores/          # Pinia state management
│   │   │   ├── feedback.ts
│   │   │   ├── form.ts
│   │   │   ├── locale.ts
│   │   │   ├── statistical.ts
│   │   │   └── translations.ts
│   │   ├── translations/    # Language specific translations
│   │   │   ├── hu.json
│   │   │   └── en.json
│   │   ├── js/              # Utility functions and API client
│   │   │   ├── api.ts
│   │   │   ├── index.ts
│   │   │   ├── main.ts
│   │   │   ├── statistical-analysis.ts
│   │   │   └── utils.ts
│   │   └── types/           # TypeScript type definitions
│   │       ├── api.ts
│   │       └── index.ts
│   ├── public/              # Static content
│   │   └── favicon.ico
│   ├── dist/                # Production build output
│   ├── package.json
│   ├── vite.config.js
│   └── tsconfig.json
├── src/whatsthedamage/      # Main source code
│   ├── api/                 # REST API endpoints
│   │   ├── v2/              # API v2 endpoints and schemas
│   │   │   ├── endpoints.py # API v2 processing endpoints
│   │   │   └── schema.py    # API response schemas
│   │   ├── docs.py          # API documentation
│   │   └── helpers.py       # API helper functions
│   ├── config/              # Configuration classes
│   │   ├── config.py        # Central configuration
|   │   ├── config.yml.default   # Default configuration template
│   │   ├── dt_models.py     # Data models for API responses
│   │   ├── exclusions.json  # ExclusionService configuration
│   │   ├── flask_config.py  # Flask-specific configuration
│   │   └── ml_config.py     # ML configuration
│   │   └── text_config.py     # TextCorrectionService configuration
│   ├── controllers/         # Request handling
│   │   ├── cli_controller.py # CLI argument parsing
│   │   ├── ml_cli.py         # ML CLI interface
│   │   ├── routes.py        # Web routes
│   │   ├── routes_helpers.py # Web route helpers
│   │   └── frontend_routes.py # Frontend SPA routes (catch-all for Vue SPA)
│   ├── models/              # Data models and processing
│   │   ├── api_models.py       # API models
│   │   ├── csv_file_handler.py # CSV file parsing
│   │   ├── csv_processor.py    # CSV processing orchestrator
│   │   ├── csv_row.py          # Transaction row model
│   │   ├── dt_calculators.py   # Calculator pattern implementations
│   │   ├── dt_models.py        # DataTable related models
│   │   ├── dt_response_builder.py # DataTables response builder
│   │   ├── machine_learning.py  # ML model training and inference
│   │   ├── row_enrichment.py    # Regex-based categorization
│   │   ├── row_enrichment_ml.py # ML-based categorization
│   │   ├── row_filter.py        # Date filtering
│   │   ├── rows_processor.py    # Main processing pipeline
│   │   └── statistical_algorithms.py # Statistical analysis
│   ├── scripts/              # placeholder
│   ├── services/             # Business logic services
│   │   ├── cache_service.py      # Caching service
│   │   ├── configuration_service.py # Configuration loading
│   │   ├── data_formatting_service.py # Output formatting (deprecated)
│   │   ├── drilldown_response_service.py    # Drilldown response building
│   │   ├── exclusion_service.py     # Exclusion handling
│   │   ├── file_upload_service.py   # File upload handling
│   │   ├── id_mapping_service.py    # ID mapping for secure URLs
│   │   ├── ml_service.py        # ML business logic orchestration
│   │   ├── processing_service.py    # Core processing service
│   │   ├── response_builder_service.py # Response construction (deprecated)
│   │   ├── response_formatting_service.py # Unified formatting & response building
│   │   ├── service_container.py      # Service container factory
│   │   ├── session_service.py      # Web session management
│   │   ├── smote_service.py      # SMOTE synthetic data generation
│   │   ├── statistical_analysis_service.py # Statistical analysis
│   │   ├── text_correction_service.py # Text cleaning for ML
│   │   └── validation_service.py   # File validation
│   ├── static/               # Backend static assets
│   ├── utils/                # Utility functions
│   │   ├── data_loader.py  # Data loading utils for Machine Learning
│   │   ├── date_converter.py  # Date parsing/formatting
│   │   ├── flask_locale.py    # Flask localization
│   │   ├── logging.py          # Centralized logging utils
│   │   ├── validation.py      # Validation utilities
│   │   └── version.py         # Version management
│   ├── view/                 # Presentation layer (legacy CLI output only)
│   │   ├── static/           # Flask static files
│   │   │   └── dist/         # Frontend build output (when served from backend)
│   │   ├── row_printer.py    # Console output formatting
│   │   └── __init__.py
│   └── uploads/              # File uploads
├── tests/                    # Backend tests
│   ├── services/             # Service layer tests
│   └── ...                   # Other test files
├── .github/                  # GitHub configurations
├── .gitignore                # Git ignore patterns
├── API.md                    # REST API documentation
├── ARCHITECTURE.md           # This document
├── CONTRIBUTING.md           # Contribution guidelines
├── LICENSE                   # License information
├── Makefile                  # Build automation
├── PRODUCT.md                # Product information
├── README.md                 # Project overview
├── pyproject.toml            # Python project metadata
├── requirements.txt          # Python dependencies
├── requirements-dev.txt      # Development dependencies
└── requirements-web.txt      # Web-specific dependencies
```

## 2. High-Level System Diagram
Provide a simple block diagram (e.g., a C4 Model Level 1: System Context diagram, or a basic component diagram) or a clear text-based description of the major components and their interactions. Focus on how data flows, services communicate, and key architectural boundaries.

```
[User] <--> [Frontend SPA (Vue 3)] <--> [REST API v2] <--> [ProcessingService] <--> [CSVProcessor] <--> [CsvFileHandler]
                                    |
                                    +--> [CLI Interface] <--> [ProcessingService]
```

**Frontend Deployment Options**:
1. **Integrated**: Backend serves the SPA via `frontend_routes.py` catch-all route
2. **Standalone**: Frontend hosted separately
3. **Development**: Vite dev server with API proxy to backend

The system follows a layered architecture with clear separation of concerns:
- **Presentation Layer**: CLI and independent Frontend SPA (Vue 3) only
- **API Layer**: REST API v2 interfaces (Flask) - API-only, no web templates
- **Service Layer**: Business logic services (ProcessingService, ValidationService, etc.)
- **Model Layer**: Data processing and domain logic (CSVProcessor, RowsProcessor, etc.)
- **Configuration Layer**: Centralized configuration management
- **Utility Layer**: Cross-cutting concerns (localization, date handling)

## 3. Core Components

### 3.1. Frontend

**Name**: Frontend SPA (Vue 3 Single Page Application)

**Description**: Completely independent frontend application for interacting with whatsthedamage. The frontend communicates with the backend exclusively through REST API v2 endpoints, enabling independent development, deployment, and scaling. Built with Vue 3, TypeScript, and modern frontend tooling.

**Technologies**:
- **Framework**: Vue 3 with Composition API
- **Type System**: TypeScript 5.x
- **State Management**: Pinia (stores for form, locale, statistical analysis, translations, feedback)
- **Routing**: Vue Router 4 for client-side navigation
- **Build Tool**: Vite 8 with ESM modules and HMR
- **UI Framework**: Bootstrap 5 with custom Vue components
- **Data Grid**: DataTables.net 2.3.x with Bootstrap 5 integration
- **Utilities**: jQuery 4.0.x (for DataTables integration)

**Deployment**: Independent static hosting or integrated with backend via Flask static serving

**Key Features**:
- Complete decoupling from backend - no server-side templates
- API-only communication via REST API v2 endpoints
- Independent build and deployment pipeline
- CORS-enabled communication with backend
- Client-side routing with Vue Router
- State management with Pinia stores
- Type-safe development with TypeScript
- Hot Module Replacement (HMR) in development

**Frontend Architecture**:
```
Frontend SPA (Vue 3)
├── App.vue              # Root component
├── router/              # Vue Router configuration
├── stores/              # Pinia state management
│   ├── form.ts           # Form state
│   ├── locale.ts         # Locale/language state
│   ├── statistical.ts    # Statistical analysis state
│   ├── translations.ts   # Translation state
│   └── feedback.ts       # User feedback state
├── components/           # Reusable Vue components
│   ├── Layout.vue
│   ├── ErrorDisplay.vue
│   └── ui/               # UI component library
├── pages/                # Page-level components (routes)
│   ├── About.vue
│   ├── Details.vue
│   ├── Results.vue
│   └── ...
└── js/                   # Utility functions
    ├── api.ts            # API client
    ├── main.ts           # DataTables initialization
    └── ...
```

**API Communication**:
- Development: Vite proxies `/api` to `http://localhost:5000/api/v2`
- Production: Uses `/api/v2` base URL or configurable via `VITE_API_BASE_URL`
- CORS-enabled for cross-origin requests

**Deployment Modes**:
1. **Integrated**: Backend serves frontend from `view/static/dist/` via `frontend_routes.py`
2. **Standalone**: Frontend hosted separately on static hosting
3. **Development**: Vite dev server (port 3000) with API proxy

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

**Description**: Unified service combining data formatting and response building capabilities. Formats processed transaction data for various output targets including console, HTML, CSV, and JSON. Supports the unified DataTablesResponse format for web and API interfaces. This service merges the functionality of the previous DataFormattingService and ResponseBuilderService to reduce cognitive complexity and ensure consistent formatting across all interfaces.

**Technologies**: Python

**Deployment**: Part of the Flask application

**Key Features**:
- Multiple output formats: HTML tables, CSV strings, JSON, plain text
- DataTablesResponse formatting for web and API interfaces
- Currency formatting with locale support
- Template preparation for Jinja2 rendering
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

**Technologies**: Python, scikit-learn, joblib

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
- Enables Vue Router client-side navigation
- Supports direct URL access to drilldown pages (e.g., `/results/abc123/`)
- Supports opening links in new tabs
- Supports browser refresh on drilldown pages
- Fallback to API error if frontend not built

**Registration Note**: The catch-all route must be registered **AFTER** all API blueprints to ensure API routes take precedence.

## 4. Data Stores

### 4.1. File-based Storage

**Name**: File Uploads and Processing Results

**Type**: File system storage

**Purpose**: Stores uploaded CSV files, configuration files, and processing results. The system uses temporary file storage for uploaded files and caching for processed results.

**Key Files/Directories**:
- `src/whatsthedamage/uploads/`: Temporary file uploads
- `src/whatsthedamage/static/`: ML models and metadata
- Session-based caching for processed results

### 4.2. Frontend Assets

**Name**: Frontend Build Artifacts

**Type**: Static file storage

**Purpose**: Stores compiled frontend assets (JavaScript, CSS, HTML) for production deployment. The frontend is now completely decoupled from the backend and can be deployed independently.

**Key Files/Directories**:
- `frontend/dist/`: Production-ready frontend build (when deployed standalone)
- `frontend/src/`: Frontend source code (TypeScript/Vue components)
- Build artifacts are excluded from Git via `.gitignore`

### 4.3. Session Storage

**Name**: Web Session Management

**Type**: Flask session storage

**Purpose**: Manages user session state between requests for the web interface, including file uploads and processing results.

## 5. External Integrations / APIs

### 5.1. Machine Learning Model

**Service Name**: Random Forest Model with Confidence Calibration

**Purpose**: Provides ML-based transaction categorization as an alternative to regex-based categorization. The model is trained on historical transaction data and includes advanced features like confidence calibration, SMOTE for rare categories, and multi-CPU training support.

**Integration Method**: joblib model loading (security warning: only use trusted models)

**Key Features**:
- Random Forest classifier with 200 estimators
- Confidence calibration using CalibratedClassifierCV
- SMOTE support for handling imbalanced datasets
- Multi-CPU parallel processing
- Confidence threshold for categorization
- Comprehensive metrics and evaluation

**Model Files**:
- `model-rf-v6alpha_en.joblib`: Trained model with calibration
- `model-rf-v6alpha_en.manifest.json`: Training metadata and parameters
- `model-rf-v6alpha_en.testdata.json`: Test data for validation

### 5.2. Localization

**Service Name**: gettext/i18n

**Purpose**: Provides localization support for English and Hungarian languages.

**Integration Method**: Python gettext module with locale files

### 5.3. REST API v2

**Service Name**: What's the Damage REST API v2

**Purpose**: Provides HTTP API for CSV transaction processing, results retrieval, drilldown navigation, and statistical analysis.

**Integration Method**: Flask REST API with Pydantic models

**Architecture:**
- **API-First Design**: Contract defined via Pydantic models in `src/whatsthedamage/models/api_responses.py`
- **Type Safety**: Backend Pydantic models mirror frontend TypeScript interfaces exactly
- **Validation**: All responses validated using Pydantic; all requests validated before processing
- **Service Layer**: Business logic delegated to services (ProcessingService, CacheService, StatisticalService, DrilldownResponseService)
- **Dependency Injection**: Services injected via Flask extensions

**Key Components:**
- `src/whatsthedamage/api/v2/endpoints.py`: REST API route handlers
- `src/whatsthedamage/models/api_responses.py`: Pydantic response DTOs
- `src/whatsthedamage/api/helpers.py`: Request validation and error handling utilities
- `frontend/src/js/api.ts`: TypeScript API client with typed functions
- `frontend/src/types/api.ts`: TypeScript response interfaces

**Endpoints:**
| Method | Endpoint | Purpose | Response Type |
|--------|----------|---------|---------------|
| POST | `/api/v2/process` | Process CSV transactions | `ProcessApiResponse` |
| GET | `/api/v2/results/<result_id>` | Retrieve processed results | `ResultsApiResponse` |
| GET | `/api/v2/results/<r>/accounts/<a>/categories/<c>/months` | Category-by-month drilldown | `CategoryMonthsApiResponse` |
| GET | `/api/v2/results/<r>/accounts/<a>/months/<m>/categories` | Month-by-category drilldown | `MonthCategoriesApiResponse` |
| GET | `/api/v2/results/<r>/accounts/<a>/categories/<c>/months/<m>/transactions` | Transaction details | `CategoryMonthTransactionsApiResponse` |
| POST | `/api/v2/recalculate-statistics` | Recalculate statistical highlights | `RecalculateApiResponse` |

**API Contract Standardization:**
- All endpoints return validated Pydantic models
- Frontend TypeScript interfaces match backend models 1:1
- Contract tests verify response schema compliance
- Standard response envelope (`ApiEnvelope<T>`) available for new endpoints
- Error responses use consistent `{code, message, details?}` format

**Contract Testing:**
- 18 contract tests in `tests/api/v2/test_contract.py`
- Tests verify Pydantic model validation for all endpoints
- Tests verify response structure, field types, and required fields

**Documentation:**
- [API-First Architecture](docs/api-first-architecture.md)
- [API Style Guide](docs/api-style-guide.md)

## 6. Deployment & Infrastructure

**Cloud Provider**: Self-hosted or any cloud provider

**Key Services Used**:
- Flask development server for local development
- Gunicorn for production deployment (backend)
- Vite for frontend bundling and optimization
- npm for frontend dependency management

**CI/CD Pipeline**: Makefile-based automation with commands like:
- `make dev`: Set up development environment (Python venv + npm dependencies)
- `make test`: Run tests
- `make backend`: Run Flask development server
- `make frontend`: Start Vite development server
- `make frontend-build:prod`: Build production frontend assets
- `make build`: Full stack build (Python + JavaScript)

**Frontend Deployment Options**:
1. **Standalone Deployment**: Frontend built with `npm run build:prod` and `dist/` directory hosted on static hosting. Backend API must be accessible via CORS.
2. **Development Mode**: Vite dev server runs on port 3000 with `/api` proxy to `http://localhost:5000/api/v2`. Backend Flask server runs separately on port 5000.

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

**Authentication**: Not applicable (local tool, no user accounts)

**Authorization**: Not applicable (local tool)

**Data Encryption**: Not applicable (local file processing)

**Key Security Tools/Practices**:
- Input validation for all user and file inputs
- File type and content verification
- Secure file handling with proper cleanup
- Never logging sensitive data (account numbers, personal info)
- Resource management with prompt file handle closing
- Error handling without exposing internal errors

**Known Security Issues**:
- joblib model loading can execute arbitrary code (only use trusted models)
- File uploads require validation of MIME types and extensions

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
- Migrate from memory-based caching to more robust solution
- Enhance ML model management and security
- Improve error handling and user feedback
- Add more statistical analysis features
- Support additional CSV formats and banks

**Significant Future Features**:
- Event-driven architecture for real-time updates
- Enhanced API capabilities for third-party integrations
- Mobile application support
- Additional localization languages

**Recent Architectural Improvements**:
- **Frontend-Backend Decoupling**: Migrated from Jinja2 server-side templates to standalone Vue 3 SPA with complete API-only communication. Frontend moved from `src/whatsthedamage/view/frontend/` to project root `frontend/`. All web templates removed. Added `frontend_routes.py` for integrated deployment support.
- **Frontend Modernization**: Adopted Vue 3 with Composition API, Vue Router 4, Pinia for state management, TypeScript 5.x, and Vite 8 for building
- **Service consolidation**: Merged DataFormattingService and ResponseBuilderService into unified ResponseFormattingService
- Improved dependency injection patterns with standardized service container
- Enhanced IdMappingService to use CacheService for consistency
- Simplified service registration and usage across CLI and web contexts
- Added CORS support for frontend-backend communication
- Added FrontendRoutes Service for serving Vue SPA in integrated deployment mode

## 10. Project Identification

**Project Name**: whatsthedamage

**Repository URL**: https://github.com/abalage/whatsthedamage

**Primary Contact/Team**: Balage Abalage

**Date of Last Update**: 2026-05-06

## 11. Glossary / Acronyms

**CLI**: Command Line Interface - The command-line tool for processing transactions

**CSV**: Comma-Separated Values - The file format used for bank transaction exports

**ML**: Machine Learning - Production-ready feature for transaction categorization using Random Forest with confidence calibration and SMOTE support

**DataTablesResponse**: Unified response format containing processed transaction data with aggregation by category and time period

**Calculator Pattern**: Extensibility pattern allowing custom transaction calculations beyond built-in categorization

**SPA**: Single Page Application - The Vue 3-based frontend that communicates with the backend via REST API

**Vue**: Progressive JavaScript framework used for the frontend SPA

**Pinia**: State management library for Vue applications, used for managing form state, locale, statistical analysis, translations, and feedback

**Vite**: Modern build tool for frontend development with HMR (Hot Module Replacement)

**Vue Router**: Client-side routing library for Vue applications, enabling navigation without page reloads

**TypeScript**: Typed superset of JavaScript used for frontend development

**CORS**: Cross-Origin Resource Sharing - Mechanism enabling frontend-backend communication across different origins