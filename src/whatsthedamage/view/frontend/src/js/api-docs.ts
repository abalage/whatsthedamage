/**
 * API Documentation JavaScript functionality
 * Handles version switching and Swagger UI initialization
 */

import SwaggerUIBundle from 'swagger-ui-dist/swagger-ui-bundle.js';
import SwaggerUIStandalonePreset from 'swagger-ui-dist/swagger-ui-standalone-preset.js';
import 'swagger-ui-dist/swagger-ui.css';

declare global {
    interface Window {
        changeVersion: () => void;
        ui: any;
        apiVersion: string;
        location: Location;
    }
}

/**
 * Change API documentation version
 */
function changeVersion(): void {
    const version = document.getElementById('version-select') as HTMLSelectElement | null;
    if (version) {
        window.location.href = '/api/docs?version=' + version.value;
    }
}

/**
 * Initialize Swagger UI
 */
function initApiDocs(): void {
    window.onload = function() {
        const ui = (SwaggerUIBundle as any)({
            url: "/api/" + window.apiVersion + "/openapi.json",
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [
                (SwaggerUIBundle as any).presets.apis,
                SwaggerUIStandalonePreset
            ],
            plugins: [
                (SwaggerUIBundle as any).plugins.DownloadUrl
            ]
        });
        window.ui = ui;
    };
}

// Expose functions globally for inline event handlers
window.changeVersion = changeVersion;

// Auto-initialize
initApiDocs();
