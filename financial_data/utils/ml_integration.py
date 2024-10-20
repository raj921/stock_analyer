import joblib
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from financial_data.models import StockData, Prediction
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(settings.BASE_DIR, 'financial_data', 'models', 'pretrained_model.pkl')

def get_or_create_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    else:
        model = LinearRegression()
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        joblib.dump(model, MODEL_PATH)
        return model

model = get_or_create_model()

def train_model(symbol, start_date, end_date):
    stock_data = StockData.objects.filter(
        symbol=symbol,
        date__range=(start_date, end_date)
    ).order_by('date').values('date', 'close_price')

    if not stock_data:
        raise ValueError(f"No data found for symbol {symbol} between {start_date} and {end_date}")

    df = pd.DataFrame(stock_data)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)

    # Create features
    for i in range(1, 6):
        df[f'price_{i}d_ago'] = df['close_price'].shift(i)

    df.dropna(inplace=True)

    X = df[['price_1d_ago', 'price_2d_ago', 'price_3d_ago', 'price_4d_ago', 'price_5d_ago']]
    y = df['close_price']

    model.fit(X, y)
    joblib.dump(model, MODEL_PATH)

def prepare_data(symbol, start_date, end_date):
    stock_data = StockData.objects.filter(
        symbol=symbol,
        date__range=(start_date, end_date)
    ).order_by('date').values('date', 'close_price')

    if not stock_data:
        raise ValueError(f"No data found for symbol {symbol} between {start_date} and {end_date}")

    df = pd.DataFrame(stock_data)
    df.set_index('date', inplace=True)
    df['return'] = df['close_price'].pct_change()
    df['MA5'] = df['close_price'].rolling(window=5).mean()
    df['MA20'] = df['close_price'].rolling(window=20).mean()
    df = df.dropna()

    features = ['close_price', 'return', 'MA5', 'MA20']
    X = df[features]
    
    return X, df.index

def predict_stock_prices(symbol, start_date, end_date):
    try:
        logger.debug(f"Starting prediction for {symbol} from {start_date} to {end_date}")
        train_model(symbol, start_date, end_date)

        stock_data = StockData.objects.filter(
            symbol=symbol,
            date__range=(start_date, end_date)
        ).order_by('date').values('date', 'close_price')

        logger.debug(f"Fetched {len(stock_data)} stock data points")

        df = pd.DataFrame(stock_data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)

        for i in range(1, 6):
            df[f'price_{i}d_ago'] = df['close_price'].shift(i)

        df.dropna(inplace=True)

        X = df[['price_1d_ago', 'price_2d_ago', 'price_3d_ago', 'price_4d_ago', 'price_5d_ago']]
        
        predictions = model.predict(X)
        
        prediction_data = [
            Prediction(symbol=symbol, date=date, predicted_price=price)
            for date, price in zip(df.index, predictions)
        ]

        Prediction.objects.filter(symbol=symbol, date__range=(start_date, end_date)).delete()
        Prediction.objects.bulk_create(prediction_data)

        logger.debug(f"Generated and saved {len(prediction_data)} predictions")

        return prediction_data  

    except Exception as e:
        logger.error(f"Error in predict_stock_prices: {str(e)}")
        raise

def compare_predictions(symbol, start_date, end_date):
    predictions = Prediction.objects.filter(
        symbol=symbol,
        date__range=(start_date, end_date)
    ).values('date', 'predicted_price')
    
    actual_prices = StockData.objects.filter(
        symbol=symbol,
        date__range=(start_date, end_date)
    ).values('date', 'close_price')
    
    df_pred = pd.DataFrame(predictions)
    df_actual = pd.DataFrame(actual_prices)
    
    df_combined = pd.merge(df_pred, df_actual, on='date', how='outer')
    df_combined['error'] = df_combined['predicted_price'] - df_combined['close_price']
    df_combined['absolute_error'] = abs(df_combined['error'])
    
    mse = (df_combined['error'] ** 2).mean()
    mae = df_combined['absolute_error'].mean()
    
    return {
        'mse': mse,
        'mae': mae,
        'comparison': df_combined.to_dict(orient='records')
    }
