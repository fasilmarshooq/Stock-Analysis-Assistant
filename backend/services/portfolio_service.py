import requests
import pandas as pd
import io
import logging
import os
from typing import List
from models import PortfolioItem
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class PortfolioService:
    def __init__(self):
        self.google_sheets_url = os.getenv(
            "GOOGLE_SHEETS_URL", 
            "https://docs.google.com/spreadsheets/d/1k4kckhpXfG6tFHySzGMWNQNLkt_WNlh6Cm6wHxHpJQ0/gviz/tq?tqx=out:csv&sheet=stocks"
        )
    
    async def fetch_portfolio_data(self) -> List[PortfolioItem]:
        """
        Fetch portfolio data from Google Sheets CSV
        Returns list of PortfolioItem objects
        """
        try:
            logger.info(f"Fetching portfolio data from Google Sheets: {self.google_sheets_url}")
            
            # Fetch CSV data from Google Sheets
            response = requests.get(self.google_sheets_url)
            response.raise_for_status()
            logger.info(f"Successfully fetched data from Google Sheets. Response status: {response.status_code}")
            
            # Parse CSV data
            csv_data = io.StringIO(response.text)
            df = pd.read_csv(csv_data)
            logger.info(f"Parsed CSV data. Shape: {df.shape}, Columns: {list(df.columns)}")
            
            # Clean column names (remove extra spaces, standardize)
            df.columns = df.columns.str.strip()
            logger.info(f"Cleaned column names: {list(df.columns)}")
            
            # Map expected columns
            portfolio_items = []
            logger.info("Processing portfolio rows...")
            
            for idx, row in df.iterrows():
                try:
                    logger.info(f"Processing row {idx}: {dict(row)}")
                    
                    # Handle different possible column names
                    ticker = str(row.get('Ticker name', row.get('Ticker', row.get('ticker', '')))).strip()
                    stock_name = str(row.get('Stock Name', row.get('stock_name', row.get('Stock', '')))).strip()
                    budget = float(row.get('Budget', row.get('budget', 0)))
                    current_invested = float(row.get('Current Invested', row.get('current_invested', 0)))
                    available = float(row.get('Available', row.get('available', budget - current_invested)))
                    total_quantity = int(row.get('Total Quantity', row.get('total_quantity', 0)))
                    
                    logger.info(f"Extracted data - Ticker: {ticker}, Stock: {stock_name}, Budget: {budget}, Available: {available}")
                    
                    if ticker and stock_name:  # Only add if we have essential data
                        portfolio_item = PortfolioItem(
                            ticker=ticker,
                            stock_name=stock_name,
                            budget=budget,
                            current_invested=current_invested,
                            available=available,
                            total_quantity=total_quantity
                        )
                        portfolio_items.append(portfolio_item)
                        logger.info(f"Added portfolio item: {ticker} - {stock_name}")
                    else:
                        logger.warning(f"Skipping row {idx} - missing ticker or stock name")
                        
                except (ValueError, KeyError) as e:
                    logger.error(f"Error processing row {idx}: {e}, row data: {dict(row)}")
                    continue
            
            logger.info(f"Successfully processed {len(portfolio_items)} portfolio items")
            return portfolio_items
            
        except Exception as e:
            logger.error(f"Error fetching portfolio data: {e}", exc_info=True)
            raise Exception(f"Failed to fetch portfolio data: {str(e)}")
    
    def get_ticker_list(self, portfolio_items: List[PortfolioItem]) -> List[str]:
        """Extract ticker symbols from portfolio items"""
        return [item.ticker for item in portfolio_items if item.ticker] 