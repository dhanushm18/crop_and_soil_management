import requests
import json

# Test the API endpoint
try:
    # Define test data
    test_data = {
        "N": 90,
        "P": 42,
        "K": 43,
        "temperature": 20.87,
        "humidity": 82.00,
        "ph": 6.5,
        "rainfall": 202.93
    }
    
    # Make a request to the API
    response = requests.post("http://localhost:5000/api/predict", json=test_data)
    
    # Print the response
    print("Status Code:", response.status_code)
    print("Response:", response.json())
    
except Exception as e:
    print("Error:", str(e))
    print("Note: Make sure the Flask app is running on http://localhost:5000")
