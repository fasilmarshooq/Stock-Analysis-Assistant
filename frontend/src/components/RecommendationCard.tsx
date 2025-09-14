import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, DollarSign, BarChart3, Wallet, Target } from 'lucide-react';
import { StockRecommendation } from '../types';

interface RecommendationCardProps {
  recommendation: StockRecommendation;
}

const RecommendationCard: React.FC<RecommendationCardProps> = ({ recommendation }) => {
  const [investmentAmount, setInvestmentAmount] = useState<number>(recommendation.suggested_amount || 0);
  const [isEditing, setIsEditing] = useState(false);


  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-4 hover:bg-white/10 transition-all duration-200"
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <h4 className="text-lg font-semibold text-white">{recommendation.stock_name}</h4>
          <p className="text-sm text-slate-400">{recommendation.ticker}</p>
        </div>
        
        {/* Investment Amount Input */}
        <div className="text-right">
          <div className="flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-green-400" />
            {isEditing ? (
              <input
                type="number"
                value={investmentAmount}
                onChange={(e) => setInvestmentAmount(Number(e.target.value))}
                onBlur={() => setIsEditing(false)}
                onKeyPress={(e) => e.key === 'Enter' && setIsEditing(false)}
                className="w-20 px-2 py-1 bg-white/10 border border-white/20 rounded text-white text-sm"
                min="0"
                max={recommendation.available_budget || 0}
              />
            ) : (
              <button
                onClick={() => setIsEditing(true)}
                className="text-green-400 font-semibold hover:text-green-300 transition-colors"
              >
                ₹{investmentAmount.toFixed(0)}
              </button>
            )}
          </div>
          {recommendation.suggested_amount && (
            <p className="text-xs text-slate-400 mt-1">
              Suggested: ₹{recommendation.suggested_amount.toFixed(0)}
            </p>
          )}
        </div>
      </div>

      {/* Stock Metrics */}
      <div className="grid grid-cols-2 gap-4 mb-3 text-sm">
        {recommendation.current_price !== null && recommendation.current_price !== undefined && (
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-blue-400" />
            <span className="text-slate-300">Price: ₹{recommendation.current_price.toFixed(2)}</span>
          </div>
        )}
        
        {recommendation.week_52_high !== null && recommendation.week_52_high !== undefined && (
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-orange-400" />
            <span className="text-slate-300">52W High: ₹{recommendation.week_52_high.toFixed(2)}</span>
          </div>
        )}
        
        {recommendation.percentage_below_52w_high !== null && recommendation.percentage_below_52w_high !== undefined && (
          <div className="flex items-center gap-2">
            {recommendation.percentage_below_52w_high > 0 ? (
              <TrendingDown className="w-4 h-4 text-red-400" />
            ) : (
              <TrendingUp className="w-4 h-4 text-green-400" />
            )}
            <span className="text-slate-300">
              {recommendation.percentage_below_52w_high.toFixed(1)}% below 52W high
            </span>
          </div>
        )}
        
        {recommendation.pe_ratio !== null && recommendation.pe_ratio !== undefined && (
          <div className="flex items-center gap-2">
            <span className="text-slate-400">P/E:</span>
            <span className="text-slate-300">{recommendation.pe_ratio.toFixed(1)}</span>
          </div>
        )}
      </div>

      {/* Available Budget */}
      {recommendation.available_budget !== null && recommendation.available_budget !== undefined && (
        <div className="mb-3 p-2 bg-white/5 rounded-lg">
          <div className="flex items-center gap-2 text-sm">
            <Wallet className="w-4 h-4 text-purple-400" />
            <span className="text-slate-300">Available Budget: ₹{recommendation.available_budget.toFixed(0)}</span>
          </div>
        </div>
      )}

      {/* Analysis Summary */}
      <div className="mb-3">
        <p className="text-slate-300 text-sm leading-relaxed">
          {recommendation.analysis_summary}
        </p>
      </div>

      {/* News Summary */}
      {recommendation.news_summary && (
        <div className="border-t border-white/10 pt-3">
          <p className="text-xs text-slate-400 leading-relaxed">
            <strong>Market Signal:</strong> {recommendation.news_summary.slice(0, 150)}
            {recommendation.news_summary.length > 150 ? '...' : ''}
          </p>
        </div>
      )}
    </motion.div>
  );
};

export default RecommendationCard; 