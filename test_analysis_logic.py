#!/usr/bin/env python3
"""
Test script to demonstrate the fixed analysis logic
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from models import PortfolioItem, RecommendationType
from services.analysis_service import AnalysisService

def test_itc_analysis():
    """Test ITC analysis with different scenarios"""
    
    # Create analysis service
    analysis_service = AnalysisService()
    
    # Test ITC with different scenarios
    test_cases = [
        {
            "name": "ITC Near 52W High (0% below) - Should be STRONG_BUY",
            "portfolio_item": PortfolioItem(
                ticker="ITC",
                stock_name="ITC Limited",
                budget=100000.0,
                current_invested=19796.36,
                available=80203.64,
                total_quantity=723
            ),
            "stock_data": {
                'current_price': 414.0,
                'week_52_high': 414.0,  # Same as current price = 0% below
                'week_52_low': 350.0,
                'pe_ratio': 22.5,
                'pb_ratio': 4.2,
                'roce': 15.8,
                'roe': 18.2,
                'market_cap': 500000.0,
                'percentage_below_52w_high': 0.0  # 0% below 52W high
            },
            "news_summary": "ITC reports strong Q3 earnings growth with revenue up 12% and improved margins across all business segments."
        },
        {
            "name": "ITC 5% below 52W High - Should be GOOD_BUY",
            "portfolio_item": PortfolioItem(
                ticker="ITC",
                stock_name="ITC Limited",
                budget=100000.0,
                current_invested=19796.36,
                available=80203.64,
                total_quantity=723
            ),
            "stock_data": {
                'current_price': 393.3,
                'week_52_high': 414.0,
                'week_52_low': 350.0,
                'pe_ratio': 22.5,
                'pb_ratio': 4.2,
                'roce': 15.8,
                'roe': 18.2,
                'market_cap': 500000.0,
                'percentage_below_52w_high': 5.0  # 5% below 52W high
            },
            "news_summary": "ITC announces expansion plans in FMCG segment with significant investments planned."
        },
        {
            "name": "ITC 10% below 52W High - Should be CONSIDER",
            "portfolio_item": PortfolioItem(
                ticker="ITC",
                stock_name="ITC Limited",
                budget=100000.0,
                current_invested=19796.36,
                available=80203.64,
                total_quantity=723
            ),
            "stock_data": {
                'current_price': 372.6,
                'week_52_high': 414.0,
                'week_52_low': 350.0,
                'pe_ratio': 22.5,
                'pb_ratio': 4.2,
                'roce': 15.8,
                'roe': 18.2,
                'market_cap': 500000.0,
                'percentage_below_52w_high': 10.0  # 10% below 52W high
            },
            "news_summary": "Limited recent news available for ITC. Market conditions appear stable."
        }
    ]
    
    print("Testing ITC Analysis Logic")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['name']}")
        print("-" * 40)
        
        # Apply decision matrix
        recommendation, amount, analysis = analysis_service._apply_decision_matrix(
            test_case['portfolio_item'],
            test_case['stock_data'],
            test_case['news_summary']
        )
        
        print(f"Recommendation: {recommendation.value}")
        print(f"Amount: ₹{amount:,.0f}")
        print(f"Analysis: {analysis}")
        print(f"News: {test_case['news_summary'][:100]}...")
        
        # Expected results
        if i == 1:
            expected = "STRONG_BUY"
            print(f"✅ Expected: {expected} - {'PASS' if recommendation.value == expected else 'FAIL'}")
        elif i == 2:
            expected = "GOOD_BUY"
            print(f"✅ Expected: {expected} - {'PASS' if recommendation.value == expected else 'FAIL'}")
        elif i == 3:
            expected = "CONSIDER"
            print(f"✅ Expected: {expected} - {'PASS' if recommendation.value == expected else 'FAIL'}")

if __name__ == "__main__":
    test_itc_analysis()
