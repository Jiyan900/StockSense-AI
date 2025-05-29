import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import os
from db_operations import (
    get_or_create_stock, 
    save_stock_prices, 
    get_stock_prices
)

def get_stock_data(symbol, start_date, end_date):
    """
    Fetch stock data from Yahoo Finance and save to database
    
    Args:
        symbol (str): Stock symbol
        start_date: Start date for data
        end_date: End date for data
        
    Returns:
        pd.DataFrame: DataFrame with stock data
    """
    try:
        # First, try to get data from the database
        db_data = get_stock_prices(symbol, start_date, end_date)

        # If we have complete data in the database, use it
        if db_data is not None and not db_data.empty and len(db_data) >= (end_date - start_date).days * 0.7:
            print(f"Using cached data for {symbol} from database")
            return db_data

        # Otherwise, fetch from Yahoo Finance
        print(f"Fetching fresh data for {symbol} from Yahoo Finance")
        stock = yf.Ticker(symbol)
        df = stock.history(start=start_date, end=end_date)

        # Check if data is empty
        if df.empty:
            raise ValueError(f"No data found for {symbol}")

        # Reset index to make Date a column
        df = df.reset_index()

        # Convert date to datetime if it's not already
        df['Date'] = pd.to_datetime(df['Date'])

        # Set date as index again
        df = df.set_index('Date')

        # Get company info and store in database
        info = stock.info

        # Save the stock to the database
        get_or_create_stock(
            symbol=symbol,
            name=info.get('shortName', symbol),
            sector=info.get('sector'),
            industry=info.get('industry'),
            description=info.get('longBusinessSummary'),
            market_cap=info.get('marketCap', 0)
        )

        # Save the price data to the database
        save_stock_prices(symbol, df)

        return df

    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        current_date = datetime.datetime.now()
        dates = [current_date - datetime.timedelta(days=i) for i in range(30)]
        df = pd.DataFrame({
            'Date': dates,
            'Open': [np.nan] * 30,
            'High': [np.nan] * 30,
            'Low': [np.nan] * 30,
            'Close': [np.nan] * 30,
            'Volume': [np.nan] * 30
        })
        df = df.set_index('Date')
        return df

def get_company_info(symbol):
    """
    Get company information for a given stock symbol
    
    Args:
        symbol (str): Stock symbol
        
    Returns:
        dict: Dictionary with company information
    """
    try:
        stock = yf.Ticker(symbol)
        info = stock.info

        company_info = {
            'name': info.get('shortName', 'Unknown'),
            'sector': info.get('sector', 'Unknown'),
            'industry': info.get('industry', 'Unknown'),
            'description': info.get('longBusinessSummary', 'No description available.'),
            'market_cap': info.get('marketCap', 0),
            'pe_ratio': info.get('trailingPE', 0),
            'dividend_yield': info.get('dividendYield', 0),
            'revenue': info.get('totalRevenue', 0),
            'eps': info.get('trailingEps', 0)
        }

        get_or_create_stock(
            symbol=symbol,
            name=company_info['name'],
            sector=company_info['sector'],
            industry=company_info['industry'],
            description=company_info['description'],
            market_cap=company_info['market_cap']
        )

        return company_info

    except Exception as e:
        print(f"Error fetching company info for {symbol}: {e}")
        return {
            'name': symbol,
            'sector': 'Unknown',
            'industry': 'Unknown',
            'description': 'Information not available.',
            'market_cap': 0,
            'pe_ratio': 0,
            'dividend_yield': 0,
            'revenue': 0,
            'eps': 0
        }

def get_popular_stocks():
    """
    Return a list of popular stocks, including US and Indian companies
    
    Returns:
        list: List of dictionaries with stock symbols and names
    """
    popular_stocks = [
        # US stocks
        {'symbol': 'AAPL', 'name': 'Apple Inc.'},
        {'symbol': 'MSFT', 'name': 'Microsoft Corp.'},
        {'symbol': 'GOOGL', 'name': 'Alphabet Inc.'},
        {'symbol': 'AMZN', 'name': 'Amazon.com Inc.'},
        {'symbol': 'TSLA', 'name': 'Tesla Inc.'},
        {'symbol': 'META', 'name': 'Meta Platforms Inc.'},
        {'symbol': 'NVDA', 'name': 'NVIDIA Corp.'},
        {'symbol': 'JPM', 'name': 'JPMorgan Chase & Co.'},
        # Indian stocks
        {'symbol': 'RELIANCE.NS', 'name': 'Reliance Industries'},
        {'symbol': 'TCS.NS', 'name': 'Tata Consultancy Services'},
        {'symbol': 'INFY.NS', 'name': 'Infosys'},
        {'symbol': 'HDFCBANK.NS', 'name': 'HDFC Bank'},
        {'symbol': 'ICICIBANK.NS', 'name': 'ICICI Bank'},
        {'symbol': 'ITC.NS', 'name': 'ITC Ltd'},
        {'symbol': 'SBIN.NS', 'name': 'State Bank of India'},
        {'symbol': 'LT.NS', 'name': 'Larsen & Toubro'}
    ]

    return popular_stocks

def search_stocks(query):
    """
    Search for stocks by symbol or name (US and Indian)

    Args:
        query (str): Search query
        
    Returns:
        list: List of matching stocks
    """
    all_stocks = {
        # US stocks
        'AAPL': 'Apple Inc.',
        'MSFT': 'Microsoft Corporation',
        'GOOGL': 'Alphabet Inc.',
        'GOOG': 'Alphabet Inc. (Class C)',
        'AMZN': 'Amazon.com Inc.',
        'TSLA': 'Tesla Inc.',
        'META': 'Meta Platforms Inc.',
        'NVDA': 'NVIDIA Corporation',
        'BRK-B': 'Berkshire Hathaway Inc.',
        'JPM': 'JPMorgan Chase & Co.',
        'JNJ': 'Johnson & Johnson',
        'V': 'Visa Inc.',
        'PG': 'Procter & Gamble Co.',
        'UNH': 'UnitedHealth Group Inc.',
        'HD': 'Home Depot Inc.',
        'BAC': 'Bank of America Corp.',
        'MA': 'Mastercard Inc.',
        'XOM': 'Exxon Mobil Corporation',
        'DIS': 'Walt Disney Co.',
        'NFLX': 'Netflix Inc.',
        'PYPL': 'PayPal Holdings Inc.',
        'INTC': 'Intel Corporation',
        'CSCO': 'Cisco Systems Inc.',
        'VZ': 'Verizon Communications Inc.',
        'ADBE': 'Adobe Inc.',
        'PFE': 'Pfizer Inc.',
        'CRM': 'Salesforce Inc.',
        'CMCSA': 'Comcast Corporation',
        'KO': 'Coca-Cola Co.',
        'PEP': 'PepsiCo Inc.',
        # Indian stocks
        'RELIANCE.NS': 'Reliance Industries',
        'TCS.NS': 'Tata Consultancy Services',
        'INFY.NS': 'Infosys Limited',
        'HDFCBANK.NS': 'HDFC Bank',
        'ICICIBANK.NS': 'ICICI Bank',
        'ITC.NS': 'ITC Ltd',
        'SBIN.NS': 'State Bank of India',
        'LT.NS': 'Larsen & Toubro'
    }

    query = query.upper()
    results = []

    for symbol, name in all_stocks.items():
        if query in symbol.upper() or query in name.upper():
            results.append({
                'symbol': symbol,
                'name': name
            })

    return results[:10]

