# NEXUS Terminal - Bloomberg-like Market Intelligence Platform

## Original Problem Statement
Build "Bloomberg-like Terminal" covering:
- Actions + Commodities + Forex with real-time prices and historicals
- Real-time global news with automatic asset tagging
- World Map showing conflicts, geopolitical events, sanctions with impact scoring
- Supply Chain Graph showing company relationships (suppliers/customers) with risk analysis

## Architecture
- **Frontend**: React 18 + Tailwind CSS + Shadcn/UI + ReactFlow + React Simple Maps + Recharts
- **Backend**: FastAPI + Motor (MongoDB async)
- **Database**: MongoDB
- **Data Sources**: 
  - Yahoo Finance (real-time market data)
  - NewsAPI (news aggregation - LIVE)
  - GDELT GEO API (geopolitical events - LIVE)

## User Personas
1. **Financial Analysts**: Need comprehensive market data and news in one terminal
2. **Portfolio Managers**: Require asset screening and risk assessment
3. **Risk Analysts**: Focus on geopolitical impacts and supply chain vulnerabilities
4. **Traders**: Need real-time quotes and market movers

## Core Requirements (Static)
- [x] Real-time market quotes for stocks, commodities, forex
- [x] Historical price charts with multiple timeframes
- [x] Global news feed with entity tagging (NewsAPI - LIVE)
- [x] Interactive world conflict map (GDELT - LIVE)
- [x] Company supply chain visualization
- [x] Asset screener with filters
- [x] Watchlist management
- [x] Impact scoring for geopolitical events

## What's Been Implemented

### 2026-02-27 - NewsAPI & GDELT Integration
- Integrated NewsAPI for real-time news with automatic asset tagging
- Integrated GDELT GEO API for live geopolitical events
- News articles now tagged with company tickers (AAPL, MSFT, etc.) and topics (MACRO, OIL, GOLD)
- Conflicts now include real-time data from GDELT merged with baseline events
- Impact scoring calculated based on event severity and affected assets

### Phase 1 - MVP Complete (Previous Session)
- **Dashboard**: Markets overview, watchlist, news widget, market movers, geopolitical alerts
- **Quote Page**: Real-time quotes, price charts, supply chain preview, related news
- **News Terminal**: Full news feed with search, filters, trending topics, breaking news
- **World Map**: Interactive conflict map with severity markers, impact scores, transmission channels
- **Supply Chain**: Company relationship graph with suppliers/customers, risk levels
- **Screener**: Stock/commodity/forex filtering with change % filters
- **Settings**: Display and notification preferences

### Backend APIs
- /api/market/quote/{symbol} - Real-time quotes (yfinance)
- /api/market/history/{symbol} - Historical OHLCV (yfinance)
- /api/market/search - Asset search
- /api/market/movers - Top gainers/losers
- /api/news - News with filters (NewsAPI - LIVE)
- /api/conflicts - Geopolitical events (GDELT + Baseline - LIVE)
- /api/supplychain/{symbol} - Company relationships (mock data)
- /api/watchlist - CRUD operations
- /api/screener - Asset screening

## 3rd Party Integrations Status
| Integration | Status | Notes |
|------------|--------|-------|
| Yahoo Finance | LIVE | Market data |
| NewsAPI | LIVE | Real-time news (key configured) |
| GDELT GEO API | LIVE | Geopolitical events |
| MongoDB | Configured | Watchlist persistence |

## Prioritized Backlog

### P0 - Critical (Done)
- [x] Core terminal UI with navigation
- [x] Real-time stock quotes
- [x] Price charts
- [x] News feed with tagging (NewsAPI - LIVE)
- [x] Conflict map (GDELT - LIVE)
- [x] Supply chain graph

### P1 - High Priority (Next)
- [ ] Real supply chain data (SEC filings parsing)
- [ ] Price alerts system
- [ ] Export to CSV functionality
- [ ] User authentication
- [ ] MongoDB persistence for news/conflicts caching

### P2 - Medium Priority
- [ ] Advanced charting indicators
- [ ] Options chain data
- [ ] Earnings calendar
- [ ] Custom screener filters

### P3 - Nice to Have
- [ ] Dark/Light theme toggle
- [ ] Mobile responsive design
- [ ] WebSocket for real-time updates
- [ ] Push notifications
- [ ] Event replay feature

## Next Tasks
1. Implement price alert system with notifications
2. Add CSV export for watchlist and screener
3. Add user authentication (JWT or OAuth)
4. Implement real supply chain data from SEC filings
5. Add MongoDB caching for news and conflicts

## Environment Configuration
- NewsAPI Key: Configured in backend/.env
- GDELT: No key required (public API)
- MongoDB: Configured in backend/.env
