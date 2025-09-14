export interface PortfolioItem {
  ticker: string;
  stock_name: string;
  budget: number;
  current_invested: number;
  available: number;
  total_quantity: number;
}

export interface StockData {
  ticker: string;
  current_price?: number;
  week_52_high?: number;
  week_52_low?: number;
  pe_ratio?: number;
  pb_ratio?: number;
  roce?: number;
  roe?: number;
  percentage_below_52w_high?: number;
  last_updated: string;
}

export enum RecommendationType {
  STRONG_BUY = "STRONG_BUY",
  GOOD_BUY = "GOOD_BUY",
  CONSIDER = "CONSIDER",
  HOLD = "HOLD",
  AVOID = "AVOID"
}

export enum AnalysisStatus {
  PENDING = "pending",
  FETCHING_PORTFOLIO = "fetching_portfolio",
  FETCHING_SCREENER = "fetching_screener",
  ANALYZING_STOCKS = "analyzing_stocks",
  COMPLETED = "completed",
  FAILED = "failed"
}

export interface StockRecommendation {
  ticker: string;
  stock_name: string;
  recommendation: RecommendationType;
  recommended_amount?: number;
  current_price?: number;
  week_52_high?: number;
  percentage_below_52w_high?: number;
  pe_ratio?: number;
  analysis_summary: string;
  news_summary?: string;
  available_budget?: number;
  suggested_amount?: number;  // System suggested amount
}

export interface AnalysisResponse {
  session_id: string;
  status: AnalysisStatus;
  recommendations: StockRecommendation[];
  total_recommendations?: number;
  top_picks?: string;
  created_at: string;
  completed_at?: string;
}

export interface StatusUpdate {
  session_id: string;
  status: AnalysisStatus;
  message: string;
  progress: number;
}

export interface AnalysisRequest {
  force_refresh?: boolean;
} 