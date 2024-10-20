import requests
from datetime import datetime
from django.conf import settings
from financial_data.models import StockData
import logging
import time

logger = logging.getLogger(__name__)

def fetch_stock_data(symbol, start_date, end_date):
    url = 'https://www.alphavantage.co/query'
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': symbol,
        'apikey': settings.ALPHA_VANTAGE_API_KEY,
        'outputsize': 'full'
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if 'Time Series (Daily)' not in data:
            if 'Note' in data:
                logger.warning(f"API call frequency exceeded: {data['Note']}")
                time.sleep(60)  # Wait for 60 seconds before retrying
                return fetch_stock_data(symbol, start_date, end_date)  # Retry the API call
            raise ValueError(f"Failed to fetch data from Alpha Vantage API for symbol {symbol}")

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

        StockData.objects.bulk_create(stock_data_list, ignore_conflicts=True)
        logger.info(f"Successfully fetched and stored data for {symbol}")
    except requests.RequestException as e:
        logger.error(f"HTTP error occurred while fetching data for {symbol}: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"Value error occurred while processing data for {symbol}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error occurred while fetching data for {symbol}: {str(e)}")
        raise

def setup_alpha_vantage_api():
    try:
        test_alpha_vantage_connection()
        logger.info("Alpha Vantage API setup completed successfully.")
    except Exception as e:
        logger.error(f"Error setting up Alpha Vantage API: {str(e)}")
        raise

def test_alpha_vantage_connection():
    url = 'https://www.alphavantage.co/query'
    params = {
        'function': 'TIME_SERIES_INTRADAY',
        'symbol': 'IBM',
        'interval': '5min',
        'apikey': settings.ALPHA_VANTAGE_API_KEY
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if "Error Message" in data:
            raise ValueError(f"Alpha Vantage API error: {data['Error Message']}")
        logger.info("Alpha Vantage API connection test successful")
    except requests.RequestException as e:
        logger.error(f"HTTP error occurred during Alpha Vantage API test: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"Value error occurred during Alpha Vantage API test: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error occurred during Alpha Vantage API test: {str(e)}")
        raise

def get_company_overview(symbol):
    url = 'https://www.alphavantage.co/query'
    params = {
        'function': 'OVERVIEW',
        'symbol': symbol,
        'apikey': settings.ALPHA_VANTAGE_API_KEY
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if "Error Message" in data:
            raise ValueError(f"Alpha Vantage API error: {data['Error Message']}")
        return data
    except requests.RequestException as e:
        logger.error(f"HTTP error occurred while fetching company overview for {symbol}: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"Value error occurred while fetching company overview for {symbol}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error occurred while fetching company overview for {symbol}: {str(e)}")
        raise

def get_intraday_data(symbol):
    url = 'https://www.alphavantage.co/query'
    params = {
        'function': 'TIME_SERIES_INTRADAY',
        'symbol': symbol,
        'interval': '5min',
        'apikey': settings.ALPHA_VANTAGE_API_KEY
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if "Error Message" in data:
            raise ValueError(f"Alpha Vantage API error: {data['Error Message']}")
        return data
    except requests.RequestException as e:
        logger.error(f"HTTP error occurred while fetching intraday data for {symbol}: {str(e)}")
        raise
    except ValueError as e:
        logger.error(f"Value error occurred while fetching intraday data for {symbol}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error occurred while fetching intraday data for {symbol}: {str(e)}")
        raise
