import requests
from bs4 import BeautifulSoup
import re
import logging
import os
from typing import Dict, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class ScreenerService:
    def __init__(self):
        self.base_url = os.getenv("SCREENER_BASE_URL", "https://www.screener.in/company/{}/")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def _setup_driver(self):
        """Setup Chrome driver for Selenium"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    
    def _extract_number(self, text: str) -> Optional[float]:
        """Extract number from text, handling Indian number format"""
        if not text or text.strip() in ['-', 'N/A', '']:
            return None
        
        # Remove commas and spaces
        cleaned = re.sub(r'[,\s]', '', text.strip())
        
        # Handle percentage
        if '%' in cleaned:
            cleaned = cleaned.replace('%', '')
        
        # Handle negative numbers
        if '(' in cleaned and ')' in cleaned:
            cleaned = '-' + cleaned.replace('(', '').replace(')', '')
        
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    async def fetch_stock_data(self, ticker: str) -> Dict[str, Optional[float]]:
        """
        Fetch stock data from Screener.in for a given ticker
        Returns dictionary with stock metrics
        """
        url = self.base_url.format(ticker.upper())
        logger.info(f"Fetching stock data for {ticker} from {url}")
        
        try:
            # Try with requests first (faster)
            logger.info(f"Attempting to fetch data with requests for {ticker}")
            response = self.session.get(url, timeout=10)
            logger.info(f"Response status for {ticker}: {response.status_code}")
            
            if response.status_code == 200:
                logger.info(f"Successfully fetched data with requests for {ticker}")
                data = self._parse_with_requests(response.text)
                logger.info(f"Parsed data for {ticker}: {data}")
                return data
            else:
                # Fallback to Selenium if requests fails
                logger.warning(f"Requests failed for {ticker}, trying Selenium")
                return await self._fetch_with_selenium(url)
                
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}", exc_info=True)
            return self._empty_stock_data()
    
    def _parse_with_requests(self, html_content: str) -> Dict[str, Optional[float]]:
        """Parse stock data using BeautifulSoup"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        data = {
            'current_price': None,
            'week_52_high': None,
            'week_52_low': None,
            'pe_ratio': None,
            'pb_ratio': None,
            'roce': None,
            'roe': None,
            'market_cap': None
        }
        
        try:
            # Current price - look for the actual stock price, not market cap
            price_element = None
            
            # Look for price in a more specific way
            # The stock price is usually in a span with class "number" that's not the market cap
            all_numbers = soup.find_all('span', {'class': 'number'})
            logger.info(f"Found {len(all_numbers)} number spans")
            
            for i, span in enumerate(all_numbers):
                span_text = span.text.strip()
                parent_text = span.parent.get_text() if span.parent else ""
                logger.info(f"Number {i}: {span_text}, parent context: {parent_text[:100]}")
                
                # Skip if it's clearly market cap (contains "Cr" or very large number)
                if 'cr' in parent_text.lower() or self._extract_number(span_text) > 100000:
                    logger.info(f"Skipping {span_text} - appears to be market cap")
                    continue
                
                # This looks like a stock price (reasonable range)
                if self._extract_number(span_text) and 10 < self._extract_number(span_text) < 10000:
                    price_element = span
                    logger.info(f"Found potential stock price: {span_text}")
                    break
            
            if price_element:
                data['current_price'] = self._extract_number(price_element.text)
                logger.info(f"Extracted current price: {data['current_price']}")
            else:
                logger.warning("Could not find current price element")
            
            # Find ratios section - try multiple approaches
            logger.info("Looking for ratios section...")
            ratios_section = soup.find('section', {'id': 'ratios'})
            if not ratios_section:
                # Try alternative selectors
                ratios_section = soup.find('div', {'class': 'ratios'}) or soup.find('div', {'id': 'ratios'})
            
            if ratios_section:
                logger.info("Found ratios section, extracting metrics...")
                
                # Extract all numbers from ratios section
                ratio_numbers = ratios_section.find_all('span', {'class': 'number'})
                logger.info(f"Found {len(ratio_numbers)} number spans in ratios section")
                
                for i, span in enumerate(ratio_numbers):
                    parent_text = span.parent.get_text() if span.parent else ""
                    span_text = span.text.strip()
                    number_value = self._extract_number(span_text)
                    
                    logger.info(f"Ratio span {i}: {span_text}, parent: {parent_text[:50]}...")
                    
                    # PE Ratio patterns
                    if any(keyword in parent_text.lower() for keyword in ['pe', 'p/e', 'price to earnings']):
                        data['pe_ratio'] = number_value
                        logger.info(f"Found PE ratio: {data['pe_ratio']}")
                    
                    # ROCE patterns
                    elif any(keyword in parent_text.lower() for keyword in ['roce', 'return on capital employed']):
                        data['roce'] = number_value
                        logger.info(f"Found ROCE: {data['roce']}")
                    
                    # ROE patterns
                    elif any(keyword in parent_text.lower() for keyword in ['roe', 'return on equity']):
                        data['roe'] = number_value
                        logger.info(f"Found ROE: {data['roe']}")
                    
                    # PB Ratio patterns
                    elif any(keyword in parent_text.lower() for keyword in ['pb', 'p/b', 'price to book']):
                        data['pb_ratio'] = number_value
                        logger.info(f"Found PB ratio: {data['pb_ratio']}")
            else:
                logger.warning("Could not find ratios section")
            
            # If ratios section not found, try searching the entire page
            if not data['pe_ratio'] or not data['roce'] or not data['roe']:
                logger.info("Ratios section not found, searching entire page...")
                page_text = soup.get_text()
                
                # PE Ratio patterns
                pe_patterns = [
                    r'Stock P/E[:\s]*([0-9,]+\.?[0-9]*)',
                    r'P/E[:\s]*([0-9,]+\.?[0-9]*)',
                    r'Price to Earnings[:\s]*([0-9,]+\.?[0-9]*)'
                ]
                
                for pattern in pe_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match and not data['pe_ratio']:
                        data['pe_ratio'] = self._extract_number(match.group(1))
                        logger.info(f"Found PE ratio via regex: {data['pe_ratio']}")
                        break
                
                # ROCE patterns
                roce_patterns = [
                    r'ROCE[:\s]*([0-9,]+\.?[0-9]*)',
                    r'Return on Capital Employed[:\s]*([0-9,]+\.?[0-9]*)'
                ]
                
                for pattern in roce_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match and not data['roce']:
                        data['roce'] = self._extract_number(match.group(1))
                        logger.info(f"Found ROCE via regex: {data['roce']}")
                        break
                
                # ROE patterns
                roe_patterns = [
                    r'ROE[:\s]*([0-9,]+\.?[0-9]*)',
                    r'Return on Equity[:\s]*([0-9,]+\.?[0-9]*)'
                ]
                
                for pattern in roe_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match and not data['roe']:
                        data['roe'] = self._extract_number(match.group(1))
                        logger.info(f"Found ROE via regex: {data['roe']}")
                        break
            
            # 52-week high/low - try multiple approaches
            logger.info("Looking for 52-week high/low data...")
            
            # Method 1: Look for spans with number class
            high_low_section = soup.find_all('span', {'class': 'number'})
            for span in high_low_section:
                parent_text = span.parent.get_text() if span.parent else ""
                span_text = span.text.strip()
                logger.info(f"Checking span: {span_text}, parent: {parent_text[:50]}...")
                
                if "52w high" in parent_text.lower() or "52 week high" in parent_text.lower():
                    data['week_52_high'] = self._extract_number(span.text)
                    logger.info(f"Found 52w high: {data['week_52_high']}")
                elif "52w low" in parent_text.lower() or "52 week low" in parent_text.lower():
                    data['week_52_low'] = self._extract_number(span.text)
                    logger.info(f"Found 52w low: {data['week_52_low']}")
            
            # Method 2: Look for specific text patterns
            if not data['week_52_high'] or not data['week_52_low']:
                page_text = soup.get_text()
                
                # Look for patterns like "52W High: 123.45" or "52 Week High: 123.45"
                high_patterns = [
                    r'52[Ww]\s*[Hh]igh[:\s]*([0-9,]+\.?[0-9]*)',
                    r'52\s*[Ww]eek\s*[Hh]igh[:\s]*([0-9,]+\.?[0-9]*)',
                    r'52W\s*[Hh]igh[:\s]*([0-9,]+\.?[0-9]*)',
                    r'₹\s*([0-9,]+\.?[0-9]*)\s*/\s*([0-9,]+\.?[0-9]*)',  # Pattern like ₹ 495 / 350
                    r'([0-9,]+\.?[0-9]*)\s*/\s*([0-9,]+\.?[0-9]*)'  # Pattern like 495 / 350
                ]
                
                low_patterns = [
                    r'52[Ww]\s*[Ll]ow[:\s]*([0-9,]+\.?[0-9]*)',
                    r'52\s*[Ww]eek\s*[Ll]ow[:\s]*([0-9,]+\.?[0-9]*)',
                    r'52W\s*[Ll]ow[:\s]*([0-9,]+\.?[0-9]*)'
                ]
                
                for pattern in high_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match and not data['week_52_high']:
                        if len(match.groups()) == 2:  # Pattern with two numbers
                            data['week_52_high'] = self._extract_number(match.group(1))
                            data['week_52_low'] = self._extract_number(match.group(2))
                            logger.info(f"Found 52w high/low via regex: {data['week_52_high']}/{data['week_52_low']}")
                        else:
                            data['week_52_high'] = self._extract_number(match.group(1))
                            logger.info(f"Found 52w high via regex: {data['week_52_high']}")
                        break
                
                for pattern in low_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match and not data['week_52_low']:
                        data['week_52_low'] = self._extract_number(match.group(1))
                        logger.info(f"Found 52w low via regex: {data['week_52_low']}")
                        break
            
            # Method 3: Look for price range patterns in the HTML
            if not data['week_52_high'] or not data['week_52_low']:
                # Look for patterns like "₹ 495 / 350" or "495 / 350"
                price_range_patterns = [
                    r'₹\s*([0-9,]+\.?[0-9]*)\s*/\s*([0-9,]+\.?[0-9]*)',
                    r'([0-9,]+\.?[0-9]*)\s*/\s*([0-9,]+\.?[0-9]*)'
                ]
                
                for pattern in price_range_patterns:
                    matches = re.findall(pattern, page_text)
                    for match in matches:
                        high_val = self._extract_number(match[0])
                        low_val = self._extract_number(match[1])
                        if high_val and low_val and high_val > low_val:
                            if not data['week_52_high']:
                                data['week_52_high'] = high_val
                                logger.info(f"Found potential 52w high: {data['week_52_high']}")
                            if not data['week_52_low']:
                                data['week_52_low'] = low_val
                                logger.info(f"Found potential 52w low: {data['week_52_low']}")
                            break
                    if data['week_52_high'] and data['week_52_low']:
                        break
            
        except Exception as e:
            print(f"Error parsing stock data: {e}")
        
        # Calculate percentage below 52w high
        if data['current_price'] and data['week_52_high']:
            data['percentage_below_52w_high'] = ((data['week_52_high'] - data['current_price']) / data['week_52_high']) * 100
        
        return data
    
    async def _fetch_with_selenium(self, url: str) -> Dict[str, Optional[float]]:
        """Fallback method using Selenium"""
        driver = None
        try:
            driver = self._setup_driver()
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "number"))
            )
            
            # Get page source and parse with BeautifulSoup
            html_content = driver.page_source
            return self._parse_with_requests(html_content)
            
        except Exception as e:
            print(f"Selenium fetch failed: {e}")
            return self._empty_stock_data()
        finally:
            if driver:
                driver.quit()
    
    def _empty_stock_data(self) -> Dict[str, Optional[float]]:
        """Return empty stock data structure"""
        return {
            'current_price': None,
            'week_52_high': None,
            'week_52_low': None,
            'pe_ratio': None,
            'pb_ratio': None,
            'roce': None,
            'roe': None,
            'market_cap': None,
            'percentage_below_52w_high': None
        } 