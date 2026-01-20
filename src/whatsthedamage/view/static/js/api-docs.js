/**
 * API Documentation JavaScript functionality
 * Handles version switching and Swagger UI initialization
 */

function changeVersion() {
    const version = document.getElementById('version-select').value;
    window.location.href = '/api/docs?version=' + version;
}

window.onload = function() {
    const ui = SwaggerUIBundle({
        url: "/api/" + window.apiVersion + "/openapi.json",
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [
            SwaggerUIBundle.presets.apis,
            SwaggerUIBundle.plugins.DownloadUrl
        ],
        plugins: [
            SwaggerUIBundle.plugins.DownloadUrl
        ],
        layout: "StandaloneLayout"
    });
    window.ui = ui;
};
