# Multi-Crop Profit Comparison Dashboard

A web application built with Flask to help farmers and agricultural professionals compare different crops based on profitability metrics and make informed decisions about which crops to plant for maximum profit.

## Features

- **Crop Comparison**: Compare multiple crops side by side based on various economic metrics
- **Profit Visualization**: Visual representation of profit and ROI for selected crops
- **Detailed Crop Information**: View detailed information about each crop
- **Profitability Analysis**: Analyze cost, revenue, profit, and ROI for each crop
- **Recommendations**: Get recommendations based on crop characteristics

## Technologies Used

- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, JavaScript
- **Data Visualization**: Chart.js
- **Styling**: Bootstrap 5

## Installation and Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies:
   ```
   pip install flask pandas matplotlib
   ```
5. Run the application:
   ```
   python app.py
   ```
6. Open your browser and navigate to `http://localhost:5000`

## Project Structure

```
├── app.py                  # Main Flask application
├── static/                 # Static files
│   ├── css/                # CSS files
│   │   └── style.css       # Custom styles
│   └── js/                 # JavaScript files
│       └── main.js         # Custom JavaScript
├── templates/              # HTML templates
│   ├── base.html           # Base template
│   ├── index.html          # Dashboard template
│   └── crop_detail.html    # Crop detail template
└── README.md               # Project documentation
```

## Usage

1. Open the dashboard
2. Select crops to compare from the checkbox list
3. Click "Compare Selected Crops" to visualize the comparison
4. Click on a crop in the table to view detailed information
5. Navigate to the crop detail page for in-depth analysis

## Domain: AIML

This project demonstrates the application of data analysis and visualization techniques to help in agricultural decision-making. Future enhancements could include:

- Machine learning models to predict crop prices
- AI-based recommendations based on soil and climate data
- Automated data collection from agricultural APIs
- Predictive analytics for future profitability

## License

This project is open source and available under the MIT License.
