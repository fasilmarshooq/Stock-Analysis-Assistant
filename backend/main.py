
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn
import logging

from database import get_db, ensure_database_exists
from models import AnalysisRequest, AnalysisResponse, StatusUpdate, AnalysisStatus
from services.analysis_service import AnalysisService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure database exists and create tables on startup
logger.info("🔍 Checking database initialization...")
ensure_database_exists()
logger.info("✅ Database initialization completed")

# Initialize FastAPI app
app = FastAPI(
    title="Stock Analysis Assistant",
    description="AI-powered stock analysis and recommendation system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
analysis_service = AnalysisService()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Stock Analysis Assistant API is running"}


@app.post("/api/analyze", response_model=dict)
async def start_analysis(
    request: AnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Start a new stock analysis session
    Returns session_id for tracking progress
    """
    try:
        logger.info(f"Received analysis request: force_refresh={request.force_refresh}")
        session_id = await analysis_service.start_analysis(db, request.force_refresh)
        logger.info(f"Started analysis session: {session_id}")
        return {
            "session_id": session_id,
            "status": "started",
            "message": "Analysis started successfully"
        }
    except Exception as e:
        logger.error(f"Failed to start analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")


@app.get("/api/analysis/{session_id}", response_model=AnalysisResponse)
async def get_analysis_status(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get current analysis status and results
    """
    try:
        logger.info(f"Getting analysis status for session: {session_id}")
        analysis_response = analysis_service.get_analysis_status(db, session_id)
        logger.info(f"Analysis status for {session_id}: {analysis_response.status}, recommendations: {len(analysis_response.recommendations)}")
        return analysis_response
    except ValueError as e:
        logger.error(f"Session not found: {session_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get analysis for {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get analysis: {str(e)}")


@app.get("/api/analysis/{session_id}/status")
async def get_analysis_status_simple(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get simplified status for real-time updates
    """
    try:
        analysis_response = analysis_service.get_analysis_status(db, session_id)
        
        # Map status to user-friendly messages
        status_messages = {
            AnalysisStatus.PENDING: "Initializing analysis...",
            AnalysisStatus.FETCHING_PORTFOLIO: "Fetching your portfolio info...",
            AnalysisStatus.FETCHING_SCREENER: "Fetching info from screener...",
            AnalysisStatus.ANALYZING_STOCKS: "Analyzing the stocks...",
            AnalysisStatus.COMPLETED: "Analysis completed!",
            AnalysisStatus.FAILED: "Analysis failed. Please try again."
        }
        
        # Calculate progress percentage
        progress_map = {
            AnalysisStatus.PENDING: 5,
            AnalysisStatus.FETCHING_PORTFOLIO: 25,
            AnalysisStatus.FETCHING_SCREENER: 50,
            AnalysisStatus.ANALYZING_STOCKS: 75,
            AnalysisStatus.COMPLETED: 100,
            AnalysisStatus.FAILED: 0
        }
        
        return StatusUpdate(
            session_id=session_id,
            status=analysis_response.status,
            message=status_messages.get(analysis_response.status, "Processing..."),
            progress=progress_map.get(analysis_response.status, 0)
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@app.get("/api/portfolio")
async def get_portfolio(db: Session = Depends(get_db)):
    """
    Get current portfolio data
    """
    try:
        from database import Portfolio
        portfolio_items = db.query(Portfolio).all()
        return {"portfolio": portfolio_items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get portfolio: {str(e)}")


@app.get("/api/recommendations/latest")
async def get_latest_recommendations(db: Session = Depends(get_db)):
    """
    Get the latest analysis recommendations
    """
    try:
        from database import AnalysisSession
        latest_session = db.query(AnalysisSession).filter(
            AnalysisSession.status == AnalysisStatus.COMPLETED.value
        ).order_by(AnalysisSession.completed_at.desc()).first()
        
        if not latest_session:
            return {"message": "No completed analysis found"}
        
        analysis_response = analysis_service.get_analysis_status(db, latest_session.session_id)
        return analysis_response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 