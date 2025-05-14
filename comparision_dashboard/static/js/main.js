// Main JavaScript for Multi-Crop Profit Comparison Dashboard

document.addEventListener('DOMContentLoaded', function() {
    // Format currency values
    function formatCurrency(value) {
        return '₹' + value.toLocaleString('en-IN');
    }
    
    // Format percentage values
    function formatPercentage(value) {
        return value.toFixed(2) + '%';
    }
    
    // Handle table sorting
    const getCellValue = (tr, idx) => tr.children[idx].innerText || tr.children[idx].textContent;
    
    const comparer = (idx, asc) => (a, b) => {
        const v1 = getCellValue(asc ? a : b, idx);
        const v2 = getCellValue(asc ? b : a, idx);
        
        // Check if the values are numeric
        return v1 !== '' && v2 !== '' && !isNaN(v1) && !isNaN(v2) 
            ? v1 - v2 
            : v1.toString().localeCompare(v2);
    };
    
    // Add sorting functionality to table headers
    document.querySelectorAll('th').forEach(th => {
        th.addEventListener('click', () => {
            const table = th.closest('table');
            const tbody = table.querySelector('tbody');
            
            Array.from(tbody.querySelectorAll('tr'))
                .sort(comparer(Array.from(th.parentNode.children).indexOf(th), this.asc = !this.asc))
                .forEach(tr => tbody.appendChild(tr));
            
            // Update header classes to show sort direction
            table.querySelectorAll('th').forEach(header => header.classList.remove('sorted-asc', 'sorted-desc'));
            th.classList.toggle('sorted-asc', this.asc);
            th.classList.toggle('sorted-desc', !this.asc);
        });
    });
    
    // Select all crops button functionality
    const selectAllBtn = document.getElementById('select-all-btn');
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', function() {
            document.querySelectorAll('.crop-checkbox').forEach(checkbox => {
                checkbox.checked = true;
            });
        });
    }
    
    // Clear selection button functionality
    const clearSelectionBtn = document.getElementById('clear-selection-btn');
    if (clearSelectionBtn) {
        clearSelectionBtn.addEventListener('click', function() {
            document.querySelectorAll('.crop-checkbox').forEach(checkbox => {
                checkbox.checked = false;
            });
        });
    }
    
    // Responsive behavior for charts
    function resizeCharts() {
        if (window.Chart && window.Chart.instances) {
            Object.values(window.Chart.instances).forEach(chart => {
                chart.resize();
            });
        }
    }
    
    // Handle window resize for responsive charts
    window.addEventListener('resize', resizeCharts);
});
