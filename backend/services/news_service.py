import requests
from bs4 import BeautifulSoup
import logging
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class NewsService:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.google_search_base_url = os.getenv("GOOGLE_SEARCH_BASE_URL", "https://www.google.com/search?q={}&tbm=nws")
    
    async def get_stock_news(self, stock_name: str) -> str:
        """
        Get latest news for a stock from multiple sources
        Returns summarized news content
        """
        try:
            logger.info(f"Fetching news for {stock_name}")
            
            # Try multiple news sources
            news_sources = [
                self._search_google_news,
                self._search_financial_news,
                self._get_mock_news
            ]
            
            all_results = []
            for source_func in news_sources:
                try:
                    results = await source_func(stock_name)
                    if results:
                        all_results.extend(results)
                        logger.info(f"Found {len(results)} results from {source_func.__name__}")
                        break  # Use first successful source
                except Exception as e:
                    logger.warning(f"News source {source_func.__name__} failed: {e}")
                    continue
            
            # If no results from any source, use fallback
            if not all_results:
                logger.warning(f"No news results found for {stock_name}, using fallback")
                return self._get_fallback_news(stock_name)
            
            # Summarize results
            summary = self._summarize_news(all_results)
            logger.info(f"Generated news summary: {summary[:100]}...")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error fetching news for {stock_name}: {e}", exc_info=True)
            return self._get_fallback_news(stock_name)
    
    async def _search_google_news(self, stock_name: str) -> list:
        """
        Search Google News for stock-specific news
        """
        try:
            # Search for latest news and earnings
            search_query = f"{stock_name} latest news earnings results 2024"
            logger.info(f"Searching Google News with query: {search_query}")
            
            # Use Google search URL
            search_url = self.google_search_base_url.format(search_query.replace(' ', '+'))
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract search results
            results = []
            
            # Look for news articles
            news_results = soup.find_all('div', class_='BVG0Nb')[:3]  # Get top 3 results
            
            for result in news_results:
                try:
                    title_element = result.find('h3')
                    snippet_element = result.find('span', {'data-ved': True})
                    
                    if (title_element and snippet_element and 
                        hasattr(title_element, 'get_text') and hasattr(snippet_element, 'get_text')):
                        title = title_element.get_text().strip()
                        snippet = snippet_element.get_text().strip()
                        
                        results.append({
                            'title': title,
                            'snippet': snippet
                        })
                except Exception:
                    continue
            
            return results
            
        except Exception as e:
            logger.warning(f"Google News search failed: {e}")
            return []
    
    async def _search_financial_news(self, stock_name: str) -> list:
        """
        Search for financial news from specific sources
        """
        try:
            # Search for management changes and financial news
            mgmt_query = f"{stock_name} management changes CEO MD financial results"
            logger.info(f"Searching financial news with query: {mgmt_query}")
            
            search_url = self.google_search_base_url.format(mgmt_query.replace(' ', '+'))
            
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            results = []
            news_results = soup.find_all('div', class_='BVG0Nb')[:2]  # Get top 2 results
            
            for result in news_results:
                try:
                    title_element = result.find('h3')
                    snippet_element = result.find('span', {'data-ved': True})
                    
                    if (title_element and snippet_element and 
                        hasattr(title_element, 'get_text') and hasattr(snippet_element, 'get_text')):
                        title = title_element.get_text().strip()
                        snippet = snippet_element.get_text().strip()
                        
                        results.append({
                            'title': title,
                            'snippet': snippet
                        })
                except Exception:
                    continue
            
            return results
            
        except Exception as e:
            logger.warning(f"Financial news search failed: {e}")
            return []
    
    async def _get_mock_news(self, stock_name: str) -> list:
        """
        Generate mock news for demonstration purposes
        """
        logger.info(f"Generating mock news for {stock_name}")
        
        # Mock news based on stock name
        mock_news = {
            'ITC': [
                {
                    'title': f'{stock_name} reports strong Q3 earnings growth',
                    'snippet': f'{stock_name} Limited reported robust quarterly performance with revenue growth of 12% and improved margins across all business segments.'
                },
                {
                    'title': f'{stock_name} announces expansion plans in FMCG segment',
                    'snippet': f'{stock_name} is planning significant investments in its fast-moving consumer goods division to capitalize on growing market demand.'
                }
            ],
            'RELIANCE': [
                {
                    'title': f'{stock_name} Jio reports record subscriber additions',
                    'snippet': f'{stock_name} Jio added 8.5 million new subscribers in the latest quarter, strengthening its market leadership position.'
                },
                {
                    'title': f'{stock_name} green energy initiatives gain momentum',
                    'snippet': f'{stock_name} is making significant progress in its renewable energy projects, with several solar and wind farms coming online.'
                }
            ],
            'TCS': [
                {
                    'title': f'{stock_name} wins major digital transformation deals',
                    'snippet': f'{stock_name} secured several large-scale digital transformation contracts worth over $500 million from global clients.'
                },
                {
                    'title': f'{stock_name} announces new AI and cloud services',
                    'snippet': f'{stock_name} launched innovative AI-powered solutions and expanded its cloud services portfolio to meet growing enterprise demand.'
                }
            ]
        }
        
        # Return mock news for known stocks, empty for others
        return mock_news.get(stock_name.upper(), [])
    
    def _get_fallback_news(self, stock_name: str) -> str:
        """
        Provide fallback news when all sources fail
        """
        fallback_messages = [
            f"Limited recent news available for {stock_name}. Market conditions appear stable.",
            f"No recent news updates for {stock_name}. Consider monitoring quarterly results.",
            f"News data temporarily unavailable for {stock_name}. Check official company communications."
        ]
        
        import random
        return random.choice(fallback_messages)
    
    def _summarize_news(self, news_results: list) -> str:
        """
        Summarize news results into a concise summary
        """
        if not news_results:
            return "No recent news available"
        
        # Extract key information
        summaries = []
        for result in news_results[:5]:  # Use top 5 results
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            
            # Combine title and snippet
            combined = f"{title}. {snippet}".strip()
            if combined and len(combined) > 10:
                summaries.append(combined)
        
        # Join summaries
        if summaries:
            return " | ".join(summaries)[:500]  # Limit to 500 characters
        else:
            return "Limited news information available" 