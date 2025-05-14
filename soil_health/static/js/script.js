document.addEventListener('DOMContentLoaded', function() {
    // Form submission
    const soilForm = document.getElementById('soil-form');
    const resultsSection = document.getElementById('results-section');
    
    soilForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get form data
        const formData = new FormData(soilForm);
        
        // Show loading state
        document.querySelector('button[type="submit"]').innerHTML = 
            '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
        
        // Send request to server
        fetch('/predict', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayResults(data.result);
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while processing your request.');
        })
        .finally(() => {
            // Reset button
            document.querySelector('button[type="submit"]').innerHTML = 'Assess Soil Health';
        });
    });
    
    // Display results
    function displayResults(result) {
        // Show results section
        resultsSection.classList.remove('d-none');
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth' });
        
        // Display fertility level
        const fertilityLevel = document.getElementById('fertility-level');
        fertilityLevel.textContent = result.fertility_level;
        fertilityLevel.className = ''; // Reset classes
        fertilityLevel.classList.add('text-center', `fertility-${result.fertility_level.toLowerCase()}`);
        
        // Display quality score
        const qualityScore = document.getElementById('quality-score');
        qualityScore.textContent = result.quality_score + '/100';
        
        // Update progress bar
        const qualityProgress = document.getElementById('quality-progress');
        qualityProgress.style.width = `${result.quality_score}%`;
        qualityProgress.className = 'progress-bar'; // Reset classes
        
        // Add color class based on score
        if (result.quality_score >= 70) {
            qualityProgress.classList.add('quality-high');
        } else if (result.quality_score >= 40) {
            qualityProgress.classList.add('quality-medium');
        } else {
            qualityProgress.classList.add('quality-low');
        }
        
        // Display suitable crops
        const suitableCrops = document.getElementById('suitable-crops');
        suitableCrops.innerHTML = ''; // Clear previous results
        
        if (result.suitable_crops.length > 0) {
            result.suitable_crops.forEach(crop => {
                const li = document.createElement('li');
                li.className = 'list-group-item';
                li.textContent = crop;
                suitableCrops.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.className = 'list-group-item text-danger';
            li.textContent = 'No suitable crops found for this soil profile';
            suitableCrops.appendChild(li);
        }
    }
    
    // Sample profiles
    const sampleProfiles = document.querySelectorAll('.sample-profile');
    
    sampleProfiles.forEach(profile => {
        profile.addEventListener('click', function() {
            const profileType = this.getAttribute('data-profile');
            
            // Fill form with sample data
            switch (profileType) {
                case 'high':
                    document.getElementById('nitrogen').value = '80';
                    document.getElementById('phosphorus').value = '75';
                    document.getElementById('potassium').value = '85';
                    document.getElementById('ph').value = '6.5';
                    document.getElementById('ec').value = '1.2';
                    document.getElementById('moisture').value = '60';
                    document.getElementById('organic_matter').value = '7.5';
                    break;
                case 'medium':
                    document.getElementById('nitrogen').value = '45';
                    document.getElementById('phosphorus').value = '40';
                    document.getElementById('potassium').value = '50';
                    document.getElementById('ph').value = '7.0';
                    document.getElementById('ec').value = '2.0';
                    document.getElementById('moisture').value = '45';
                    document.getElementById('organic_matter').value = '4.0';
                    break;
                case 'low':
                    document.getElementById('nitrogen').value = '15';
                    document.getElementById('phosphorus').value = '10';
                    document.getElementById('potassium').value = '20';
                    document.getElementById('ph').value = '5.0';
                    document.getElementById('ec').value = '3.5';
                    document.getElementById('moisture').value = '30';
                    document.getElementById('organic_matter').value = '1.5';
                    break;
            }
            
            // Scroll to form
            soilForm.scrollIntoView({ behavior: 'smooth' });
        });
    });
});
