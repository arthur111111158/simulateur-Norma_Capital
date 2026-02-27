# NEXUS Terminal - Global Market Intelligence Platform

## Original Problem Statement
Build a "Bloomberg-like Terminal" covering:
- Global stocks (US, Europe, Asia) + Commodities + Forex with real-time prices and historicals
- Real-time global news with automatic asset tagging
- World Map showing conflicts, geopolitical events, sanctions with impact scoring
- Supply Chain Graph showing company relationships (suppliers/customers) with risk analysis
- Advanced Technical Indicators for trading signals
- **Options Chain data** for stock options (calls/puts)
- **Earnings Calendar** for upcoming company earnings announcements
- **Real-time updates** via WebSocket with polling fallback

## Architecture
- **Frontend**: React 18 + Tailwind CSS + Shadcn/UI + ReactFlow + React Simple Maps + Recharts
- **Backend**: FastAPI + Motor (MongoDB async)
- **Database**: MongoDB (with caching for news/conflicts/earnings)
- **Data Sources**: 
  - Yahoo Finance (real-time market data - 163+ global stocks, options, earnings)
  - NewsAPI (news aggregation - LIVE with MongoDB cache)
  - GDELT GEO API (geopolitical events - LIVE with MongoDB cache)

## User Personas
1. **Financial Analysts**: Need comprehensive market data and news in one terminal
2. **Portfolio Managers**: Require asset screening and risk assessment
3. **Risk Analysts**: Focus on geopolitical impacts and supply chain vulnerabilities
4. **Traders**: Need real-time quotes, technical indicators, and market movers
5. **Options Traders**: Require options chain data (calls/puts, IV, strike prices)

## What's Been Implemented

### 2026-02-27 - Options Chain, Earnings Calendar, Real-time Updates
- **Options Chain Feature**:
  - `/api/options/expirations/{symbol}` - Get available expiration dates
  - `/api/options/chain/{symbol}?expiration={date}` - Get calls/puts with strike, bid, ask, IV, OI
  - OptionsChain component displays on Quote page for stock symbols
  - Tabs for Calls and Puts with ITM/OTM badges
  
- **Earnings Calendar Feature**:
  - `/api/earnings/calendar?days={n}&region={region}` - Get upcoming earnings
  - `/api/earnings/symbol/{symbol}` - Get next earnings for specific symbol
  - New EarningsPage with grouped events by date
  - Region filter (US, Europe, Asia) and days selector
  - MongoDB caching for earnings data
  
- **Real-time Updates**:
  - WebSocket endpoint at `/ws/quotes` for real-time price updates
  - Polling fallback in useWebSocket hook for environments where WebSocket doesn't work
  - 10-second polling interval for subscribed symbols
  
- **Enhanced Supply Chain**:
  - yfinance fallback for stocks not in predefined list
  - Returns institutional holders and sector-based suppliers/customers
  - Works for any stock symbol now (JNJ, COST, etc.)

### 2026-02-27 - Global Market Coverage & Technical Analysis
- **163 Global Stocks Coverage**:
  - 48 US stocks (S&P 500 components, major tech, finance, healthcare)
  - 55 European stocks (CAC 40, DAX, FTSE 100, Euro Stoxx components)
  - 60 Asian stocks (Nikkei, KOSPI, Hang Seng, Taiwan, India, Singapore, Australia)
- **Global Indices**: S&P 500, Dow Jones, NASDAQ, CAC 40, DAX, FTSE 100, Nikkei, Hang Seng, Shanghai Composite
- **Technical Indicators**: RSI, MACD, SMA, EMA, Bollinger Bands, ATR, Stochastic, OBV
- **Dynamic Impact Scoring**: Score 0-100 based on geopolitical risk exposure
- **MongoDB Caching**: News (1 hour), Conflicts (2 hours), Earnings (6 hours)

## Backend APIs

### Market Data
- `GET /api/market/quote/{symbol}` - Real-time quote
- `GET /api/market/quotes?symbols=...` - Multiple quotes
- `GET /api/market/history/{symbol}?period=&interval=` - Historical OHLCV
- `GET /api/market/technical/{symbol}` - Technical indicators
- `GET /api/market/search?q=...` - Asset search
- `GET /api/market/movers?region=...` - Top gainers/losers
- `GET /api/market/indices?region=...` - Global indices
- `GET /api/market/universe` - Full list of instruments

### Options Chain (NEW)
- `GET /api/options/expirations/{symbol}` - Available expiration dates
- `GET /api/options/chain/{symbol}?expiration={date}` - Options chain (calls/puts)

### Earnings Calendar (NEW)
- `GET /api/earnings/calendar?days={n}&region={region}` - Upcoming earnings
- `GET /api/earnings/symbol/{symbol}` - Earnings for specific symbol

### News & Conflicts
- `GET /api/news` - News with filters (NewsAPI - LIVE, MongoDB cached)
- `GET /api/news/breaking` - Breaking headlines
- `GET /api/conflicts` - Geopolitical events (GDELT + Baseline - LIVE, MongoDB cached)
- `GET /api/conflicts/{id}` - Conflict detail

### Analysis
- `GET /api/impact/{symbol}` - Dynamic impact score
- `GET /api/supplychain/{symbol}` - Company supply chain (predefined + yfinance fallback)

### User Data
- `GET/POST/DELETE /api/watchlist` - Watchlist CRUD
- `GET /api/screener?...` - Asset screening

### WebSocket (NEW)
- `WS /ws/quotes` - Real-time quote updates (with polling fallback)

## Frontend Pages
- `/` - Dashboard with global markets overview
- `/quote?symbol={symbol}` - Quote page with chart, technicals, options chain
- `/news` - News terminal
- `/worldmap` - Interactive conflict map
- `/supplychain?symbol={symbol}` - Supply chain graph
- `/screener` - Asset screener
- `/earnings` - Earnings calendar (NEW)
- `/settings` - User settings

## 3rd Party Integrations Status
| Integration | Status | Notes |
|------------|--------|-------|
| Yahoo Finance | LIVE | 163+ global stocks, indices, commodities, forex, options, earnings |
| NewsAPI | LIVE | Real-time news with MongoDB cache |
| GDELT GEO API | LIVE | Geopolitical events with MongoDB cache |
| MongoDB | LIVE | Watchlist + News/Conflicts/Earnings caching |

## Prioritized Backlog

### P0 - Critical (DONE)
- [x] Core terminal UI with navigation
- [x] Real-time stock quotes
- [x] Price charts with multiple timeframes
- [x] News feed with tagging (NewsAPI - LIVE)
- [x] Conflict map (GDELT - LIVE)
- [x] Supply chain graph
- [x] Global stock coverage (US, Europe, Asia)
- [x] Technical indicators (RSI, MACD, SMA, Bollinger)
- [x] Dynamic impact scoring
- [x] MongoDB caching for news/conflicts
- [x] **Options chain data**
- [x] **Earnings calendar**
- [x] **WebSocket for real-time updates**
- [x] **Enhanced supply chain for all stocks**

### P1 - High Priority (Next)
- [ ] User authentication (JWT/OAuth)
- [ ] Price alerts system with notifications
- [ ] Export to CSV functionality
- [ ] Portfolio tracking

### P2 - Medium Priority
- [ ] Custom screener filters
- [ ] Historical impact score trends
- [ ] Correlation matrix
- [ ] Options greeks (delta, gamma, theta, vega)

### P3 - Nice to Have
- [ ] Dark/Light theme toggle
- [ ] Mobile responsive design
- [ ] Push notifications
- [ ] Event replay feature

## Known Limitations
1. **Quote Page Load Time**: 10-30 seconds due to multiple Yahoo Finance API calls
2. **WebSocket**: May not work through some proxies - polling fallback available
3. **Earnings Data**: Limited to 60 days ahead, some stocks may not have data

## Environment Configuration
- NewsAPI Key: Configured in backend/.env
- GDELT: No key required (public API)
- MongoDB: Configured in backend/.env

## Test Results
- Backend: 100% pass (16/16 tests)
- Frontend: 100% (all features working)
- Last test report: /app/test_reports/iteration_3.json
