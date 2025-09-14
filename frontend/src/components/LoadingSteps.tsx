import React from 'react';
import { motion } from 'framer-motion';
import { Loader2, CheckCircle, Clock } from 'lucide-react';
import { AnalysisStatus } from '../types';

interface LoadingStepsProps {
  currentStatus: AnalysisStatus | null;
  statusMessage: string;
  progress: number;
}

const LoadingSteps: React.FC<LoadingStepsProps> = ({ currentStatus, statusMessage, progress }) => {
  const steps = [
    { 
      status: AnalysisStatus.PENDING, 
      message: 'Initializing analysis...',
      icon: Clock 
    },
    { 
      status: AnalysisStatus.FETCHING_PORTFOLIO, 
      message: 'Fetching your portfolio info...',
      icon: Loader2 
    },
    { 
      status: AnalysisStatus.FETCHING_SCREENER, 
      message: 'Fetching info from screener...',
      icon: Loader2 
    },
    { 
      status: AnalysisStatus.ANALYZING_STOCKS, 
      message: 'Analyzing the stocks...',
      icon: Loader2 
    },
    { 
      status: AnalysisStatus.COMPLETED, 
      message: 'Analysis completed!',
      icon: CheckCircle 
    }
  ];

  const getStepStatus = (stepStatus: AnalysisStatus) => {
    const currentIndex = steps.findIndex(step => step.status === currentStatus);
    const stepIndex = steps.findIndex(step => step.status === stepStatus);
    
    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'active';
    return 'pending';
  };

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      className="border-t border-white/10 bg-white/5"
    >
      <div className="p-6">
        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-slate-300">Progress</span>
            <span className="text-sm text-slate-300">{progress}%</span>
          </div>
          <div className="w-full bg-white/10 rounded-full h-2">
            <motion.div
              className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>

        {/* Current Status */}
        <div className="text-center mb-6">
          <motion.div
            key={statusMessage}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center justify-center gap-3 text-white"
          >
            <Loader2 className="w-5 h-5 animate-spin text-blue-400" />
            <span className="text-lg font-medium">{statusMessage}</span>
          </motion.div>
        </div>

        {/* Step Indicators */}
        <div className="space-y-3">
          {steps.slice(0, -1).map((step, index) => {
            const status = getStepStatus(step.status);
            const Icon = step.icon;
            
            return (
              <motion.div
                key={step.status}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`
                  flex items-center gap-3 p-3 rounded-lg transition-all duration-200
                  ${status === 'completed' 
                    ? 'bg-green-500/20 text-green-400' 
                    : status === 'active' 
                    ? 'bg-blue-500/20 text-blue-400' 
                    : 'bg-white/5 text-slate-400'
                  }
                `}
              >
                <div className={`
                  w-8 h-8 rounded-full flex items-center justify-center
                  ${status === 'completed' 
                    ? 'bg-green-500' 
                    : status === 'active' 
                    ? 'bg-blue-500' 
                    : 'bg-slate-600'
                  }
                `}>
                  {status === 'completed' ? (
                    <CheckCircle className="w-4 h-4 text-white" />
                  ) : status === 'active' ? (
                    <Icon className="w-4 h-4 text-white animate-spin" />
                  ) : (
                    <Clock className="w-4 h-4 text-white" />
                  )}
                </div>
                <span className="font-medium">{step.message}</span>
              </motion.div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
};

export default LoadingSteps; 