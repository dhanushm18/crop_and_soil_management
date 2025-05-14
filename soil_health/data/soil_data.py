import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

def generate_synthetic_data(n_samples=500):
    """
    Generate synthetic soil data with the following parameters:
    - N (Nitrogen): 0-100 ppm
    - P (Phosphorus): 0-100 ppm
    - K (Potassium): 0-100 ppm
    - pH: 4.0-8.5
    - EC (Electrical Conductivity): 0-4 dS/m
    - Moisture: 0-100%
    - Organic Matter: 0-10%
    - Soil Fertility Level: Low, Medium, High
    - Soil Quality Score: 0-100
    """
    np.random.seed(42)
    
    # Generate random values for soil parameters
    nitrogen = np.random.uniform(0, 100, n_samples)
    phosphorus = np.random.uniform(0, 100, n_samples)
    potassium = np.random.uniform(0, 100, n_samples)
    ph = np.random.uniform(4.0, 8.5, n_samples)
    ec = np.random.uniform(0, 4, n_samples)
    moisture = np.random.uniform(0, 100, n_samples)
    organic_matter = np.random.uniform(0, 10, n_samples)
    
    # Create a dataframe
    df = pd.DataFrame({
        'nitrogen': nitrogen,
        'phosphorus': phosphorus,
        'potassium': potassium,
        'ph': ph,
        'ec': ec,
        'moisture': moisture,
        'organic_matter': organic_matter
    })
    
    # Calculate soil quality score based on the parameters
    # This is a simplified model - in reality, the relationship would be more complex
    scaler = MinMaxScaler()
    
    # Normalize pH to have higher scores for values around 6.5 (optimal for most crops)
    ph_score = 100 - 20 * np.abs(df['ph'] - 6.5)
    
    # Scale other parameters to 0-100 range
    n_score = scaler.fit_transform(df[['nitrogen']]) * 100
    p_score = scaler.fit_transform(df[['phosphorus']]) * 100
    k_score = scaler.fit_transform(df[['potassium']]) * 100
    ec_score = (1 - scaler.fit_transform(df[['ec']])) * 100  # Lower EC is better
    moisture_score = 100 - 4 * np.abs(df['moisture'] - 50)  # Optimal around 50%
    om_score = scaler.fit_transform(df[['organic_matter']]) * 100
    
    # Calculate overall quality score (weighted average)
    quality_score = (
        0.2 * n_score.flatten() + 
        0.2 * p_score.flatten() + 
        0.2 * k_score.flatten() + 
        0.15 * ph_score + 
        0.1 * ec_score.flatten() + 
        0.1 * moisture_score + 
        0.05 * om_score.flatten()
    )
    
    df['quality_score'] = quality_score.round(1)
    
    # Determine fertility level based on quality score
    fertility_conditions = [
        (df['quality_score'] < 40),
        (df['quality_score'] >= 40) & (df['quality_score'] < 70),
        (df['quality_score'] >= 70)
    ]
    fertility_values = ['Low', 'Medium', 'High']
    df['fertility_level'] = np.select(fertility_conditions, fertility_values)
    
    # Determine suitable crops based on soil parameters
    crops = {
        'Rice': (df['ph'] >= 5.0) & (df['ph'] <= 7.5) & (df['moisture'] > 60),
        'Wheat': (df['ph'] >= 6.0) & (df['ph'] <= 7.5) & (df['nitrogen'] > 40),
        'Corn': (df['ph'] >= 5.5) & (df['ph'] <= 7.5) & (df['potassium'] > 50),
        'Soybeans': (df['ph'] >= 6.0) & (df['ph'] <= 7.0) & (df['phosphorus'] > 40),
        'Cotton': (df['ph'] >= 5.5) & (df['ph'] <= 8.0) & (df['ec'] < 3),
        'Tomatoes': (df['ph'] >= 5.5) & (df['ph'] <= 7.5) & (df['organic_matter'] > 3),
        'Potatoes': (df['ph'] >= 4.8) & (df['ph'] <= 6.5) & (df['moisture'] > 40),
        'Carrots': (df['ph'] >= 5.5) & (df['ph'] <= 7.0) & (df['phosphorus'] > 30),
        'Lettuce': (df['ph'] >= 6.0) & (df['ph'] <= 7.0) & (df['nitrogen'] > 30),
        'Spinach': (df['ph'] >= 6.0) & (df['ph'] <= 7.5) & (df['nitrogen'] > 50)
    }
    
    # Create columns for each crop
    for crop, condition in crops.items():
        df[f'suitable_{crop.lower()}'] = condition
    
    # Create a suitable_crops column with a list of suitable crops
    df['suitable_crops'] = ''
    for i, row in df.iterrows():
        suitable = []
        for crop in crops.keys():
            if row[f'suitable_{crop.lower()}']:
                suitable.append(crop)
        df.at[i, 'suitable_crops'] = ', '.join(suitable)
        
    # Drop the individual crop columns
    for crop in crops.keys():
        df.drop(f'suitable_{crop.lower()}', axis=1, inplace=True)
    
    return df

def save_data():
    """Generate and save the synthetic data to a CSV file."""
    df = generate_synthetic_data()
    df.to_csv('data/soil_dataset.csv', index=False)
    print(f"Dataset with {len(df)} samples saved to data/soil_dataset.csv")
    return df

if __name__ == "__main__":
    save_data()
