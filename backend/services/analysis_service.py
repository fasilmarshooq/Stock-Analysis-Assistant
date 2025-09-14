import asyncio
import uuid
import logging
from typing import List, Dict, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from models import (
    PortfolioItem, 
    StockRecommendation, 
    RecommendationType, 
    AnalysisStatus,
    AnalysisResponse
)
from database import Portfolio, StockData, StockAnalysis, AnalysisSession
from services.portfolio_service import PortfolioService
from services.screener_service import ScreenerService
from services.news_service import NewsService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self):
        self.portfolio_service = PortfolioService()
        self.screener_service = ScreenerService()
        self.news_service = NewsService()
    
    async def start_analysis(self, db: Session, force_refresh: bool = False) -> str:
        """
        Start a new analysis session
        Returns session_id for tracking progress
        """
        session_id = str(uuid.uuid4())
        logger.info(f"Starting new analysis session: {session_id}, force_refresh: {force_refresh}")
        
        # Create new analysis session
        analysis_session = AnalysisSession(
            session_id=session_id,
            status=AnalysisStatus.PENDING.value
        )
        db.add(analysis_session)
        db.commit()
        logger.info(f"Created analysis session in database: {session_id}")
        
        # Start analysis in background
        asyncio.create_task(self._run_analysis(session_id, db, force_refresh))
        logger.info(f"Started background analysis task for session: {session_id}")
        
        return session_id
    
    async def _run_analysis(self, session_id: str, db: Session, force_refresh: bool):
        """
        Run the complete analysis workflow following the master prompt
        """
        try:
            logger.info(f"Starting analysis workflow for session: {session_id}")
            
            # Update status: Fetching portfolio
            self._update_session_status(db, session_id, AnalysisStatus.FETCHING_PORTFOLIO)
            logger.info(f"Updated status to FETCHING_PORTFOLIO for session: {session_id}")
            
            # STEP 1: FETCH PORTFOLIO DATA
            logger.info("Fetching portfolio data from Google Sheets...")
            portfolio_items = await self.portfolio_service.fetch_portfolio_data()
            logger.info(f"Fetched {len(portfolio_items)} portfolio items: {[item.ticker for item in portfolio_items]}")
            
            # Save portfolio to database
            logger.info("Saving portfolio data to database...")
            for item in portfolio_items:
                logger.info(f"Processing portfolio item: {item.ticker} - {item.stock_name}")
                existing = db.query(Portfolio).filter(Portfolio.ticker == item.ticker).first()
                if existing:
                    existing.stock_name = item.stock_name
                    existing.budget = item.budget
                    existing.current_invested = item.current_invested
                    existing.available = item.available
                    existing.total_quantity = item.total_quantity
                    existing.updated_at = datetime.utcnow()
                    logger.info(f"Updated existing portfolio record for {item.ticker}")
                else:
                    portfolio_record = Portfolio(**item.dict())
                    db.add(portfolio_record)
                    logger.info(f"Added new portfolio record for {item.ticker}")
            
            db.commit()
            logger.info("Portfolio data saved to database successfully")
            
            # Update status: Fetching screener data
            self._update_session_status(db, session_id, AnalysisStatus.FETCHING_SCREENER)
            logger.info(f"Updated status to FETCHING_SCREENER for session: {session_id}")
            
            # STEP 2: ANALYZE FUNDAMENTALS
            logger.info("Starting fundamental analysis for each stock...")
            stock_data_results = []
            for i, item in enumerate(portfolio_items):
                logger.info(f"Fetching stock data for {item.ticker} ({i+1}/{len(portfolio_items)})")
                stock_data = await self.screener_service.fetch_stock_data(item.ticker)
                stock_data['ticker'] = item.ticker
                logger.info(f"Stock data for {item.ticker}: {stock_data}")
                stock_data_results.append(stock_data)
                
                # Save to database
                logger.info(f"Saving stock data to database for {item.ticker}")
                existing_data = db.query(StockData).filter(StockData.ticker == item.ticker).first()
                if existing_data:
                    for key, value in stock_data.items():
                        if key != 'ticker':
                            setattr(existing_data, key, value)
                    existing_data.last_updated = datetime.utcnow()
                    logger.info(f"Updated existing stock data for {item.ticker}")
                else:
                    stock_record = StockData(
                        ticker=item.ticker,
                        current_price=stock_data.get('current_price'),
                        week_52_high=stock_data.get('week_52_high'),
                        week_52_low=stock_data.get('week_52_low'),
                        pe_ratio=stock_data.get('pe_ratio'),
                        pb_ratio=stock_data.get('pb_ratio'),
                        roce=stock_data.get('roce'),
                        roe=stock_data.get('roe'),
                        market_cap=stock_data.get('market_cap'),
                        percentage_below_52w_high=stock_data.get('percentage_below_52w_high')
                    )
                    db.add(stock_record)
                    logger.info(f"Added new stock data record for {item.ticker}")
                
                # Small delay to avoid overwhelming the server
                await asyncio.sleep(1)
            
            db.commit()
            logger.info("Stock data saved to database successfully")
            
            # Update status: Analyzing stocks
            self._update_session_status(db, session_id, AnalysisStatus.ANALYZING_STOCKS)
            logger.info(f"Updated status to ANALYZING_STOCKS for session: {session_id}")
            
            # STEP 3: RESEARCH MARKET SIGNALS & GENERATE RECOMMENDATIONS
            logger.info("Starting recommendation generation...")
            recommendations = []
            total_recommended_amount = 0.0
            
            for i, item in enumerate(portfolio_items):
                logger.info(f"Processing recommendations for {item.ticker} ({i+1}/{len(portfolio_items)})")
                stock_data = stock_data_results[i]
                
                # Get news signals
                logger.info(f"Fetching news for {item.stock_name}")
                news_summary = await self.news_service.get_stock_news(item.stock_name)
                logger.info(f"News summary for {item.stock_name}: {news_summary[:100]}...")
                
                # Apply investment decision matrix
                logger.info(f"Applying decision matrix for {item.ticker}")
                recommendation, amount, analysis_summary = self._apply_decision_matrix(
                    item, stock_data, news_summary
                )
                logger.info(f"Decision matrix result for {item.ticker}: {recommendation.value}, amount: {amount}")
                
                # Create recommendation object
                stock_recommendation = StockRecommendation(
                    ticker=item.ticker,
                    stock_name=item.stock_name,
                    recommendation=recommendation,
                    recommended_amount=None,  # Let investor decide
                    current_price=stock_data.get('current_price'),
                    week_52_high=stock_data.get('week_52_high'),
                    percentage_below_52w_high=stock_data.get('percentage_below_52w_high'),
                    pe_ratio=stock_data.get('pe_ratio'),
                    analysis_summary=analysis_summary,
                    news_summary=news_summary,
                    available_budget=item.available,
                    suggested_amount=amount  # System suggestion
                )
                
                recommendations.append(stock_recommendation)
                if amount:
                    total_recommended_amount += amount
                    logger.info(f"Added recommendation for {item.ticker}: {recommendation.value} - Suggested: ₹{amount}")
                else:
                    logger.info(f"No suggested amount for {item.ticker}: {recommendation.value}")
                
                # Save analysis to database
                analysis_record = StockAnalysis(
                    session_id=session_id,
                    ticker=item.ticker,
                    recommendation=recommendation.value,
                    recommended_amount=amount,
                    analysis_summary=analysis_summary,
                    news_summary=news_summary
                )
                db.add(analysis_record)
                logger.info(f"Saved analysis record for {item.ticker}")
            
            db.commit()
            logger.info(f"Analysis records saved to database. Total recommendations: {len(recommendations)}")
            
            # Generate top picks
            logger.info("Generating top picks summary...")
            top_picks = self._generate_top_picks(recommendations)
            logger.info(f"Top picks generated: {top_picks}")
            
            # Update session as completed
            logger.info(f"Updating session {session_id} as completed...")
            session = db.query(AnalysisSession).filter(AnalysisSession.session_id == session_id).first()
            if session:
                session.status = AnalysisStatus.COMPLETED.value
                session.total_recommendations = total_recommended_amount
                session.top_picks = top_picks
                session.completed_at = datetime.utcnow()
                db.commit()
                logger.info(f"Session {session_id} marked as completed with {len(recommendations)} recommendations, total suggested amount: ₹{total_recommended_amount}")
            else:
                logger.error(f"Session {session_id} not found when trying to mark as completed")
            
        except Exception as e:
            logger.error(f"Analysis failed for session {session_id}: {e}", exc_info=True)
            self._update_session_status(db, session_id, AnalysisStatus.FAILED)
    
    def _apply_decision_matrix(self, portfolio_item: PortfolioItem, stock_data: Dict, news_summary: str) -> Tuple[RecommendationType, float, str]:
        """
        Apply the investment decision matrix from the master prompt
        """
        current_price = stock_data.get('current_price')
        pe_ratio = stock_data.get('pe_ratio')
        roce = stock_data.get('roce')
        roe = stock_data.get('roe')
        pct_below_52w = stock_data.get('percentage_below_52w_high', 0)
        
        logger.info(f"Decision matrix inputs for {portfolio_item.ticker}:")
        logger.info(f"  Current price: {current_price}")
        logger.info(f"  PE ratio: {pe_ratio}")
        logger.info(f"  ROCE: {roce}")
        logger.info(f"  ROE: {roe}")
        logger.info(f"  % below 52W high: {pct_below_52w}")
        
        # Available budget for this stock
        available_budget = portfolio_item.available
        logger.info(f"  Available budget: {available_budget}")
        
        # Analyze news sentiment (simplified)
        news_positive = self._analyze_news_sentiment(news_summary)
        logger.info(f"  News sentiment positive: {news_positive}")
        
        # Check if we have current price
        if not current_price:
            analysis = "No current price data available"
            logger.info(f"Decision: HOLD for {portfolio_item.ticker} - no price data")
            return RecommendationType.HOLD, 0.0, analysis
        
        # Validate that we have essential financial data
        if not pe_ratio or not roce or not roe:
            analysis = f"Insufficient financial data available (PE: {pe_ratio}, ROCE: {roce}, ROE: {roe}). Current price: ₹{current_price:.2f}"
            logger.warning(f"Decision: HOLD for {portfolio_item.ticker} - insufficient financial data")
            return RecommendationType.HOLD, 0.0, analysis
        
        # No available budget
        if available_budget <= 0:
            analysis = f"No available budget for investment. Current price: ₹{current_price:.2f}"
            logger.info(f"Decision: HOLD for {portfolio_item.ticker} - no budget")
            return RecommendationType.HOLD, 0.0, analysis
        
        # Calculate investment amount based on budget
        base_amount = min(available_budget, min(3000, max(1000, available_budget * 0.6)))
        
        # STRONG BUY: Excellent fundamentals + positive news + value opportunity (Value Investing Priority)
        if pe_ratio and pe_ratio < 30 and roce and roce > 20 and roe and roe > 20:
            if news_positive:
                amount = base_amount
                analysis = f"Excellent fundamentals (PE: {pe_ratio:.1f}, ROCE: {roce:.1f}%, ROE: {roe:.1f}%) with positive news. Current price: ₹{current_price:.2f}"
                logger.info(f"Decision: STRONG_BUY for {portfolio_item.ticker}, amount: {amount}")
                return RecommendationType.STRONG_BUY, amount, analysis
            elif pct_below_52w is not None and pct_below_52w > 10:  # Value opportunity
                amount = base_amount
                analysis = f"Excellent fundamentals (PE: {pe_ratio:.1f}, ROCE: {roce:.1f}%, ROE: {roe:.1f}%) with value opportunity ({pct_below_52w:.1f}% below 52W high). Current price: ₹{current_price:.2f}"
                logger.info(f"Decision: STRONG_BUY for {portfolio_item.ticker}, amount: {amount}")
                return RecommendationType.STRONG_BUY, amount, analysis
            else:
                amount = min(base_amount, base_amount * 0.8)
                analysis = f"Excellent fundamentals (PE: {pe_ratio:.1f}, ROCE: {roce:.1f}%, ROE: {roe:.1f}%). Current price: ₹{current_price:.2f}"
                logger.info(f"Decision: STRONG_BUY for {portfolio_item.ticker}, amount: {amount}")
                return RecommendationType.STRONG_BUY, amount, analysis
        
        # STRONG BUY: Strong fundamentals + positive news + value opportunity
        elif pe_ratio and pe_ratio < 25 and roce and roce > 12 and roe and roe > 10:
            if news_positive and pct_below_52w is not None and pct_below_52w > 10:
                amount = base_amount
                analysis = f"Strong fundamentals (PE: {pe_ratio:.1f}, ROCE: {roce:.1f}%, ROE: {roe:.1f}%) with positive news and value opportunity ({pct_below_52w:.1f}% below 52W high). Current price: ₹{current_price:.2f}"
                logger.info(f"Decision: STRONG_BUY for {portfolio_item.ticker}, amount: {amount}")
                return RecommendationType.STRONG_BUY, amount, analysis
            elif news_positive:
                amount = min(base_amount, base_amount * 0.8)
                analysis = f"Strong fundamentals (PE: {pe_ratio:.1f}, ROCE: {roce:.1f}%, ROE: {roe:.1f}%) with positive news. Current price: ₹{current_price:.2f}"
                logger.info(f"Decision: GOOD_BUY for {portfolio_item.ticker}, amount: {amount}")
                return RecommendationType.GOOD_BUY, amount, analysis
            else:
                amount = min(base_amount, base_amount * 0.8)
                analysis = f"Strong fundamentals (PE: {pe_ratio:.1f}, ROCE: {roce:.1f}%, ROE: {roe:.1f}%). Current price: ₹{current_price:.2f}"
                logger.info(f"Decision: GOOD_BUY for {portfolio_item.ticker}, amount: {amount}")
                return RecommendationType.GOOD_BUY, amount, analysis
        
        # GOOD BUY: Momentum signal (near 52W high) with good fundamentals
        elif pct_below_52w is not None and pct_below_52w < 3:  # Less than 3% below 52W high
            if pe_ratio and pe_ratio < 25 and roce and roce > 12 and roe and roe > 10:
                amount = base_amount
                analysis = f"Near 52W high ({pct_below_52w:.1f}% below) with strong fundamentals. Current price: ₹{current_price:.2f}"
                logger.info(f"Decision: GOOD_BUY for {portfolio_item.ticker}, amount: {amount}")
                return RecommendationType.GOOD_BUY, amount, analysis
            elif news_positive:
                amount = min(base_amount, base_amount * 0.8)
                analysis = f"Near 52W high ({pct_below_52w:.1f}% below) with positive news. Current price: ₹{current_price:.2f}"
                logger.info(f"Decision: GOOD_BUY for {portfolio_item.ticker}, amount: {amount}")
                return RecommendationType.GOOD_BUY, amount, analysis
            else:
                amount = min(base_amount, base_amount * 0.6)
                analysis = f"Near 52W high ({pct_below_52w:.1f}% below) - momentum signal. Current price: ₹{current_price:.2f}"
                logger.info(f"Decision: CONSIDER for {portfolio_item.ticker}, amount: {amount}")
                return RecommendationType.CONSIDER, amount, analysis
        
        # GOOD BUY: Value opportunity with moderate fundamentals
        elif pct_below_52w is not None and pct_below_52w > 10 and pe_ratio and pe_ratio < 30 and roce and roce > 15 and roe and roe > 15:
            if news_positive:
                amount = min(base_amount, base_amount * 0.8)
                analysis = f"Value opportunity - {pct_below_52w:.1f}% below 52W high with strong fundamentals (PE: {pe_ratio:.1f}, ROCE: {roce:.1f}%, ROE: {roe:.1f}%) and positive news. Current price: ₹{current_price:.2f}"
                logger.info(f"Decision: GOOD_BUY for {portfolio_item.ticker}, amount: {amount}")
                return RecommendationType.GOOD_BUY, amount, analysis
            else:
                amount = min(base_amount, base_amount * 0.6)
                analysis = f"Value opportunity - {pct_below_52w:.1f}% below 52W high with strong fundamentals (PE: {pe_ratio:.1f}, ROCE: {roce:.1f}%, ROE: {roe:.1f}%). Current price: ₹{current_price:.2f}"
                logger.info(f"Decision: CONSIDER for {portfolio_item.ticker}, amount: {amount}")
                return RecommendationType.CONSIDER, amount, analysis
        
        # CONSIDER: Moderate fundamentals or positive news
        elif (pe_ratio and pe_ratio < 30) or (roce and roce > 8) or (roe and roe > 8) or news_positive:
            amount = min(base_amount, base_amount * 0.6)
            if news_positive:
                analysis = f"Positive news signals with moderate fundamentals. Current price: ₹{current_price:.2f}"
            else:
                pe_str = f"{pe_ratio:.1f}" if pe_ratio else "N/A"
                roce_str = f"{roce:.1f}%" if roce else "N/A"
                analysis = f"Moderate fundamentals (PE: {pe_str}, ROCE: {roce_str}). Current price: ₹{current_price:.2f}"
            logger.info(f"Decision: CONSIDER for {portfolio_item.ticker}, amount: {amount}")
            return RecommendationType.CONSIDER, amount, analysis
        
        # HOLD: Poor fundamentals or overvalued
        elif pe_ratio and pe_ratio > 30:
            analysis = f"Overvalued (PE: {pe_ratio:.1f}). Current price: ₹{current_price:.2f}"
            logger.info(f"Decision: HOLD for {portfolio_item.ticker} - overvalued")
            return RecommendationType.HOLD, 0.0, analysis
        elif roce and roce < 8 and roe and roe < 8:
            analysis = f"Poor fundamentals (ROCE: {roce:.1f}%, ROE: {roe:.1f}%). Current price: ₹{current_price:.2f}"
            logger.info(f"Decision: HOLD for {portfolio_item.ticker} - poor fundamentals")
            return RecommendationType.HOLD, 0.0, analysis
        else:
            # Default case - no clear signals
            analysis = f"No clear investment signals. Current price: ₹{current_price:.2f}"
            logger.info(f"Decision: HOLD for {portfolio_item.ticker} - no clear signals")
            return RecommendationType.HOLD, 0.0, analysis
    
    def _analyze_news_sentiment(self, news_summary: str) -> bool:
        """
        Simple news sentiment analysis
        """
        if not news_summary:
            return False
        
        positive_keywords = ['growth', 'profit', 'expansion', 'strong', 'beat', 'outperform', 'positive', 'good', 'excellent']
        negative_keywords = ['loss', 'decline', 'fall', 'weak', 'poor', 'miss', 'negative', 'bad', 'concern']
        
        news_lower = news_summary.lower()
        positive_count = sum(1 for keyword in positive_keywords if keyword in news_lower)
        negative_count = sum(1 for keyword in negative_keywords if keyword in news_lower)
        
        return positive_count > negative_count
    
    def _generate_top_picks(self, recommendations: List[StockRecommendation]) -> str:
        """
        Generate top picks summary
        """
        strong_buys = [r for r in recommendations if r.recommendation == RecommendationType.STRONG_BUY]
        good_buys = [r for r in recommendations if r.recommendation == RecommendationType.GOOD_BUY]
        
        if strong_buys:
            top_picks = [f"{r.stock_name} (₹{r.suggested_amount:.0f})" for r in strong_buys[:3] if r.suggested_amount]
            return f"Focus on {', '.join(top_picks)} due to strong fundamentals and positive signals"
        elif good_buys:
            top_picks = [f"{r.stock_name} (₹{r.suggested_amount:.0f})" for r in good_buys[:3] if r.suggested_amount]
            return f"Consider {', '.join(top_picks)} for good value opportunities"
        else:
            return "Market conditions suggest waiting for better entry points"
    
    def _update_session_status(self, db: Session, session_id: str, status: AnalysisStatus):
        """Update analysis session status"""
        session = db.query(AnalysisSession).filter(AnalysisSession.session_id == session_id).first()
        if session:
            session.status = status.value
            db.commit()
    
    def get_analysis_status(self, db: Session, session_id: str) -> AnalysisResponse:
        """
        Get current analysis status and results
        """
        session = db.query(AnalysisSession).filter(AnalysisSession.session_id == session_id).first()
        if not session:
            raise ValueError("Session not found")
        
        recommendations = []
        if session.status == AnalysisStatus.COMPLETED.value:
            # Get recommendations for this specific session
            analysis_records = db.query(StockAnalysis).filter(StockAnalysis.session_id == session_id).all()
            for record in analysis_records:
                # Get portfolio item for stock name
                portfolio_item = db.query(Portfolio).filter(Portfolio.ticker == record.ticker).first()
                stock_data = db.query(StockData).filter(StockData.ticker == record.ticker).first()
                
                if portfolio_item:
                    recommendation = StockRecommendation(
                        ticker=str(record.ticker),
                        stock_name=str(portfolio_item.stock_name),
                        recommendation=RecommendationType(record.recommendation),
                        recommended_amount=None,  # Let investor decide
                        current_price=float(stock_data.current_price) if stock_data and stock_data.current_price else None,
                        week_52_high=float(stock_data.week_52_high) if stock_data and stock_data.week_52_high else None,
                        percentage_below_52w_high=float(stock_data.percentage_below_52w_high) if stock_data and stock_data.percentage_below_52w_high else None,
                        pe_ratio=float(stock_data.pe_ratio) if stock_data and stock_data.pe_ratio else None,
                        analysis_summary=str(record.analysis_summary),
                        news_summary=str(record.news_summary) if record.news_summary else None,
                        available_budget=float(portfolio_item.available),
                        suggested_amount=float(record.recommended_amount) if record.recommended_amount else None  # System suggestion
                    )
                    recommendations.append(recommendation)
        
        return AnalysisResponse(
            session_id=str(session.session_id),
            status=AnalysisStatus(session.status),
            recommendations=recommendations,
            total_recommendations=float(session.total_recommendations) if session.total_recommendations else None,
            top_picks=str(session.top_picks) if session.top_picks else None,
            created_at=session.created_at,
            completed_at=session.completed_at
        ) 