import pandas as pd
from sklearn.linear_model import LinearRegression
from fastapi.responses import JSONResponse

def predict(training_data, current_data):
    # Convert input data to DataFrames
    training_df = pd.DataFrame(training_data)
    current_df = pd.DataFrame(current_data)

    # Ensure current_df only has one row (if there are more, select the first one)
    if len(current_df) > 1:
        current_df = current_df.head(1)

    # Create a mapping from 'nama_obat' to numeric values in the training DataFrame
    obat_mapping = {name: i for i, name in enumerate(training_df['nama_obat'])}

    # Add a new column to the training DataFrame with numeric values
    training_df['nama_obat_numeric'] = training_df['nama_obat'].map(obat_mapping)

    # Apply the same mapping to the current DataFrame
    current_df['nama_obat_numeric'] = current_df['nama_obat'].map(obat_mapping)

    # Handle rows in current_df where 'nama_obat' was not found in the training data
    current_df['nama_obat_numeric'] = current_df['nama_obat_numeric'].fillna(-1)

    # Prepare features and target for the model
    X = training_df[['stok_awal', 'nama_obat_numeric', 'bulan', 'tahun']]
    y = training_df['stok_akhir']

    # Create and fit the linear regression model
    model = LinearRegression()
    model.fit(X, y)

    # Prepare features for prediction
    X_predict = current_df[['stok_awal', 'nama_obat_numeric', 'bulan', 'tahun']]

    # Make predictions
    prediction = model.predict(X_predict)

    return prediction
