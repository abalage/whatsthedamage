/**
 * Statistical Analysis Controls functionality
 * Handles recalculate and reset buttons for statistical analysis
 */

document.addEventListener('DOMContentLoaded', function() {
    var recalculateBtn = document.getElementById('recalculate-btn');
    var resetBtn = document.getElementById('reset-btn');

    if (recalculateBtn && resetBtn) {
        var spinner = recalculateBtn.querySelector('.spinner-border');

        // Recalculate button click handler
        recalculateBtn.addEventListener('click', function() {
            var algorithms = Array.prototype.slice.call(document.querySelectorAll('input[type="checkbox"][value]:checked'))
                .map(function(el) { return el.value; });
            var direction = document.querySelector('input[name="direction"]:checked').value;

            // Show loading spinner
            spinner.classList.remove('d-none');
            recalculateBtn.querySelector('span:last-child').textContent = 'Processing...';
            recalculateBtn.disabled = true;
            resetBtn.disabled = true;

            fetch('/recalculate-statistics', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    result_id: window.resultId,
                    algorithms: algorithms,
                    direction: direction
                })
            })
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(function(data) {
                if (data.status === 'success') {
                    // Update all cell highlights
                    updateCellHighlights(data.highlights);
                    showNotification('Statistics recalculated successfully!', 'success');
                } else {
                    throw new Error(data.error || 'Unknown error');
                }
            })
            .catch(function(error) {
                console.error('Error:', error);
                showNotification('Error recalculating statistics: ' + error.message, 'danger');
            })
            .finally(function() {
                // Hide loading spinner
                spinner.classList.add('d-none');
                recalculateBtn.querySelector('span:last-child').textContent = 'Recalculate';
                recalculateBtn.disabled = false;
                resetBtn.disabled = false;
            });
        });

        // Reset button click handler
        resetBtn.addEventListener('click', function() {
            // Reset checkboxes to default (both checked)
            document.getElementById('algorithm-iqr').checked = true;
            document.getElementById('algorithm-pareto').checked = true;

            // Reset radio buttons to default (columns checked)
            document.getElementById('direction-columns').checked = true;

            // Trigger recalculation with default settings
            recalculateBtn.click();
        });
    }
});
