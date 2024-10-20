import requests
from datetime import datetime
from django.conf import settings
from financial_data.models import StockData
import logging
from .rate_limiter import rate_limit
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.core.cache import cache

logger = logging.getLogger(__name__)

BASE_URL = 'https://www.alphavantage.co/query'

def fetch_stock_data(symbol, start_date, end_date):

    if cache.get('api_limit_reached'):
        raise ValueError("Daily API limit reached. Please try again tomorrow.")

    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': symbol,
        'apikey': settings.ALPHA_VANTAGE_API_KEY,
        'outputsize': 'full'
    }

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if 'Information' in data and 'standard API rate limit' in data['Information']:
            cache.set('api_limit_reached', True, 86400)  # Set for 24 hours
            raise ValueError("API rate limit reached. Please try again tomorrow.")

        if 'Time Series (Daily)' not in data:
            logger.error(f"Unexpected response format for {symbol}: {data}")
            raise ValueError(f"Failed to fetch data for {symbol}: Unexpected response format")

        daily_data = data['Time Series (Daily)']
        stock_data_list = []

        for date_str, values in daily_data.items():
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            if start_date <= date <= end_date:
                stock_data = StockData(
                    symbol=symbol,
                    date=date,
                    open_price=float(values['1. open']),
                    high_price=float(values['2. high']),
                    low_price=float(values['3. low']),
                    close_price=float(values['4. close']),
                    volume=int(values['5. volume'])
                )
                stock_data_list.append(stock_data)

        if not stock_data_list:
            raise ValueError(f"No data found for symbol {symbol} between {start_date} and {end_date}")

        StockData.objects.bulk_create(stock_data_list, ignore_conflicts=True)
        logger.info(f"Successfully fetched and stored data for {symbol} from {start_date} to {end_date}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {symbol}: {e}")
        raise ValueError(f"Failed to fetch data for {symbol}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error for {symbol}: {e}")
        raise ValueError(f"Failed to fetch data for {symbol}: {str(e)}")

def get_company_overview(symbol):
    params = {
        'function': 'OVERVIEW',
        'symbol': symbol,
        'apikey': settings.ALPHA_VANTAGE_API_KEY
    }

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch company overview for {symbol}: {e}")
        raise

def get_intraday_data(symbol, interval='5min'):
    params = {
        'function': 'TIME_SERIES_INTRADAY',
        'symbol': symbol,
        'interval': interval,
        'apikey': settings.ALPHA_VANTAGE_API_KEY
    }

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch intraday data for {symbol}: {e}")
        raise

def setup_alpha_vantage_api():
    api_key = getattr(settings, 'ALPHA_VANTAGE_API_KEY', None)
    if not api_key:
        logger.error("Alpha Vantage API key is not set in settings")
        raise ValueError("Alpha Vantage API key is not set")
    logger.info("Alpha Vantage API setup completed successfully.")
    return api_key

def test_alpha_vantage_connection():
    api_key = setup_alpha_vantage_api()
    if not api_key:
        raise ImproperlyConfigured("Alpha Vantage API key is not set")
    
    symbol = 'AAPL'  
    try:
        
        overview = get_company_overview(symbol)
        print(f"Successfully fetched company overview for {symbol}")
        print(f"Company Name: {overview.get('Name')}")
        print(f"Industry: {overview.get('Industry')}")
        
      
        intraday = get_intraday_data(symbol)
        print(f"\nSuccessfully fetched intraday data for {symbol}")
        latest_refresh = intraday['Meta Data']['3. Last Refreshed']
        print(f"Last Refreshed: {latest_refresh}")
        
        
        from datetime import date, timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=7) 
        fetch_stock_data(symbol, start_date, end_date)
        print(f"\nSuccessfully fetched stock data for {symbol} from {start_date} to {end_date}")
        
        print("\nAll tests passed successfully!")
    except Exception as e:
        print(f"Error occurred: {str(e)}")
