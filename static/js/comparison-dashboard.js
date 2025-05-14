// Comparison Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Chart configuration
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'bottom',
                labels: {
                    boxWidth: 12,
                    padding: 10,
                    font: {
                        size: 10
                    }
                }
            },
            tooltip: {
                backgroundColor: 'rgba(255, 255, 255, 0.9)',
                titleColor: '#333',
                bodyColor: '#666',
                borderColor: '#ddd',
                borderWidth: 1,
                padding: 10,
                boxWidth: 10,
                boxHeight: 10,
                usePointStyle: true,
                callbacks: {
                    label: function(context) {
                        let label = context.dataset.label || '';
                        if (label) {
                            label += ': ';
                        }
                        if (context.parsed.y !== null) {
                            if (context.dataset.yAxisID === 'y-axis-profit') {
                                label += '₹' + context.parsed.y.toLocaleString();
                            } else {
                                label += context.parsed.y.toFixed(1) + '%';
                            }
                        }
                        return label;
                    }
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                ticks: {
                    font: {
                        size: 10
                    }
                }
            },
            x: {
                ticks: {
                    font: {
                        size: 10
                    }
                }
            }
        }
    };

    // Initialize profit and ROI charts
    const profitChartCtx = document.getElementById('profit-chart').getContext('2d');
    const roiChartCtx = document.getElementById('roi-chart').getContext('2d');

    const profitChart = new Chart(profitChartCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Profit per Acre',
                data: [],
                backgroundColor: 'rgba(40, 167, 69, 0.7)',
                borderColor: 'rgba(40, 167, 69, 1)',
                borderWidth: 1
            }]
        },
        options: {
            ...chartOptions,
            plugins: {
                ...chartOptions.plugins,
                title: {
                    display: true,
                    text: 'Profit per Acre (₹)',
                    font: {
                        size: 14,
                        weight: 'bold'
                    }
                }
            }
        }
    });

    const roiChart = new Chart(roiChartCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'ROI (%)',
                data: [],
                backgroundColor: 'rgba(253, 126, 20, 0.7)',
                borderColor: 'rgba(253, 126, 20, 1)',
                borderWidth: 1
            }]
        },
        options: {
            ...chartOptions,
            plugins: {
                ...chartOptions.plugins,
                title: {
                    display: true,
                    text: 'Return on Investment (%)',
                    font: {
                        size: 14,
                        weight: 'bold'
                    }
                }
            }
        }
    });

    // Initialize yield comparison chart if prediction result exists
    const yieldComparisonChartElement = document.getElementById('yield-comparison-chart');
    if (yieldComparisonChartElement) {
        const yieldComparisonChartCtx = yieldComparisonChartElement.getContext('2d');

        // First check if we have prediction data in the global window object (from debug script)
        if (window.predictionData) {
            console.log("Using global prediction data:", window.predictionData);
            createYieldComparisonChart(yieldComparisonChartCtx, window.predictionData);
        }
        // Otherwise try to get it from the data attribute
        else if (yieldComparisonChartElement.hasAttribute('data-prediction-result')) {
            try {
                const predictionDataStr = yieldComparisonChartElement.getAttribute('data-prediction-result');
                console.log("Raw prediction data string:", predictionDataStr);

                // Try to parse the JSON data
                const predictionData = JSON.parse(predictionDataStr);
                console.log("Parsed prediction data:", predictionData);

                createYieldComparisonChart(yieldComparisonChartCtx, predictionData);
            } catch (error) {
                console.error("Error parsing prediction data:", error);
            }
        } else {
            console.log("No prediction data found");
        }
    }

    // Function to create the yield comparison chart
    function createYieldComparisonChart(ctx, data) {
        if (!data || !data.base_yield || !data.yield_per_acre) {
            console.error("Invalid prediction data format:", data);
            return;
        }

        console.log("Creating yield comparison chart with data:", data);

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Base Yield', 'Predicted Yield'],
                datasets: [{
                    label: 'Yield (kg/acre)',
                    data: [data.base_yield, data.yield_per_acre],
                    backgroundColor: ['rgba(108, 117, 125, 0.7)', 'rgba(40, 167, 69, 0.7)'],
                    borderColor: ['rgba(108, 117, 125, 1)', 'rgba(40, 167, 69, 1)'],
                    borderWidth: 1,
                    borderRadius: 4,
                    hoverBackgroundColor: ['rgba(108, 117, 125, 0.9)', 'rgba(40, 167, 69, 0.9)']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 1000,
                    easing: 'easeOutQuart'
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: `${data.crop_name} Yield Comparison`,
                        font: {
                            size: 12,
                            weight: 'bold'
                        },
                        padding: {
                            bottom: 8
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(38, 50, 56, 0.9)',
                        titleFont: {
                            weight: 'bold',
                            size: 11
                        },
                        bodyFont: {
                            size: 10
                        },
                        padding: 8,
                        cornerRadius: 4,
                        callbacks: {
                            label: function(context) {
                                return `${context.raw.toLocaleString()} kg/acre`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            font: {
                                size: 9
                            }
                        },
                        title: {
                            display: true,
                            text: 'Yield (kg/acre)',
                            font: {
                                size: 9,
                                weight: 'bold'
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                size: 9
                            }
                        }
                    }
                }
            }
        });
    }

    // Crop selection and comparison functionality
    const cropCheckboxes = document.querySelectorAll('.crop-checkbox');
    const compareBtn = document.getElementById('compare-btn');
    const cropRows = document.querySelectorAll('.crop-row');

    // Handle crop row click to show details
    cropRows.forEach(row => {
        row.addEventListener('click', function() {
            const cropId = this.getAttribute('data-crop-id');
            showCropDetails(cropId);

            // Highlight the selected row
            document.querySelectorAll('.crop-row').forEach(r => r.classList.remove('selected'));
            this.classList.add('selected');
        });
    });

    // Handle compare button click
    if (compareBtn) {
        compareBtn.addEventListener('click', function() {
            const selectedCrops = [];
            cropCheckboxes.forEach(checkbox => {
                if (checkbox.checked) {
                    const cropId = checkbox.value;
                    const cropRow = document.querySelector(`.crop-row[data-crop-id="${cropId}"]`);
                    if (cropRow) {
                        const cropName = cropRow.querySelector('strong').textContent;
                        const profit = parseFloat(cropRow.querySelector('td:nth-child(6)').textContent.replace('₹', '').replace(',', ''));
                        const roi = parseFloat(cropRow.querySelector('td:nth-child(7) span').textContent.replace('%', ''));

                        selectedCrops.push({
                            id: cropId,
                            name: cropName,
                            profit: profit,
                            roi: roi
                        });
                    }
                }
            });

            updateCharts(selectedCrops);
        });
    }

    // Function to update charts with selected crops
    function updateCharts(crops) {
        if (crops.length === 0) {
            alert('Please select at least one crop to compare.');
            return;
        }

        // Update profit chart
        profitChart.data.labels = crops.map(crop => crop.name);
        profitChart.data.datasets[0].data = crops.map(crop => crop.profit);
        profitChart.update();

        // Update ROI chart
        roiChart.data.labels = crops.map(crop => crop.name);
        roiChart.data.datasets[0].data = crops.map(crop => crop.roi);
        roiChart.update();
    }

    // Function to show crop details
    function showCropDetails(cropId) {
        const cropRow = document.querySelector(`.crop-row[data-crop-id="${cropId}"]`);
        if (!cropRow) return;

        const cropName = cropRow.querySelector('strong').textContent;
        const cropInfo = document.getElementById('crop-info');

        // Get crop data from the row
        const cost = cropRow.querySelector('td:nth-child(2) span').textContent;
        const yield_per_acre = cropRow.querySelector('td:nth-child(3) span').textContent;
        const price = cropRow.querySelector('td:nth-child(4)').textContent;
        const revenue = cropRow.querySelector('td:nth-child(5)').textContent;
        const profit = cropRow.querySelector('td:nth-child(6) span').textContent;
        const roi = cropRow.querySelector('td:nth-child(7) span').textContent;
        const period = cropRow.querySelector('td:nth-child(8) span').textContent;

        // Update the crop info card
        cropInfo.innerHTML = `
            <div style="width: 100%; background-color: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); overflow: hidden;">
                <!-- Header -->
                <div style="background: linear-gradient(to right, #2E7D32, #4CAF50); padding: 15px; text-align: center; color: white;">
                    <h5 style="font-size: 1.2rem; font-weight: 600; margin-bottom: 5px;">${cropName}</h5>
                    <div style="font-size: 0.85rem; opacity: 0.9;">Crop Information</div>
                </div>

                <!-- Crop Details -->
                <div style="padding: 20px;">
                    <div class="row">
                        <div class="col-6 mb-3">
                            <div style="font-size: 0.8rem; color: #666; margin-bottom: 5px;">Cost per Acre</div>
                            <div style="font-size: 1rem; font-weight: 500;">${cost}</div>
                        </div>
                        <div class="col-6 mb-3">
                            <div style="font-size: 0.8rem; color: #666; margin-bottom: 5px;">Yield per Acre</div>
                            <div style="font-size: 1rem; font-weight: 500;">${yield_per_acre}</div>
                        </div>
                        <div class="col-6 mb-3">
                            <div style="font-size: 0.8rem; color: #666; margin-bottom: 5px;">Price per kg</div>
                            <div style="font-size: 1rem; font-weight: 500;">${price}</div>
                        </div>
                        <div class="col-6 mb-3">
                            <div style="font-size: 0.8rem; color: #666; margin-bottom: 5px;">Revenue</div>
                            <div style="font-size: 1rem; font-weight: 500;">${revenue}</div>
                        </div>
                        <div class="col-6 mb-3">
                            <div style="font-size: 0.8rem; color: #666; margin-bottom: 5px;">Profit</div>
                            <div style="font-size: 1rem; font-weight: 500; color: #28a745;">${profit}</div>
                        </div>
                        <div class="col-6 mb-3">
                            <div style="font-size: 0.8rem; color: #666; margin-bottom: 5px;">ROI</div>
                            <div style="font-size: 1rem; font-weight: 500; color: #fd7e14;">${roi}</div>
                        </div>
                    </div>
                </div>

                <!-- Growing Period -->
                <div style="display: flex; border-top: 1px solid #e9ecef;">
                    <div style="flex: 1; padding: 12px; text-align: center;">
                        <div style="font-size: 0.75rem; color: #666; margin-bottom: 5px;">Growing Period</div>
                        <div style="font-size: 0.9rem; color: #333;">
                            <i class="bi bi-calendar-fill me-1" style="font-size: 0.8rem;"></i>
                            ${period}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Season filtering functionality
    const seasonFilters = document.querySelectorAll('.season-filter');
    seasonFilters.forEach(filter => {
        filter.addEventListener('click', function() {
            const season = this.getAttribute('data-season');

            // Update active state
            seasonFilters.forEach(f => f.classList.remove('active'));
            this.classList.add('active');

            // Filter table rows
            cropRows.forEach(row => {
                if (season === 'all') {
                    row.style.display = '';
                } else {
                    const seasonBadge = row.querySelector('.season-badge');
                    const rowSeason = seasonBadge ? seasonBadge.textContent.toLowerCase() : '';

                    if (rowSeason.includes(season.toLowerCase())) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                }
            });
        });
    });

    // Table sorting functionality
    const sortIcons = document.querySelectorAll('.sort-icon');
    sortIcons.forEach(icon => {
        icon.addEventListener('click', function() {
            const sortBy = this.getAttribute('data-sort');
            sortTable(sortBy);
        });
    });

    function sortTable(sortBy) {
        const tableBody = document.getElementById('comparison-table-body');
        const rows = Array.from(tableBody.querySelectorAll('tr'));

        rows.sort((a, b) => {
            let aValue, bValue;

            switch(sortBy) {
                case 'name':
                    aValue = a.querySelector('strong').textContent;
                    bValue = b.querySelector('strong').textContent;
                    return aValue.localeCompare(bValue);
                case 'cost':
                    aValue = parseFloat(a.querySelector('td:nth-child(2) span').textContent.replace('₹', '').replace(',', ''));
                    bValue = parseFloat(b.querySelector('td:nth-child(2) span').textContent.replace('₹', '').replace(',', ''));
                    break;
                case 'yield':
                    aValue = parseFloat(a.querySelector('td:nth-child(3) span').textContent.replace(' kg', '').replace(',', ''));
                    bValue = parseFloat(b.querySelector('td:nth-child(3) span').textContent.replace(' kg', '').replace(',', ''));
                    break;
                case 'price':
                    aValue = parseFloat(a.querySelector('td:nth-child(4)').textContent.replace('₹', '').replace(',', ''));
                    bValue = parseFloat(b.querySelector('td:nth-child(4)').textContent.replace('₹', '').replace(',', ''));
                    break;
                case 'revenue':
                    aValue = parseFloat(a.querySelector('td:nth-child(5)').textContent.replace('₹', '').replace(',', ''));
                    bValue = parseFloat(b.querySelector('td:nth-child(5)').textContent.replace('₹', '').replace(',', ''));
                    break;
                case 'profit':
                    aValue = parseFloat(a.querySelector('td:nth-child(6) span').textContent.replace('₹', '').replace(',', ''));
                    bValue = parseFloat(b.querySelector('td:nth-child(6) span').textContent.replace('₹', '').replace(',', ''));
                    break;
                case 'roi':
                    aValue = parseFloat(a.querySelector('td:nth-child(7) span').textContent.replace('%', ''));
                    bValue = parseFloat(b.querySelector('td:nth-child(7) span').textContent.replace('%', ''));
                    break;
                case 'period':
                    aValue = parseInt(a.querySelector('td:nth-child(8) span').textContent.replace(' days', ''));
                    bValue = parseInt(b.querySelector('td:nth-child(8) span').textContent.replace(' days', ''));
                    break;
                default:
                    return 0;
            }

            return bValue - aValue; // Descending order
        });

        // Clear and re-append rows
        rows.forEach(row => tableBody.appendChild(row));

        // Add highlight animation
        rows.forEach(row => {
            row.classList.add('highlight-sort');
            setTimeout(() => {
                row.classList.remove('highlight-sort');
            }, 1000);
        });
    }
});
