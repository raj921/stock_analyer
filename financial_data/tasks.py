from celery import shared_task
from datetime import date, timedelta
from .utils.alpha_vantage_api import fetch_stock_data, get_company_overview
from .models import CompanyOverview
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def update_stock_data(self, symbol):
    end_date = date.today()
    start_date = end_date - timedelta(days=730)  # 2 years of data
    try:
        fetch_stock_data(symbol, start_date, end_date)
        logger.info(f"Successfully updated stock data for {symbol}")
    except Exception as e:
        logger.error(f"Error updating stock data for {symbol}: {e}")
        self.retry(exc=e)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def update_company_overview(self, symbol):
    try:
        overview = get_company_overview(symbol)
        CompanyOverview.objects.update_or_create(
            symbol=symbol,
            defaults={
                'name': overview.get('Name'),
                'description': overview.get('Description'),
                'exchange': overview.get('Exchange'),
                'currency': overview.get('Currency'),
                'country': overview.get('Country'),
                'sector': overview.get('Sector'),
                'industry': overview.get('Industry'),
                'market_capitalization': int(overview.get('MarketCapitalization', 0)),
                'pe_ratio': float(overview.get('PERatio')) if overview.get('PERatio') else None,
                'dividend_yield': float(overview.get('DividendYield')) if overview.get('DividendYield') else None,
                'beta': float(overview.get('Beta')) if overview.get('Beta') else None,
                'fifty_two_week_high': float(overview.get('52WeekHigh', 0)),
                'fifty_two_week_low': float(overview.get('52WeekLow', 0)),
            }
        )
        logger.info(f"Successfully updated company overview for {symbol}")
    except Exception as e:
        logger.error(f"Error updating company overview for {symbol}: {e}")
        self.retry(exc=e)
