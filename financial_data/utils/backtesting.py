import pandas as pd
import numpy as np
from financial_data.models import StockData, BacktestResult
import logging

logger = logging.getLogger(__name__)

def calculate_moving_average(data, window):
    return data['close_price'].rolling(window=window).mean()

def backtest_strategy(params):
    symbol = params['symbol']
    start_date = params['start_date']
    end_date = params['end_date']
    initial_investment = params['initial_investment']
    short_window = params.get('short_window', 50)
    long_window = params.get('long_window', 200)

    
    stock_data = StockData.objects.filter(
        symbol=symbol,
        date__range=(start_date, end_date)
    ).order_by('date').values('date', 'close_price')

    if not stock_data:
        raise ValueError(f"No data found for symbol {symbol} between {start_date} and {end_date}")

    # Convert to DataFrame
    df = pd.DataFrame(stock_data)
    df.set_index('date', inplace=True)

    
    df['SMA_short'] = df['close_price'].rolling(window=short_window).mean()
    df['SMA_long'] = df['close_price'].rolling(window=long_window).mean()

   
    df['signal'] = np.where(df['SMA_short'] > df['SMA_long'], 1, 0)
    df['position'] = df['signal'].diff()

    position = 0
    balance = initial_investment
    trades = []

    
    for date, row in df.iterrows():
        if row['position'] == 1:  # Buy signal
            if balance > 0:
                position = balance / row['close_price']
                balance = 0
                trades.append(('buy', date, row['close_price']))
        elif row['position'] == -1:  # Sell signal
            if position > 0:
                balance = position * row['close_price']
                position = 0
                trades.append(('sell', date, row['close_price']))


    final_value = balance + position * df['close_price'].iloc[-1]
    total_return = (final_value - initial_investment) / initial_investment * 100
    max_drawdown = calculate_max_drawdown(df)
    num_trades = len(trades)

   
    result = BacktestResult.objects.create(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        initial_investment=initial_investment,
        final_value=final_value,
        total_return=total_return,
        max_drawdown=max_drawdown,
        num_trades=num_trades
    )

    return {
        'backtest_id': result.id,
        'symbol': symbol,
        'start_date': start_date,
        'end_date': end_date,
        'initial_investment': initial_investment,
        'final_value': final_value,
        'total_return': total_return,
        'max_drawdown': max_drawdown,
        'num_trades': num_trades
    }

def calculate_max_drawdown(df):
    df['cumulative_max'] = df['close_price'].cummax()
    df['drawdown'] = (df['close_price'] - df['cumulative_max']) / df['cumulative_max']
    return df['drawdown'].min() * 100
