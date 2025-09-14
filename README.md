# Stock Analysis Assistant

A modern AI-powered stock analysis application that fetches portfolio data from Google Sheets, analyzes stocks using Screener.in data, and provides intelligent buy/sell recommendations based on fundamental analysis and market signals.

## Features

- 🔥 **AI-Powered Analysis**: Implements a sophisticated investment decision matrix
- 📊 **Real-time Data**: Fetches live data from Google Sheets and Screener.in
- 🎯 **Smart Recommendations**: Categorizes stocks into Strong Buy, Good Buy, Consider, Hold, and Avoid
- 💫 **Modern UI**: Beautiful React interface with Cursor-style agent assistance
- ⚡ **Real-time Updates**: Live progress tracking during analysis
- 🌙 **Dark Theme**: Modern glassmorphism design with smooth animations

## Architecture

- **Backend**: FastAPI with SQLite database
- **Frontend**: React with TypeScript, Tailwind CSS, and Framer Motion
- **Data Sources**: Google Sheets (portfolio) + Screener.in (stock data)
- **Analysis Engine**: Custom implementation of the finance analyst master prompt

## Prerequisites

### Option 1: Docker (Recommended)
- Docker and Docker Compose

### Option 2: Local Development
- Python 3.10+
- Node.js 18+
- Poetry (for Python dependency management)
- Chrome/Chromium (for web scraping)

## Quick Start

### 🐳 Docker Setup (Recommended)

The easiest way to run the application is using Docker:

```bash
# Using Docker Compose (recommended)
./run-docker-compose.sh

# Or using Docker directly
./run-docker.sh
```

This will:
- Build the application
- Start both backend and frontend
- Make the app available at `http://localhost:3000`
- API available at `http://localhost:8000`

### 🛠️ Local Development Setup

#### 1. Backend Setup

```bash
# Install dependencies
poetry install

# Start the backend server
poetry run python start_backend.py
```

The backend will start at `http://localhost:8000`

#### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will start at `http://localhost:3000`

## Configuration

### Environment Variables Setup

1. **Copy the environment template:**
   ```bash
   cp env.example .env
   ```

2. **Update the `.env` file with your configuration:**
   ```bash
   # Database Configuration
   DATABASE_URL=sqlite:///stock_analysis.db

   # Google Sheets Configuration
   GOOGLE_SHEETS_URL=https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/gviz/tq?tqx=out:csv&sheet=stocks

   # Screener.in Configuration
   SCREENER_BASE_URL=https://www.screener.in/company/{}

   # News Service Configuration
   GOOGLE_SEARCH_BASE_URL=https://www.google.com/search?q={}&tbm=nws
   ```

3. **Replace `YOUR_SHEET_ID` with your actual Google Sheets ID**

### Google Sheets Setup

The application expects portfolio data in the following format:

| Ticker | Stock Name | Budget | Current Invested | Available | Total Quantity |
|--------|------------|--------|------------------|-----------|----------------|
| RELIANCE | Reliance Industries | 10000 | 5000 | 5000 | 10 |
| TCS | Tata Consultancy Services | 15000 | 8000 | 7000 | 5 |

**Important:** Update the `GOOGLE_SHEETS_URL` in your `.env` file to point to your own Google Sheet. The URL should be in the format:
```
https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/gviz/tq?tqx=out:csv&sheet=stocks
```

## Usage

1. **Open the application** at `http://localhost:3000`
2. **Click "Analyze My Portfolio"** to start the analysis
3. **Watch the real-time progress** as the system:
   - Fetches portfolio data from Google Sheets
   - Scrapes stock data from Screener.in
   - Analyzes each stock using the decision matrix
   - Generates buy/sell recommendations
4. **Review recommendations** categorized by investment strength
5. **View detailed analysis** including price metrics, fundamentals, and news sentiment

## Docker Management

### Using Docker Compose (Recommended)

```bash
# Start the application
./run-docker-compose.sh

# View logs
docker-compose logs -f

# Stop the application
docker-compose down

# Restart the application
docker-compose restart

# Check status
docker-compose ps
```

### Using Docker Directly

```bash
# Start the application
./run-docker.sh

# View logs
docker logs stock-analysis-assistant

# Stop the application
docker stop stock-analysis-assistant

# Remove the container
docker rm stock-analysis-assistant

# Enter the container
docker exec -it stock-analysis-assistant /bin/bash
```

## Investment Decision Matrix

The system uses a sophisticated decision matrix based on:

### 🔥 Strong Buy (₹2000-5000)
- >10% below 52W high
- P/E < 25
- ROCE > 15%
- Positive news sentiment

### 🟢 Good Buy (₹1000-3000)
- 5-10% below 52W high
- P/E < 30
- ROCE > 10%
- Decent fundamentals

### 🟡 Consider (₹500-1500)
- 3-5% below 52W high
- ROCE > 12%
- ROE > 10%
- Strong quality metrics

### ⚪ Hold
- Near 52W high (<3% below)
- Waiting for better entry

### 🔴 Avoid
- Poor fundamentals
- Overvalued
- Negative news sentiment

## API Endpoints

- `POST /api/analyze` - Start new analysis
- `GET /api/analysis/{session_id}` - Get analysis results
- `GET /api/analysis/{session_id}/status` - Get real-time status
- `GET /api/portfolio` - Get portfolio data
- `GET /api/recommendations/latest` - Get latest recommendations

## Development

### Backend Structure
```
backend/
├── main.py              # FastAPI application
├── database.py          # SQLAlchemy models
├── models.py            # Pydantic models
└── services/
    ├── portfolio_service.py   # Google Sheets integration
    ├── screener_service.py    # Screener.in scraping
    ├── news_service.py        # News sentiment analysis
    └── analysis_service.py    # Main analysis engine
```

### Frontend Structure
```
frontend/src/
├── App.tsx              # Main application
├── types/               # TypeScript definitions
├── services/            # API integration
└── components/          # React components
```

## Troubleshooting

### Backend Issues
- **Import errors**: Ensure you're using Poetry and all dependencies are installed
- **Database errors**: Delete `stock_analysis.db` to reset the database
- **Scraping failures**: Check if Screener.in is accessible and Chrome is installed

### Frontend Issues
- **Module not found**: Run `npm install` in the frontend directory
- **API connection**: Ensure backend is running on port 8000
- **Build errors**: Check TypeScript configuration and dependencies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Disclaimer

This application is for educational and research purposes only. Stock recommendations should not be considered as financial advice. Always do your own research and consult with financial advisors before making investment decisions. 