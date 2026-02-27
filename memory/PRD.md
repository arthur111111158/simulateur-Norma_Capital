# NEXUS Terminal - Global Market Intelligence Platform

## Original Problem Statement
Build a "Bloomberg-like Terminal" covering:
- Global stocks (US, Europe, Asia) + Commodities + Forex with real-time prices and historicals
- Real-time global news with automatic asset tagging
- World Map showing conflicts, geopolitical events, sanctions with impact scoring
- **Global Shipping Routes** - Maritime and Air Cargo routes with volume data
- Supply Chain Graph showing company relationships (suppliers/customers) with risk analysis
- Advanced Technical Indicators for trading signals
- **Options Chain data** for stock options (calls/puts)
- **Earnings Calendar** for upcoming company earnings announcements
- **Real-time updates** via WebSocket with polling fallback
- **Dedicated Commodities & Forex pages** with currency converter

## Architecture
- **Frontend**: React 18 + Tailwind CSS + Shadcn/UI + ReactFlow + React Simple Maps + Recharts
- **Backend**: FastAPI + Motor (MongoDB async)
- **Database**: MongoDB (with caching for news/conflicts/earnings/forex)
- **Data Sources**: 
  - Yahoo Finance (real-time market data - 163+ global stocks, options, earnings, forex rates, NEWS)
  - Boursorama (French financial news - LIVE scraping)
  - GDELT GEO API (geopolitical events - LIVE with MongoDB cache)
  - Static Shipping Data (27 seaports, 20 airports, 18 routes with dynamic disruption analysis)

## User Personas
1. **Financial Analysts**: Need comprehensive market data and news in one terminal
2. **Portfolio Managers**: Require asset screening and risk assessment
3. **Risk Analysts**: Focus on geopolitical impacts and supply chain vulnerabilities
4. **Traders**: Need real-time quotes, technical indicators, and market movers
5. **Options Traders**: Require options chain data (calls/puts, IV, strike prices)
6. **Logistics Analysts**: Need shipping routes and disruption monitoring

## What's Been Implemented

### 2026-02-27 - News Sources Change (Yahoo Finance + Boursorama)
- **Replaced NewsAPI** with:
  - **Yahoo Finance** for English financial news (stock market, earnings, S&P 500, etc.)
  - **Boursorama** for French financial news (web scraping)
- **Benefits**:
  - More relevant financial news (less general news)
  - No API key required for Yahoo Finance
  - Real-time French financial news from major French broker

### 2026-02-27 - Forex Currency Converter Fix
- **Fixed Forex converter** with cached rates to avoid yfinance rate limiting
- **5-minute TTL cache** for forex rates
- **Cross-currency conversion** via USD fallback for pairs not directly available

### 2026-02-27 - News/Conflicts Language Filtering (EN/FR Only)
- **Conflict titles** now generated in standardized English (not raw GDELT titles)
- **News API** supports `?languages=en,fr` parameter
- **Mock news** include French articles for fallback

### 2026-02-27 - Global Shipping Routes Visualization
- **Maritime Shipping Routes**:
  - 9 major maritime routes (Asia-Europe, Transpacific, Transatlantic, etc.)
  - 27 major seaports worldwide (Shanghai, Singapore, Rotterdam, etc.)
  - Volume data in TEU (Twenty-foot Equivalent Units)
  - Strategic chokepoints identification (Suez, Malacca, Panama, Hormuz, etc.)
  
- **Air Cargo Routes**:
  - 9 major air cargo routes (Hong Kong-Frankfurt, Shanghai-Anchorage-Memphis, etc.)
  - 20 cargo airports worldwide (Memphis, Anchorage, Hong Kong, Frankfurt, etc.)
  - Volume data in tonnes/year
  
- **Conflict Integration**:
  - Dynamic disruption level calculation based on current conflicts
  - Routes affected: Asia-Europe via Suez (40% - Red Sea/Yemen), Persian Gulf-Asia (100% - Iran), Intra-Asia (100% - South China Sea/Taiwan)
  - Volume at risk calculation (currently 57.6% of global shipping volume)

### 2026-02-27 - Options Chain, Earnings Calendar, Real-time Updates
- **Options Chain Feature**:
  - `/api/options/expirations/{symbol}` - Get available expiration dates
  - `/api/options/chain/{symbol}?expiration={date}` - Get calls/puts with strike, bid, ask, IV, OI
  - OptionsChain component displays on Quote page for stock symbols
  
- **Earnings Calendar Feature**:
  - `/api/earnings/calendar?days={n}&region={region}` - Get upcoming earnings
  - `/api/earnings/symbol/{symbol}` - Get next earnings for specific symbol
  - New EarningsPage with grouped events by date
  
- **Real-time Updates**:
  - WebSocket endpoint at `/ws/quotes` for real-time price updates
  - Polling fallback for environments where WebSocket doesn't work

### Previous Implementations
- 163 Global Stocks Coverage (US, Europe, Asia)
- Technical Indicators (RSI, MACD, SMA, EMA, Bollinger Bands, ATR)
- Dynamic Impact Scoring (0-100 based on geopolitical risk)
- MongoDB Caching for news/conflicts/earnings
- Supply Chain Graph with yfinance fallback

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

### Forex (with converter)
- `GET /api/forex/pairs` - All forex pairs with live rates
- `GET /api/forex/currencies` - List of available currencies
- `POST /api/forex/convert?amount=X&from_currency=EUR&to_currencies=USD,GBP` - Multi-currency conversion

### Options Chain
- `GET /api/options/expirations/{symbol}` - Available expiration dates
- `GET /api/options/chain/{symbol}?expiration={date}` - Options chain (calls/puts)

### Earnings Calendar
- `GET /api/earnings/calendar?days={n}&region={region}` - Upcoming earnings
- `GET /api/earnings/symbol/{symbol}` - Earnings for specific symbol

### Shipping Routes
- `GET /api/shipping/routes?route_type={all|maritime|air}` - Get shipping routes with disruption analysis
- `GET /api/shipping/ports` - Get all major ports and airports
- `GET /api/shipping/stats` - Get shipping statistics and risk summary

### News & Conflicts
- `GET /api/news?languages=en,fr` - News from Yahoo Finance (EN) + Boursorama (FR)
- `GET /api/news/breaking` - Breaking headlines
- `GET /api/conflicts` - Geopolitical events (GDELT - titles in English)
- `GET /api/conflicts/{id}` - Conflict detail

### Analysis
- `GET /api/impact/{symbol}` - Dynamic impact score
- `GET /api/supplychain/{symbol}` - Company supply chain

### WebSocket
- `WS /ws/quotes` - Real-time quote updates (with polling fallback)

## Frontend Pages
- `/` - Dashboard with global markets overview
- `/quote?symbol={symbol}` - Quote page with chart, technicals, options chain
- `/news` - News terminal (Yahoo Finance + Boursorama)
- `/worldmap` - Interactive map with conflicts AND shipping routes
- `/supplychain?symbol={symbol}` - Supply chain graph
- `/screener` - Asset screener
- `/earnings` - Earnings calendar
- `/commodities` - Commodities page
- `/forex` - Forex page with currency converter
- `/settings` - User settings

## 3rd Party Integrations Status
| Integration | Status | Notes |
|------------|--------|-------|
| Yahoo Finance | LIVE | 163+ stocks, forex, options, earnings, NEWS |
| Boursorama | LIVE | French financial news (web scraping) |
| GDELT GEO API | LIVE | Geopolitical events with MongoDB cache |
| MongoDB | LIVE | Caching for news/conflicts/earnings/forex |
| Shipping Data | STATIC | 27 seaports, 20 airports, 18 routes |

## Prioritized Backlog

### P0 - Critical (DONE)
- [x] Core terminal UI with navigation
- [x] Real-time stock quotes
- [x] Price charts with multiple timeframes
- [x] News feed with tagging (Yahoo Finance + Boursorama - LIVE)
- [x] Conflict map (GDELT - LIVE, English titles)
- [x] Supply chain graph
- [x] Global stock coverage (US, Europe, Asia)
- [x] Technical indicators (RSI, MACD, SMA, Bollinger)
- [x] Dynamic impact scoring
- [x] MongoDB caching for news/conflicts
- [x] Options chain data
- [x] Earnings calendar
- [x] WebSocket for real-time updates
- [x] Maritime shipping routes + volumes
- [x] Air cargo routes + volumes
- [x] Route disruption analysis based on conflicts
- [x] Forex currency converter
- [x] News in English AND French only

### P1 - High Priority (Next)
- [ ] Real-time shipping data via AIS API (MarineTraffic/VesselFinder)
- [ ] User authentication (JWT/OAuth)
- [ ] Price alerts system with notifications
- [ ] Export to CSV functionality
- [ ] Portfolio tracking

### P2 - Medium Priority
- [ ] Custom screener filters
- [ ] Historical impact score trends
- [ ] Correlation matrix
- [ ] Options greeks (delta, gamma, theta, vega)
- [ ] React hydration error fix (Dashboard.jsx)

### P3 - Nice to Have
- [ ] Dark/Light theme toggle
- [ ] Mobile responsive design
- [ ] Push notifications
- [ ] Event replay feature

## Known Limitations
1. **Quote Page Load Time**: 10-30 seconds due to multiple Yahoo Finance API calls
2. **WebSocket**: May not work through some proxies - polling fallback available
3. **Shipping Data**: Static routes/ports (not real-time vessel tracking)
4. **Forex Converter UI**: May have timing issues on first load (rates take time to cache)

## Environment Configuration
- GDELT: No key required (public API)
- Yahoo Finance: No key required (yfinance library)
- MongoDB: Configured in backend/.env

## Test Results
- Backend: 100% pass
- Frontend: 95% (minor hydration warning)
- Last test report: /app/test_reports/iteration_5.json
