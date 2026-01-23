/**
 * API Documentation JavaScript functionality
 * Handles version switching and Swagger UI initialization
 */

import SwaggerUIBundle from 'swagger-ui-dist/swagger-ui-bundle.js';
import SwaggerUIStandalonePreset from 'swagger-ui-dist/swagger-ui-standalone-preset.js';
import 'swagger-ui-dist/swagger-ui.css';

/**
 * Change API documentation version
 */
function changeVersion() {
    const version = document.getElementById('version-select').value;
    globalThis.location.href = '/api/docs?version=' + version;
}

/**
 * Initialize Swagger UI
 */
function initApiDocs() {
    globalThis.onload = function() {
        const ui = SwaggerUIBundle({
            url: "/api/" + globalThis.apiVersion + "/openapi.json",
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIStandalonePreset
            ],
            plugins: [
                SwaggerUIBundle.plugins.DownloadUrl
            ]
        });
        globalThis.ui = ui;
    };
}

// Expose functions globally for inline event handlers
globalThis.changeVersion = changeVersion;

// Auto-initialize
initApiDocs();
