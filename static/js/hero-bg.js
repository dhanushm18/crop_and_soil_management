// This script adds a hero background image using a data URI to avoid needing to download an image file

document.addEventListener('DOMContentLoaded', function() {
    // Check if hero section exists
    const heroSection = document.querySelector('.hero-section');
    if (heroSection) {
        // Set a gradient background as fallback
        heroSection.style.background = 'linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.6)), url("https://images.unsplash.com/photo-1500382017468-9049fed747ef?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1920&q=80")';
        heroSection.style.backgroundSize = 'cover';
        heroSection.style.backgroundPosition = 'center';
    }

    // Add images to feature cards
    const featureImages = {
        'Crop Recommendation': 'https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=240&h=240&q=80',
        'Fertilizer Recommendation': 'https://images.unsplash.com/photo-1592982537447-7440770cbfc9?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=240&h=240&q=80',
        'Plant Disease Detection': 'https://images.unsplash.com/photo-1530836369250-ef72a3f5cda8?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=240&h=240&q=80',
        'Agriculture Chatbot': 'https://images.unsplash.com/photo-1577563908411-5077b6dc7624?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=240&h=240&q=80',
        'Soil Quality Dashboard': 'https://images.unsplash.com/photo-1605000797499-95a51c5269ae?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=240&h=240&q=80'
    };

    // Find all feature cards and set their images
    document.querySelectorAll('.feature-card h3').forEach(heading => {
        const title = heading.textContent.trim();
        if (featureImages[title]) {
            const imgElement = heading.parentElement.querySelector('img');
            if (imgElement) {
                imgElement.src = featureImages[title];
                imgElement.onerror = null; // Remove the onerror handler since we're setting a valid URL
            }
        }
    });
});
