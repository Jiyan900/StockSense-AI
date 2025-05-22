import os
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Get the database URL from environment variables
DATABASE_URL = os.environ.get('DATABASE_URL', '')

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a base class for our models
Base = declarative_base()

# Create session factory
Session = sessionmaker(bind=engine)


class Stock(Base):
    """Model for storing basic stock information"""
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    sector = Column(String(100))
    industry = Column(String(100))
    description = Column(Text)
    market_cap = Column(Float)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    price_data = relationship("StockPrice", back_populates="stock", cascade="all, delete-orphan")
    watchlist_items = relationship("WatchlistItem", back_populates="stock", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Stock(symbol='{self.symbol}', name='{self.name}')>"


class StockPrice(Base):
    """Model for storing historical stock price data"""
    __tablename__ = 'stock_prices'
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    date = Column(DateTime, nullable=False)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float)
    
    # Relationship
    stock = relationship("Stock", back_populates="price_data")
    
    __table_args__ = (
        # Composite index for faster querying by stock and date
        {'sqlite_autoincrement': True},
    )
    
    def __repr__(self):
        return f"<StockPrice(symbol='{self.stock.symbol}', date='{self.date}', close='{self.close_price}')>"


class User(Base):
    """Model for storing user information"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(128))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    watchlists = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"


class Watchlist(Base):
    """Model for storing user watchlists"""
    __tablename__ = 'watchlists'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(50), nullable=False)
    description = Column(Text)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="watchlists")
    items = relationship("WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Watchlist(name='{self.name}', user='{self.user.username}')>"


class WatchlistItem(Base):
    """Model for storing stocks in a watchlist"""
    __tablename__ = 'watchlist_items'
    
    id = Column(Integer, primary_key=True)
    watchlist_id = Column(Integer, ForeignKey('watchlists.id'), nullable=False)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    added_at = Column(DateTime, default=datetime.datetime.utcnow)
    notes = Column(Text)
    
    # Relationships
    watchlist = relationship("Watchlist", back_populates="items")
    stock = relationship("Stock", back_populates="watchlist_items")
    
    def __repr__(self):
        return f"<WatchlistItem(watchlist='{self.watchlist.name}', stock='{self.stock.symbol}')>"


class PredictionHistory(Base):
    """Model for storing prediction history"""
    __tablename__ = 'prediction_history'
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    prediction_date = Column(DateTime, default=datetime.datetime.utcnow)
    target_date = Column(DateTime, nullable=False)
    predicted_price = Column(Float, nullable=False)
    lower_bound = Column(Float)
    upper_bound = Column(Float)
    accuracy = Column(Float)
    confidence = Column(Float)
    
    # Relationship
    stock = relationship("Stock")
    
    def __repr__(self):
        return f"<PredictionHistory(stock='{self.stock.symbol}', target_date='{self.target_date}')>"


# Function to initialize the database
def init_db():
    Base.metadata.create_all(engine)


# Function to get a database session
def get_db_session():
    return Session()