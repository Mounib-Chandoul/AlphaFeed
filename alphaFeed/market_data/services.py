import yfinance as yf # Install via: pip install yfinance
from .models import Ticker, PriceHistory

def update_market_prices(symbol):
    # 1. Fetch data
    ticker_obj = Ticker.objects.get(symbol=symbol)
    data = yf.Ticker(symbol).history(period="1d")
    latest_price = data['Close'].iloc[-1]
    
    # 2. Save to database
    PriceHistory.objects.create(ticker=ticker_obj, price=latest_price)
    print(f"Updated {symbol} to {latest_price}")