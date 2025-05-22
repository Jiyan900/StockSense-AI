import datetime
import pandas as pd
from sqlalchemy import desc, func
from database import get_db_session, Stock, StockPrice, Watchlist, WatchlistItem, PredictionHistory, User


def get_or_create_stock(symbol, name, sector=None, industry=None, description=None, market_cap=None):
    """
    Get a stock from the database or create it if it doesn't exist
    
    Args:
        symbol (str): Stock symbol
        name (str): Company name
        sector (str, optional): Company sector
        industry (str, optional): Company industry
        description (str, optional): Company description
        market_cap (float, optional): Company market cap
        
    Returns:
        Stock: Stock object from the database
    """
    session = get_db_session()
    
    try:
        # Check if stock exists
        stock = session.query(Stock).filter(Stock.symbol == symbol).first()
        
        if not stock:
            # Create new stock
            stock = Stock(
                symbol=symbol,
                name=name,
                sector=sector,
                industry=industry,
                description=description,
                market_cap=market_cap,
                last_updated=datetime.datetime.utcnow()
            )
            session.add(stock)
            session.commit()
            # Refresh to make sure we have the complete object
            session.refresh(stock)
        else:
            # Update existing stock with new information if provided
            if name:
                stock.name = name
            if sector:
                stock.sector = sector
            if industry:
                stock.industry = industry
            if description:
                stock.description = description
            if market_cap:
                stock.market_cap = market_cap
            
            # Update last_updated attribute
            stock.last_updated = datetime.datetime.utcnow()
            session.commit()
            # Refresh to make sure we have the complete object
            session.refresh(stock)
        
        # Make a copy of the stock to return after session is closed
        stock_copy = Stock(
            id=stock.id,
            symbol=stock.symbol,
            name=stock.name,
            sector=stock.sector,
            industry=stock.industry,
            description=stock.description,
            market_cap=stock.market_cap,
            last_updated=stock.last_updated
        )
        
        return stock_copy
    
    except Exception as e:
        print(f"Error in get_or_create_stock: {e}")
        session.rollback()
        return None
    
    finally:
        # Always close the session
        session.close()


def save_stock_prices(stock_symbol, price_df):
    """
    Save stock price data to the database
    
    Args:
        stock_symbol (str): Stock symbol
        price_df (pd.DataFrame): DataFrame with stock price data
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        session = get_db_session()
        
        # Get stock from database
        stock = session.query(Stock).filter(Stock.symbol == stock_symbol).first()
        
        if not stock:
            session.close()
            return False
        
        # Process each row in the DataFrame
        for index, row in price_df.iterrows():
            # Convert numpy data types to Python native types
            open_price = float(row['Open']) if not pd.isna(row['Open']) else 0.0
            high_price = float(row['High']) if not pd.isna(row['High']) else 0.0
            low_price = float(row['Low']) if not pd.isna(row['Low']) else 0.0
            close_price = float(row['Close']) if not pd.isna(row['Close']) else 0.0
            volume = float(row['Volume']) if not pd.isna(row['Volume']) else 0.0
            
            # Convert timestamp to datetime
            date_val = pd.Timestamp(index).to_pydatetime()
            
            # Check if price data already exists for this date
            existing_price = session.query(StockPrice).filter(
                StockPrice.stock_id == stock.id,
                StockPrice.date == date_val
            ).first()
            
            if existing_price:
                # Update existing price data
                existing_price.open_price = open_price
                existing_price.high_price = high_price
                existing_price.low_price = low_price
                existing_price.close_price = close_price
                existing_price.volume = volume
            else:
                # Create new price data
                new_price = StockPrice(
                    stock_id=stock.id,
                    date=date_val,
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    volume=volume
                )
                session.add(new_price)
            
            # Commit after each row to avoid large transactions
            session.commit()
        
        session.close()
        return True
    
    except Exception as e:
        print(f"Error saving stock prices: {e}")
        try:
            session.rollback()
            session.close()
        except:
            pass
        return False


def get_stock_prices(stock_symbol, start_date, end_date):
    """
    Get stock price data from the database
    
    Args:
        stock_symbol (str): Stock symbol
        start_date (datetime): Start date
        end_date (datetime): End date
        
    Returns:
        pd.DataFrame: DataFrame with stock price data, or None if no data is available
    """
    try:
        session = get_db_session()
        
        # Get stock from database
        stock = session.query(Stock).filter(Stock.symbol == stock_symbol).first()
        
        if not stock:
            session.close()
            return None
        
        # Query price data
        prices = session.query(StockPrice).filter(
            StockPrice.stock_id == stock.id,
            StockPrice.date >= start_date,
            StockPrice.date <= end_date
        ).order_by(StockPrice.date).all()
        
        if not prices:
            session.close()
            return None
        
        # Convert to DataFrame
        data = {
            'Open': [price.open_price for price in prices],
            'High': [price.high_price for price in prices],
            'Low': [price.low_price for price in prices],
            'Close': [price.close_price for price in prices],
            'Volume': [price.volume for price in prices]
        }
        
        df = pd.DataFrame(data, index=[price.date for price in prices])
        
        session.close()
        return df
    
    except Exception as e:
        print(f"Error getting stock prices: {e}")
        session.close()
        return None


def save_prediction(stock_symbol, prediction_date, predictions_df):
    """
    Save prediction data to the database
    
    Args:
        stock_symbol (str): Stock symbol
        prediction_date (datetime): Date when prediction was made
        predictions_df (pd.DataFrame): DataFrame with prediction data
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        session = get_db_session()
        
        # Get stock from database
        stock = session.query(Stock).filter(Stock.symbol == stock_symbol).first()
        
        if not stock:
            session.close()
            return False
        
        # Process each row in the DataFrame
        for index, row in predictions_df.iterrows():
            # Create new prediction
            new_prediction = PredictionHistory(
                stock_id=stock.id,
                prediction_date=prediction_date,
                target_date=index,
                predicted_price=row['Predicted'],
                lower_bound=row.get('Lower_Bound'),
                upper_bound=row.get('Upper_Bound'),
                accuracy=None,  # To be updated later when we can validate
                confidence=None  # To be updated later when we can validate
            )
            session.add(new_prediction)
        
        # Commit changes
        session.commit()
        session.close()
        return True
    
    except Exception as e:
        print(f"Error saving prediction: {e}")
        session.rollback()
        session.close()
        return False


def get_recent_predictions(stock_symbol, limit=5):
    """
    Get recent predictions for a stock
    
    Args:
        stock_symbol (str): Stock symbol
        limit (int, optional): Maximum number of predictions to return
        
    Returns:
        list: List of PredictionHistory objects
    """
    try:
        session = get_db_session()
        
        # Get stock from database
        stock = session.query(Stock).filter(Stock.symbol == stock_symbol).first()
        
        if not stock:
            session.close()
            return []
        
        # Query recent predictions
        predictions = session.query(PredictionHistory).filter(
            PredictionHistory.stock_id == stock.id
        ).order_by(desc(PredictionHistory.prediction_date)).limit(limit).all()
        
        session.close()
        return predictions
    
    except Exception as e:
        print(f"Error getting recent predictions: {e}")
        session.close()
        return []


def create_default_watchlist(username="guest"):
    """
    Create a default watchlist for a user
    
    Args:
        username (str, optional): Username
        
    Returns:
        Watchlist: Watchlist object
    """
    try:
        session = get_db_session()
        
        # Create default user if not exists
        user = session.query(User).filter_by(username=username).first()
        if not user:
            from hashlib import sha256
            user = User(
                username=username,
                email=f"{username}@example.com",
                password_hash=sha256(username.encode()).hexdigest(),
                created_at=datetime.datetime.utcnow(),
                last_login=datetime.datetime.utcnow()
            )
            session.add(user)
            session.commit()
        
        # Check if default watchlist exists
        watchlist = session.query(Watchlist).filter_by(
            user_id=user.id, 
            is_default=True
        ).first()
        
        if not watchlist:
            # Create default watchlist
            watchlist = Watchlist(
                user_id=user.id,
                name="Default Watchlist",
                description="Default watchlist for tracking stocks",
                is_default=True,
                created_at=datetime.datetime.utcnow(),
                last_updated=datetime.datetime.utcnow()
            )
            session.add(watchlist)
            
            # Add some popular stocks to the watchlist
            popular_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
            
            for symbol in popular_symbols:
                stock = get_or_create_stock(symbol, f"{symbol} Inc.")
                
                # Add to watchlist
                watchlist_item = WatchlistItem(
                    watchlist_id=watchlist.id,
                    stock_id=stock.id,
                    added_at=datetime.datetime.utcnow()
                )
                session.add(watchlist_item)
            
            session.commit()
        
        session.close()
        return watchlist
    
    except Exception as e:
        print(f"Error creating default watchlist: {e}")
        session.rollback()
        session.close()
        return None