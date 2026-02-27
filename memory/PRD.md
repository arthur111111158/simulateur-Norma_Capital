# NEXUS Terminal - Global Market Intelligence Platform

## Original Problem Statement
Build a "Bloomberg-like Terminal" covering:
- Global stocks (US, Europe, Asia) + Commodities + Forex with real-time prices and historicals
- Real-time global news with automatic asset tagging
- World Map showing conflicts, geopolitical events, sanctions with impact scoring
- Supply Chain Graph showing company relationships (suppliers/customers) with risk analysis
- Advanced Technical Indicators for trading signals

## Architecture
- **Frontend**: React 18 + Tailwind CSS + Shadcn/UI + ReactFlow + React Simple Maps + Recharts
- **Backend**: FastAPI + Motor (MongoDB async)
- **Database**: MongoDB (with caching for news/conflicts)
- **Data Sources**: 
  - Yahoo Finance (real-time market data - 163+ global stocks)
  - NewsAPI (news aggregation - LIVE with MongoDB cache)
  - GDELT GEO API (geopolitical events - LIVE with MongoDB cache)

## User Personas
1. **Financial Analysts**: Need comprehensive market data and news in one terminal
2. **Portfolio Managers**: Require asset screening and risk assessment
3. **Risk Analysts**: Focus on geopolitical impacts and supply chain vulnerabilities
4. **Traders**: Need real-time quotes, technical indicators, and market movers

## What's Been Implemented

### 2026-02-27 - Global Market Coverage & Technical Analysis
- **163 Global Stocks Coverage**:
  - 48 US stocks (S&P 500 components, major tech, finance, healthcare)
  - 55 European stocks (CAC 40, DAX, FTSE 100, Euro Stoxx components)
  - 60 Asian stocks (Nikkei, KOSPI, Hang Seng, Taiwan, India, Singapore, Australia)
- **Global Indices**: S&P 500, Dow Jones, NASDAQ, CAC 40, DAX, FTSE 100, Nikkei, Hang Seng, Shanghai Composite
- **Technical Indicators**:
  - RSI (14-period)
  - MACD (12/26 with signal line)
  - SMA (20, 50, 200)
  - EMA (12, 26)
  - Bollinger Bands (20-period, 2 std dev)
  - ATR (14-period)
  - Stochastic Oscillator
  - OBV (On-Balance Volume)
  - Trading Signal (BUY/SELL/HOLD)
  - Trend Detection (Bullish/Bearish/Neutral)
- **Dynamic Impact Scoring**:
  - Score 0-100 based on geopolitical risk exposure
  - Risk factors from conflicts affecting assets
  - Risk level classification (LOW/MEDIUM/HIGH/CRITICAL)
- **MongoDB Caching**:
  - News articles cached for 1 hour
  - Conflict data cached for 2 hours
  - Reduces API calls and improves performance

### 2026-02-27 - NewsAPI & GDELT Integration
- Integrated NewsAPI for real-time news with automatic asset tagging
- Integrated GDELT GEO API for live geopolitical events
- News articles tagged with company tickers and macro topics
- Conflicts include real-time data from GDELT merged with baseline events

### Phase 1 - MVP Complete
- **Dashboard**: Global markets overview (US/Europe/Asia), watchlist, news, market movers, geopolitical alerts
- **Quote Page**: Real-time quotes, price charts, technical analysis, impact score, supply chain preview
- **News Terminal**: Full news feed with search, filters, trending topics
- **World Map**: Interactive conflict map with severity markers, impact scores, transmission channels
- **Supply Chain**: Company relationship graph with suppliers/customers, risk levels
- **Screener**: Global stock/commodity/forex filtering with region and sector filters

## Backend APIs

### Market Data
- `GET /api/market/quote/{symbol}` - Real-time quote
- `GET /api/market/quotes?symbols=...` - Multiple quotes
- `GET /api/market/history/{symbol}?period=&interval=` - Historical OHLCV
- `GET /api/market/technical/{symbol}` - Technical indicators (RSI, MACD, SMA, Bollinger, Signal, Trend)
- `GET /api/market/search?q=...` - Asset search across all markets
- `GET /api/market/movers?region=...` - Top gainers/losers by region
- `GET /api/market/indices?region=...` - Global indices by region
- `GET /api/market/universe` - Full list of available instruments

### News & Conflicts
- `GET /api/news` - News with filters (NewsAPI - LIVE, MongoDB cached)
- `GET /api/news/breaking` - Breaking headlines
- `GET /api/conflicts` - Geopolitical events (GDELT + Baseline - LIVE, MongoDB cached)
- `GET /api/conflicts/{id}` - Conflict detail

### Analysis
- `GET /api/impact/{symbol}` - Dynamic impact score with risk factors
- `GET /api/supplychain/{symbol}` - Company supply chain relationships

### User Data
- `GET/POST/DELETE /api/watchlist` - Watchlist CRUD
- `GET /api/screener?asset_type=&region=&sector=&min_change=&max_change=` - Asset screening

## 3rd Party Integrations Status
| Integration | Status | Notes |
|------------|--------|-------|
| Yahoo Finance | LIVE | 163+ global stocks, indices, commodities, forex |
| NewsAPI | LIVE | Real-time news with MongoDB cache |
| GDELT GEO API | LIVE | Geopolitical events with MongoDB cache |
| MongoDB | LIVE | Watchlist + News/Conflicts caching |

## Prioritized Backlog

### P0 - Critical (DONE)
- [x] Core terminal UI with navigation
- [x] Real-time stock quotes
- [x] Price charts with multiple timeframes
- [x] News feed with tagging (NewsAPI - LIVE)
- [x] Conflict map (GDELT - LIVE)
- [x] Supply chain graph
- [x] **Global stock coverage (US, Europe, Asia)**
- [x] **Technical indicators (RSI, MACD, SMA, Bollinger)**
- [x] **Dynamic impact scoring**
- [x] **MongoDB caching for news/conflicts**

### P1 - High Priority (Next)
- [ ] Real supply chain data (SEC filings parsing)
- [ ] Price alerts system with notifications
- [ ] Export to CSV functionality
- [ ] User authentication (JWT/OAuth)
- [ ] WebSocket for real-time updates

### P2 - Medium Priority
- [ ] Options chain data
- [ ] Earnings calendar
- [ ] Custom screener filters
- [ ] Historical impact score trends
- [ ] Correlation matrix

### P3 - Nice to Have
- [ ] Dark/Light theme toggle
- [ ] Mobile responsive design
- [ ] Push notifications
- [ ] Event replay feature
- [ ] Portfolio tracking

## Known Limitations
1. **Supply Chain Data**: Currently using enhanced mock data (not real SEC filing data)
2. **API Rate Limits**: Yahoo Finance can be slow with many sequential calls
3. **Quote Page Load Time**: 10-30 seconds due to multiple API calls

## Environment Configuration
- NewsAPI Key: Configured in backend/.env
- GDELT: No key required (public API)
- MongoDB: Configured in backend/.env

## Test Results
- Backend: 100% pass (22/22 tests)
- Frontend: 95% pass (minor cosmetic issues only)
- Last test report: /app/test_reports/iteration_2.json
