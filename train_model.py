# File: train_model.py

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler
import joblib
import numpy as np
import os

# Define file paths
DATA_FILE = os.path.join('data', 'c4_game_database.csv')
MODEL_FILE = os.path.join('models', 'c4_evaluation_model.joblib')
SCALER_FILE = os.path.join('models', 'c4_board_scaler.joblib')

def train_and_save_model():
    """
    Loads the dataset, trains a logistic regression model,
    and saves the model and scaler to the 'models' directory.
    """
    print(f"Loading dataset from {DATA_FILE}...")
    # Load the dataset
    try:
        df = pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        print(f"Error: Dataset not found at {DATA_FILE}")
        print("Please make sure 'c4_game_database.csv' is in the 'data' folder.")
        return

    # --- 1. Data Preprocessing ---
    
    # Drop the few rows with null values
    df.dropna(inplace=True)

    # Define features (X) and target (y)
    X = df.drop('winner', axis=1)
    y = df['winner']

    # Map target variable to integer classes for sklearn
    # Player 2 Win (-1.0) -> 0
    # Draw (0.0)         -> 1
    # Player 1 Win (1.0) -> 2
    y_mapped = y.map({-1.0: 0, 0.0: 1, 1.0: 2})
    
    if y_mapped.isnull().any():
        print("Error: Null values found after mapping 'winner' column. Check unique values.")
        return
    else:
        y_mapped = y_mapped.astype(int)

    # --- 2. Train-Test Split ---
    X_train, X_test, y_train, y_test = train_test_split(X, y_mapped, test_size=0.2, random_state=42, stratify=y_mapped)
    
    # --- 3. Scaling ---
    print("Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # --- 4. Model Training ---
    print("Training the AI evaluation model... (This may take a moment)")
    model = LogisticRegression(multi_class='multinomial', solver='lbfgs', max_iter=1000, random_state=42, n_jobs=-1)
    
    model.fit(X_train_scaled, y_train)
    print("Model training complete.")

    # --- 5. Model Evaluation ---
    y_pred = model.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nAccuracy of the AI's evaluation model: {accuracy * 100:.2f}%")

    # --- 6. Save the Model and Scaler ---
    # Ensure 'models' directory exists
    os.makedirs('models', exist_ok=True)
    
    joblib.dump(model, MODEL_FILE)
    joblib.dump(scaler, SCALER_FILE)
    print(f"Successfully saved model to '{MODEL_FILE}'")
    print(f"Successfully saved scaler to '{SCALER_FILE}'")

if __name__ == "__main__":
    train_and_save_model()