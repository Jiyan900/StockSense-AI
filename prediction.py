import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import datetime

def calculate_technical_indicators(df):
    """
    Calculate technical indicators for the given DataFrame
    
    Args:
        df (pd.DataFrame): DataFrame with OHLCV data
        
    Returns:
        pd.DataFrame: DataFrame with additional technical indicators
    """
    # Create a copy of the DataFrame to avoid modifying the original
    df_temp = df.copy()
    
    # Calculate Moving Averages
    df_temp['MA20'] = df_temp['Close'].rolling(window=20).mean()
    df_temp['MA50'] = df_temp['Close'].rolling(window=50).mean()
    
    # Calculate RSI (Relative Strength Index)
    delta = df_temp['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
    
    rs = gain / loss
    df_temp['RSI'] = 100 - (100 / (1 + rs))
    
    # Calculate MACD (Moving Average Convergence Divergence)
    exp1 = df_temp['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df_temp['Close'].ewm(span=26, adjust=False).mean()
    df_temp['MACD'] = exp1 - exp2
    df_temp['Signal_Line'] = df_temp['MACD'].ewm(span=9, adjust=False).mean()
    
    # Calculate Bollinger Bands
    df_temp['MA20_std'] = df_temp['Close'].rolling(window=20).std()
    df_temp['Upper_Band'] = df_temp['MA20'] + (df_temp['MA20_std'] * 2)
    df_temp['Lower_Band'] = df_temp['MA20'] - (df_temp['MA20_std'] * 2)
    
    # Calculate Average True Range (ATR)
    high_low = df_temp['High'] - df_temp['Low']
    high_close = np.abs(df_temp['High'] - df_temp['Close'].shift())
    low_close = np.abs(df_temp['Low'] - df_temp['Close'].shift())
    
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df_temp['ATR'] = true_range.rolling(window=14).mean()
    
    # Fill NaN values
    df_temp = df_temp.bfill()
    
    return df_temp

def create_features(df):
    """
    Create features for the prediction model
    
    Args:
        df (pd.DataFrame): DataFrame with stock data
        
    Returns:
        tuple: (X, y) where X is the feature matrix and y is the target vector
    """
    # Create a new DataFrame for features
    df_features = df.copy()
    
    # Create consistent lag features - only specific lags to avoid errors
    consistent_lags = [1, 2, 3, 5, 10]
    for lag in consistent_lags:
        df_features[f'lag_{lag}'] = df_features['Close'].shift(lag)
    
    # Create return features
    for lag in consistent_lags:
        df_features[f'return_{lag}'] = (df_features['Close'] / df_features[f'lag_{lag}']) - 1
    
    # Add technical indicators as features
    feature_columns = [
        'Open', 'High', 'Low', 'Close', 'Volume',
        'MA20', 'MA50', 'RSI', 'MACD', 'Signal_Line',
        'Upper_Band', 'Lower_Band', 'ATR'
    ]
    
    # Add lag and return features
    for lag in consistent_lags:
        feature_columns.append(f'lag_{lag}')
        feature_columns.append(f'return_{lag}')
    
    # Remove NaN values
    df_features = df_features.dropna()
    
    # Define features and target
    X = df_features[feature_columns]
    y = df_features['Close']
    
    return X, y

def predict_stock_trend(df, prediction_days=30):
    """
    Predict stock trend using a Random Forest model
    
    Args:
        df (pd.DataFrame): DataFrame with stock data
        prediction_days (int): Number of days to predict
        
    Returns:
        tuple: (pred_df, accuracy, confidence)
            - pred_df: DataFrame with predicted prices
            - accuracy: Model accuracy (%)
            - confidence: Confidence score (%)
    """
    # Calculate technical indicators if not already present
    if 'RSI' not in df.columns:
        df = calculate_technical_indicators(df)
    
    # Create features
    X, y = create_features(df)
    
    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
    
    # Create and train the model
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate the model
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    # Calculate accuracy (as percentage of correct directional predictions)
    y_test_np = np.array(y_test)
    actual_direction = np.sign(y_test_np[1:] - y_test_np[:-1])
    pred_direction = np.sign(y_pred[1:] - y_pred[:-1])
    direction_accuracy = np.mean(actual_direction == pred_direction) * 100
    
    # Calculate confidence score based on R^2 and RMSE
    r2_score_float = float(r2)
    confidence = max(0.0, min(100.0, r2_score_float * 100.0))
    
    # Generate dates for prediction
    last_date = df.index[-1]
    future_dates = pd.date_range(start=last_date + datetime.timedelta(days=1), periods=prediction_days)
    
    # Create a DataFrame for prediction
    pred_df = pd.DataFrame(index=future_dates)
    
    # Predict future prices
    last_row = X.iloc[-1:].copy()
    predictions = []
    
    # Store list of feature names for consistent reference
    consistent_lags = [1, 2, 3, 5, 10]
    
    for i in range(prediction_days):
        # Make prediction for next day
        next_pred = model.predict(last_row)[0]
        predictions.append(next_pred)
        
        # Update last row for next prediction
        # Shift lag features (only update the lags we've defined)
        for j in range(len(consistent_lags)-1, 0, -1):
            current_lag = consistent_lags[j]
            prev_lag = consistent_lags[j-1]
            last_row[f'lag_{current_lag}'] = last_row[f'lag_{prev_lag}']
        
        # Update lag_1 with the latest prediction
        last_row['lag_1'] = next_pred
        
        # Update Close price (assumed to be the predicted price)
        last_row['Close'] = next_pred
        
        # Recalculate returns for our consistent lags
        for lag in consistent_lags:
            if last_row[f'lag_{lag}'].values[0] != 0:
                last_row[f'return_{lag}'] = (next_pred / last_row[f'lag_{lag}'].values[0]) - 1
    
    # Add predictions to DataFrame
    pred_df['Predicted'] = predictions
    
    # Add confidence interval
    std_dev = np.std(y_test - y_pred)
    multiplier = 1.96  # 95% confidence interval
    
    pred_df['Upper_Bound'] = pred_df['Predicted'] + (multiplier * std_dev * np.sqrt(np.arange(1, prediction_days + 1) / 10))
    pred_df['Lower_Bound'] = pred_df['Predicted'] - (multiplier * std_dev * np.sqrt(np.arange(1, prediction_days + 1) / 10))
    
    return pred_df, direction_accuracy, confidence
