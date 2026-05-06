# What's the Damage Frontend

Independent frontend application for What's the Damage - a bank transaction analysis tool.

## Overview

This is a standalone TypeScript/Vite frontend that communicates with the backend exclusively through REST API endpoints. The frontend is completely decoupled from the backend, enabling independent development, deployment, and scaling.

## Architecture

```
[User] <--> [Frontend SPA] <--> [Backend API] <--> [Processing Services]
```

## Features

- **Complete Decoupling**: No direct dependency on backend templates or static files
- **API-only Communication**: All interactions go through REST API endpoints
- **Modern Tooling**: Vite, TypeScript, ESM modules
- **CORS Support**: Cross-origin communication with backend
- **Independent Deployment**: Can be hosted separately from backend

## Development Setup

### Prerequisites

- Node.js 24+
- npm 10+
- Backend API running on `http://localhost:5000`

### Installation

```bash
# Install dependencies
npm install

# Start development server with backend proxy
dev: npm run dev

# Build for production
build: npm run build
build:prod: npm run build:prod

# Run tests
test: npm run test
test:watch: npm run test:watch

# Lint and format
lint: npm run lint
format: npm run format
```

## Static Pages

The frontend includes static informational pages in multiple languages:

### English Pages
- **About Page**: `/about/` - Information about the application
- **Legal Page**: `/legal/` - License and legal information
- **Privacy Page**: `/privacy/` - Privacy policy

### Hungarian Pages
- **About Page**: `/hu/about/` - Információ az alkalmazásról
- **Legal Page**: `/hu/legal/` - Licenc és jogi információk
- **Privacy Page**: `/hu/privacy/` - Adatvédelmi nyilatkozat

### Assets
- **Favicon**: `public/favicon.ico` - Application icon

These pages are standalone HTML files with inline CSS and include the favicon for proper branding.

## Configuration

The frontend uses environment variables for configuration:

- `VITE_API_BASE_URL`: Base URL for API endpoints (default: `/api`)
- Development: Proxies `/api` to `http://localhost:5000/api/v2`
- Production: Uses `/api/v2` directly

## API Endpoints

The frontend communicates with these backend API endpoints:

- `POST /api/v2/process` - Process CSV transactions
- `POST /api/v2/recalculate-statistics` - Recalculate statistical analysis

## Build Output

Production builds output to `dist/` directory:

```
dist/
├── css/          # Compiled CSS files
├── js/           # Compiled JavaScript bundles
├── assets/       # Static assets
└── index.html    # Main HTML entry point
```

## Deployment

### Development

```bash
# Start frontend dev server (port 3000)
npm run dev

# Start backend API (port 5000)
cd ..
make backend
```

The development setup uses Vite's proxy to forward API requests to the backend.

### Production

```bash
# Build frontend
npm run build:prod

# Deploy dist/ directory to:
# - Static hosting (Netlify, Vercel, S3, etc.)
# - CDN
# - Separate service

# Backend API should be available at the configured URL
```

## CORS Configuration

The backend must be configured to allow CORS requests from the frontend:

```python
# In backend Flask app
from flask_cors import CORS
CORS(app, resources={
    r"/api/*": {"origins": ["http://localhost:3000", "https://your-frontend-url.com"]}
})
```

## Project Structure

```
frontend/
├── src/                # Source code
│   ├── js/             # JavaScript/TypeScript modules
│   ├── css/            # CSS files
│   ├── types/          # TypeScript type definitions
│   └── main.ts          # Main entry point
├── public/             # Public assets
│   ├── index.html      # Main HTML template
│   ├── about/          # About page (English)
│   │   └── index.html
│   ├── legal/          # Legal page (English)
│   │   └── index.html
│   ├── privacy/        # Privacy page (English)
│   │   └── index.html
│   ├── hu/             # Hungarian pages
│   │   ├── about/      # About page (Hungarian)
│   │   │   └── index.html
│   │   ├── legal/      # Legal page (Hungarian)
│   │   │   └── index.html
│   │   └── privacy/    # Privacy page (Hungarian)
│   │       └── index.html
├── test/               # Tests
├── dist/               # Build output (generated)
├── package.json        # npm configuration
├── vite.config.js      # Vite configuration
└── README.md           # This file
```

## Communication with Backend

The frontend uses the `api.ts` module to communicate with the backend:

```typescript
// Example API call
import { processTransactions, recalculateStatistics } from './js/api';

// Process transactions
const formData = new FormData();
formData.append('csv_file', file);
const result = await processTransactions(formData);

// Recalculate statistics
const stats = await recalculateStatistics(resultId, algorithms, direction);
```