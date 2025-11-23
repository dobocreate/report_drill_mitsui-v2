import pandas as pd
import numpy as np
from pathlib import Path
import os

# Create data directory
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# Generate dummy data
def generate_dummy_data(filename, length=45, interval=0.02):
    steps = int(length / interval)
    depth = np.linspace(0, length, steps)
    
    # Simulate energy data with some random noise and trends
    base_energy = 500
    noise = np.random.normal(0, 50, steps)
    trend = np.sin(depth * 0.5) * 100
    energy = base_energy + noise + trend
    energy = np.clip(energy, 0, 1000)
    
    df = pd.DataFrame({
        'x:TD(m)': depth,
        'Ene-M': energy,
        'Press-M': np.random.uniform(10, 20, steps),
        'Rot-M': np.random.uniform(50, 100, steps),
        'Feed-M': np.random.uniform(20, 40, steps),
        'W-Time': np.random.uniform(0, 10, steps)
    })
    
    # Add header rows to simulate the actual data format (header at row 2, index 1)
    # We'll just write the dataframe directly for now, assuming header_row=0 for simplicity in this script, 
    # but the app uses header_row=1 by default. Let's match the app's expectation.
    # If app expects header at index 1 (2nd row), row 0 is metadata.
    
    with open(data_dir / filename, 'w', encoding='shift_jis') as f:
        f.write("Machine,Drill,Date,Time\n") # Row 0: Metadata
        df.to_csv(f, index=False, lineterminator='\n') # Row 1: Header, Row 2+: Data

files = [
    "2025_11_17_12_33_57_L.csv",
    "2025_11_17_12_33_57_M.csv",
    "2025_11_17_12_33_57_R.csv"
]

for file in files:
    generate_dummy_data(file)
    print(f"Created {file}")
