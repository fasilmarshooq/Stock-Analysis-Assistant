import axios from 'axios';
import { AnalysisRequest, AnalysisResponse, StatusUpdate } from '../types';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const analysisAPI = {
  // Start a new analysis
  startAnalysis: async (request: AnalysisRequest = {}): Promise<{ session_id: string; status: string; message: string }> => {
    const response = await api.post('/analyze', request);
    return response.data;
  },

  // Get analysis status and results
  getAnalysis: async (sessionId: string): Promise<AnalysisResponse> => {
    const response = await api.get(`/analysis/${sessionId}`);
    return response.data;
  },

  // Get simplified status for real-time updates
  getAnalysisStatus: async (sessionId: string): Promise<StatusUpdate> => {
    const response = await api.get(`/analysis/${sessionId}/status`);
    return response.data;
  },

  // Get portfolio data
  getPortfolio: async () => {
    const response = await api.get('/portfolio');
    return response.data;
  },

  // Get latest recommendations
  getLatestRecommendations: async (): Promise<AnalysisResponse> => {
    const response = await api.get('/recommendations/latest');
    return response.data;
  },
};

export default api; 