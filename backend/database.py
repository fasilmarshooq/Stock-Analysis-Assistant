from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL - create in current directory (backend)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///stock_analysis.db")

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


class Portfolio(Base):
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, unique=True, index=True, nullable=False)
    stock_name = Column(String, nullable=False)
    budget = Column(Float, nullable=False)
    current_invested = Column(Float, default=0.0)
    available = Column(Float, nullable=False)
    total_quantity = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StockData(Base):
    __tablename__ = "stock_data"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True, nullable=False)
    current_price = Column(Float)
    week_52_high = Column(Float)
    week_52_low = Column(Float)
    pe_ratio = Column(Float)
    pb_ratio = Column(Float)
    roce = Column(Float)
    roe = Column(Float)
    market_cap = Column(Float)
    percentage_below_52w_high = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)


class StockAnalysis(Base):
    __tablename__ = "stock_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    ticker = Column(String, index=True, nullable=False)
    recommendation = Column(String, nullable=False)  # STRONG_BUY, GOOD_BUY, CONSIDER, HOLD, AVOID
    recommended_amount = Column(Float)
    analysis_summary = Column(Text)
    news_summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, default="pending")  # pending, fetching_portfolio, analyzing_stocks, completed, failed
    total_recommendations = Column(Float)
    top_picks = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


# Check if database file exists and create if needed
def ensure_database_exists():
    """Check if database file exists and create it if needed."""
    # Extract the database file path from the URL
    db_path = Path("stock_analysis.db")
    
    if not db_path.exists():
        print(f"📁 Database file not found at {db_path.absolute()}")
        print("🆕 Creating new database file...")
        
        # Ensure the backend directory exists
        backend_dir = Path(".")
        backend_dir.mkdir(exist_ok=True)
        
        # Create the database file by creating tables
        create_tables()
        print(f"✅ Database file created successfully at {db_path.absolute()}")
    else:
        print(f"✅ Database file found at {db_path.absolute()}")


# Create all tables
def create_tables():
    Base.metadata.create_all(bind=engine)


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 