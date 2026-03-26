# whatsthedamage Architecture Overview
This document serves as a critical, living template designed to equip agents with a rapid and comprehensive understanding of the codebase's architecture, enabling efficient navigation and effective contribution from day one. Update this document as the codebase evolves.

## 1. Project Structure
This section provides a high-level overview of the project's directory and file structure, categorised by architectural layer or major functional area. It is essential for quickly navigating the codebase, locating relevant files, and understanding the overall organization and separation of concerns.

```
whatsthedamage/
├── config/                  # Configuration files
│   └── gunicorn_conf.py     # Gunicorn production configuration
├── docs/                    # Project documentation
│   ├── calculator_pattern_example.py
│   └── scripts/README.md    # ML documentation
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
│   │   └── routes_helpers.py # Web route helpers
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
│   │   ├── data_formatting_service.py # Output formatting
│   │   ├── drilldown_service.py    # Drilldown functionality
│   │   ├── exclusion_service.py     # Exclusion handling
│   │   ├── file_upload_service.py   # File upload handling
│   │   ├── id_mapping_service.py    # ID mapping for secure URLs
│   │   ├── ml_service.py        # ML business logic orchestration
│   │   ├── processing_service.py    # Core processing service
│   │   ├── response_builder_service.py # Response construction
│   │   ├── service_factory.py      # Service container factory
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
│   ├── view/                 # Presentation layer
│   │   ├── frontend/         # TypeScript frontend
│   │   │   ├── src/          # Frontend sources
│   │   │   │   ├── main.ts   # Main entry point
│   │   │   │   ├── js/       # TypeScript modules
│   │   │   │   ├── css/      # CSS files
│   │   │   │   └── types/    # Type definitions
│   │   │   ├── package.json  # npm dependencies
│   │   │   ├── vite.config.js # Vite configuration
│   │   │   └── public/       # Public assets
│   │   ├── static/           # Flask static files
│   │   │   └── dist/         # Frontend build output
│   │   ├── templates/        # Jinja2 templates
│   │   ├── forms.py          # Flask forms
│   │   └── row_printer.py    # Console output formatting
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
[User] <--> [CLI Interface] <--> [ProcessingService] <--> [CSVProcessor] <--> [CsvFileHandler]
                                    |
                                    +--> [Web Interface] <--> [Flask App] <--> [ProcessingService]
                                    |
                                    +--> [REST API v2] <--> [ProcessingService]
```

The system follows a layered architecture with clear separation of concerns:
- **Presentation Layer**: CLI, Web, and REST API interfaces
- **Service Layer**: Business logic services (ProcessingService, ValidationService, etc.)
- **Model Layer**: Data processing and domain logic (CSVProcessor, RowsProcessor, etc.)
- **Configuration Layer**: Centralized configuration management
- **Utility Layer**: Cross-cutting concerns (localization, date handling)

## 3. Core Components

### 3.1. Frontend

**Name**: Web Application

**Description**: The main user interface for interacting with whatsthedamage, allowing users to upload CSV files, configure processing options, and view transaction analysis results. The web interface uses server-side rendering with Flask templates and progressive enhancement with TypeScript.

**Technologies**: Flask (Jinja2 templates), TypeScript, Vite, Bootstrap, DataTables

**Deployment**: Flask development server (make web), Gunicorn for production

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

#### 3.2.4. DataFormattingService

**Name**: Data Formatting Service

**Description**: Formats processed transaction data for various output targets including console, HTML, CSV, and JSON. Supports the unified DataTablesResponse format for web and API interfaces.

**Technologies**: Python

**Deployment**: Part of the Flask application

#### 3.2.5. IdMappingService

**Name**: ID Mapping Service

**Description**: Provides secure URL generation and mapping between internal IDs and user-facing identifiers. This service enables safe drilldown functionality by creating non-predictable URLs for accessing specific transaction details.

**Technologies**: Python, Flask-Caching integration

**Deployment**: Part of the Flask application

#### 3.2.6. DrilldownService

**Name**: Drilldown Service

**Description**: Enables detailed transaction analysis by providing drilldown capabilities. This service allows users to explore specific transactions, categories, or time periods in greater detail through secure URL-based access.

**Technologies**: Python

**Deployment**: Part of the Flask application

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

#### 3.2.9. TextCorrectionService

**Name**: Text Correction Service

**Description**: Provides ML-specific text cleaning and preprocessing for partner field values. Ensures consistent text normalization between training and inference phases, including unicode normalization, payment provider removal, and suffix cleaning.

**Technologies**: Python, regex

**Deployment**: Part of the Flask application

## 4. Data Stores

### 4.1. File-based Storage

**Name**: File Uploads and Processing Results

**Type**: File system storage

**Purpose**: Stores uploaded CSV files, configuration files, and processing results. The system uses temporary file storage for uploaded files and caching for processed results.

**Key Files/Directories**:
- `src/whatsthedamage/uploads/`: Temporary file uploads
- `src/whatsthedamage/static/`: ML models and metadata
- Session-based caching for processed results

### 4.2. Session Storage

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

## 6. Deployment & Infrastructure

**Cloud Provider**: Self-hosted or any cloud provider

**Key Services Used**:
- Flask development server for local development
- Gunicorn for production deployment
- Vite for frontend bundling and optimization

**CI/CD Pipeline**: Makefile-based automation with commands like:
- `make dev`: Set up development environment
- `make test`: Run tests
- `make web`: Run Flask development server
- `make vite-build`: Build production frontend assets

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

## 9. Future Considerations / Roadmap

**Known Architectural Debts**:
- Migrate from monolith to separate backend and fronend repositories.

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

## 10. Project Identification

**Project Name**: whatsthedamage

**Repository URL**: https://github.com/abalage/whatsthedamage

**Primary Contact/Team**: Balage Abalage

**Date of Last Update**: 2026-03-25

## 11. Glossary / Acronyms

**CLI**: Command Line Interface - The command-line tool for processing transactions

**CSV**: Comma-Separated Values - The file format used for bank transaction exports

**ML**: Machine Learning - Production-ready feature for transaction categorization using Random Forest with confidence calibration and SMOTE support

**DataTablesResponse**: Unified response format containing processed transaction data with aggregation by category and time period

**Calculator Pattern**: Extensibility pattern allowing custom transaction calculations beyond built-in categorization