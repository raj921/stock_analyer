from django.test import TestCase
from financial_data.utils.backtesting import backtest_strategy
from financial_data.models import StockData
from datetime import date, timedelta

class BacktestingTestCase(TestCase):
    def setUp(self):
        symbol = 'AAPL'
        start_date = date(2020, 1, 1)
        for i in range(300):  
            StockData.objects.create(
                symbol=symbol,
                date=start_date + timedelta(days=i),
                open_price=100 + i,
                high_price=105 + i,
                low_price=95 + i,
                close_price=102 + i,
                volume=1000000
            )

    def test_backtest_strategy(self):
        params = {
            'symbol': 'AAPL',
            'start_date': date(2020, 1, 1),
            'end_date': date(2020, 12, 31),
            'initial_investment': 10000,
            'short_window': 50,
            'long_window': 200
        }
        result = backtest_strategy(params)

        self.assertIn('backtest_id', result)
        self.assertEqual(result['symbol'], 'AAPL')
        self.assertIsInstance(result['total_return'], float)
        self.assertIsInstance(result['max_drawdown'], float)
        self.assertIsInstance(result['num_trades'], int)

    def test_backtest_strategy_no_data(self):
        params = {
            'symbol': 'NONEXISTENT',
            'start_date': date(2020, 1, 1),
            'end_date': date(2020, 12, 31),
            'initial_investment': 10000
        }
        with self.assertRaises(ValueError):
            backtest_strategy(params)
