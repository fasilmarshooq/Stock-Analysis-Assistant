import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { TrendingUp, Brain, DollarSign, AlertCircle, Loader2 } from 'lucide-react';
import { analysisAPI } from './services/api';
import { AnalysisStatus, StockRecommendation, RecommendationType } from './types';
import RecommendationCard from './components/RecommendationCard';
import LoadingSteps from './components/LoadingSteps';

function App() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [currentStatus, setCurrentStatus] = useState<AnalysisStatus | null>(null);
  const [statusMessage, setStatusMessage] = useState('');
  const [progress, setProgress] = useState(0);
  const [, setSessionId] = useState<string | null>(null);
  const [recommendations, setRecommendations] = useState<StockRecommendation[]>([]);
  const [totalRecommendations, setTotalRecommendations] = useState<number>(0);
  const [topPicks, setTopPicks] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const startAnalysis = async () => {
    try {
      setError(null);
      setIsAnalyzing(true);
      setCurrentStatus(AnalysisStatus.PENDING);
      setStatusMessage('Initializing analysis...');
      setProgress(5);
      setRecommendations([]);
      
      const response = await analysisAPI.startAnalysis();
      setSessionId(response.session_id);
      
      // Start polling for status updates
      pollStatus(response.session_id);
    } catch (err) {
      setError('Failed to start analysis. Please try again.');
      setIsAnalyzing(false);
      console.error('Analysis start error:', err);
    }
  };

  const pollStatus = async (sessionId: string) => {
    try {
      const statusResponse = await analysisAPI.getAnalysisStatus(sessionId);
      setCurrentStatus(statusResponse.status);
      setStatusMessage(statusResponse.message);
      setProgress(statusResponse.progress);

      if (statusResponse.status === AnalysisStatus.COMPLETED) {
        // Get final results
        const analysisResponse = await analysisAPI.getAnalysis(sessionId);
        setRecommendations(analysisResponse.recommendations);
        setTotalRecommendations(analysisResponse.total_recommendations || 0);
        setTopPicks(analysisResponse.top_picks || '');
        setIsAnalyzing(false);
      } else if (statusResponse.status === AnalysisStatus.FAILED) {
        setError('Analysis failed. Please try again.');
        setIsAnalyzing(false);
      } else {
        // Continue polling
        setTimeout(() => pollStatus(sessionId), 2000);
      }
    } catch (err) {
      setError('Failed to get analysis status.');
      setIsAnalyzing(false);
      console.error('Status polling error:', err);
    }
  };

  const getRecommendationsByType = (type: RecommendationType) => {
    return recommendations.filter(rec => rec.recommendation === type);
  };

  const getRecommendationIcon = (type: RecommendationType) => {
    switch (type) {
      case RecommendationType.STRONG_BUY:
        return '🔥';
      case RecommendationType.GOOD_BUY:
        return '🟢';
      case RecommendationType.CONSIDER:
        return '🟡';
      case RecommendationType.HOLD:
        return '⚪';
      case RecommendationType.AVOID:
        return '🔴';
      default:
        return '📊';
    }
  };

  const getRecommendationTitle = (type: RecommendationType) => {
    switch (type) {
      case RecommendationType.STRONG_BUY:
        return 'STRONG BUY';
      case RecommendationType.GOOD_BUY:
        return 'GOOD BUY';
      case RecommendationType.CONSIDER:
        return 'CONSIDER';
      case RecommendationType.HOLD:
        return 'HOLD';
      case RecommendationType.AVOID:
        return 'AVOID';
      default:
        return 'UNKNOWN';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="p-3 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl">
              <Brain className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-4xl font-bold text-white">
              Stock Analysis Assistant
            </h1>
          </div>
          <p className="text-slate-300 text-lg">
            AI-powered portfolio analysis with real-time market insights
          </p>
        </motion.div>

        {/* Main Card */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="max-w-4xl mx-auto"
        >
          <div className="bg-white/10 backdrop-blur-lg rounded-3xl border border-white/20 shadow-2xl overflow-hidden">
            
            {/* Action Section */}
            <div className="p-8 text-center">
              <h2 className="text-2xl font-semibold text-white mb-4">
                What should I buy today?
              </h2>
              
              <motion.button
                onClick={startAnalysis}
                disabled={isAnalyzing}
                className={`
                  px-8 py-4 rounded-2xl font-semibold text-lg transition-all duration-200
                  ${isAnalyzing 
                    ? 'bg-gray-500 cursor-not-allowed' 
                    : 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 transform hover:scale-105'
                  }
                  text-white shadow-lg
                `}
                whileTap={{ scale: 0.95 }}
              >
                {isAnalyzing ? (
                  <div className="flex items-center gap-3">
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Analyzing...
                  </div>
                ) : (
                  <div className="flex items-center gap-3">
                    <TrendingUp className="w-5 h-5" />
                    Analyze My Portfolio
                  </div>
                )}
              </motion.button>
            </div>

            {/* Loading Section */}
            <AnimatePresence>
              {isAnalyzing && (
                <LoadingSteps 
                  currentStatus={currentStatus}
                  statusMessage={statusMessage}
                  progress={progress}
                />
              )}
            </AnimatePresence>

            {/* Error Section */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="border-t border-white/10"
                >
                  <div className="p-6 text-center">
                    <div className="flex items-center justify-center gap-3 text-red-400">
                      <AlertCircle className="w-6 h-6" />
                      <p>{error}</p>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Results Section */}
            <AnimatePresence>
              {recommendations.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="border-t border-white/10"
                >
                  <div className="p-6">
                    {/* Summary */}
                    <div className="mb-6 text-center">
                      <div className="flex items-center justify-center gap-4 mb-4">
                        <div className="flex items-center gap-2 text-green-400">
                          <DollarSign className="w-5 h-5" />
                          <span className="font-semibold">
                            Total Recommendations: ₹{totalRecommendations.toFixed(0)}
                          </span>
                        </div>
                      </div>
                      {topPicks && (
                        <p className="text-slate-300 text-sm bg-white/5 rounded-lg p-3">
                          🎯 <strong>Top Picks:</strong> {topPicks}
                        </p>
                      )}
                    </div>

                    {/* Recommendations by Category */}
                    <div className="space-y-6">
                      {[
                        RecommendationType.STRONG_BUY,
                        RecommendationType.GOOD_BUY,
                        RecommendationType.CONSIDER,
                        RecommendationType.HOLD,
                        RecommendationType.AVOID
                      ].map(type => {
                        const recs = getRecommendationsByType(type);
                        if (recs.length === 0) return null;

                        return (
                          <motion.div
                            key={type}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="space-y-3"
                          >
                            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                              <span className="text-2xl">{getRecommendationIcon(type)}</span>
                              {getRecommendationTitle(type)}
                            </h3>
                            <div className="grid gap-3">
                              {recs.map((rec) => (
                                <RecommendationCard key={rec.ticker} recommendation={rec} />
                              ))}
                            </div>
                          </motion.div>
                        );
                      })}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>

        {/* Footer */}
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="text-center mt-8 text-slate-400 text-sm"
        >
          <p>Powered by AI • Real-time market data • Investment recommendations</p>
        </motion.div>
      </div>
    </div>
  );
}

export default App; 