/**
 * API Documentation JavaScript functionality
 * Handles version switching and Swagger UI initialization
 */

function changeVersion() {
    const version = document.getElementById('version-select').value;
    window.location.href = '/api/docs?version=' + version;
}

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
