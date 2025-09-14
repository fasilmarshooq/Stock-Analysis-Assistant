from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


class RecommendationType(str, Enum):
    STRONG_BUY = "STRONG_BUY"
    GOOD_BUY = "GOOD_BUY"
    CONSIDER = "CONSIDER"
    HOLD = "HOLD"
    AVOID = "AVOID"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    FETCHING_PORTFOLIO = "fetching_portfolio"
    FETCHING_SCREENER = "fetching_screener"
    ANALYZING_STOCKS = "analyzing_stocks"
    COMPLETED = "completed"
    FAILED = "failed"


class PortfolioItem(BaseModel):
    ticker: str
    stock_name: str
    budget: float
    current_invested: float = 0.0
    available: float
    total_quantity: int = 0

    class Config:
        from_attributes = True


class StockDataResponse(BaseModel):
    ticker: str
    current_price: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    roce: Optional[float] = None
    roe: Optional[float] = None
    percentage_below_52w_high: Optional[float] = None
    last_updated: datetime

    class Config:
        from_attributes = True


class StockRecommendation(BaseModel):
    ticker: str
    stock_name: str
    recommendation: RecommendationType
    recommended_amount: Optional[float] = None
    current_price: Optional[float] = None
    week_52_high: Optional[float] = None
    percentage_below_52w_high: Optional[float] = None
    pe_ratio: Optional[float] = None
    analysis_summary: str
    news_summary: Optional[str] = None
    available_budget: Optional[float] = None
    suggested_amount: Optional[float] = None  # System suggested amount

    class Config:
        from_attributes = True


class AnalysisResponse(BaseModel):
    session_id: str
    status: AnalysisStatus
    recommendations: List[StockRecommendation] = []
    total_recommendations: Optional[float] = None
    top_picks: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnalysisRequest(BaseModel):
    force_refresh: bool = False


class StatusUpdate(BaseModel):
    session_id: str
    status: AnalysisStatus
    message: str
    progress: int  # 0-100 