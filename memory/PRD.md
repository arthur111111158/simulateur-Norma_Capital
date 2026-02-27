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
  - NewsAPI (news aggregation - using mock for demo)
  - GDELT (geopolitical events - using mock for demo)

## User Personas
1. **Financial Analysts**: Need comprehensive market data and news in one terminal
2. **Portfolio Managers**: Require asset screening and risk assessment
3. **Risk Analysts**: Focus on geopolitical impacts and supply chain vulnerabilities
4. **Traders**: Need real-time quotes and market movers

## Core Requirements (Static)
- [ ] Real-time market quotes for stocks, commodities, forex
- [ ] Historical price charts with multiple timeframes
- [ ] Global news feed with entity tagging
- [ ] Interactive world conflict map
- [ ] Company supply chain visualization
- [ ] Asset screener with filters
- [ ] Watchlist management
- [ ] Impact scoring for geopolitical events

## What's Been Implemented (2026-02-27)
### Phase 1 - MVP Complete
- **Dashboard**: Markets overview, watchlist, news widget, market movers, geopolitical alerts
- **Quote Page**: Real-time quotes, price charts, supply chain preview, related news
- **News Terminal**: Full news feed with search, filters, trending topics, breaking news
- **World Map**: Interactive conflict map with severity markers, impact scores, transmission channels
- **Supply Chain**: Company relationship graph with suppliers/customers, risk levels
- **Screener**: Stock/commodity/forex filtering with change % filters
- **Settings**: Display and notification preferences

### Backend APIs
- /api/market/quote/{symbol} - Real-time quotes
- /api/market/history/{symbol} - Historical OHLCV
- /api/market/search - Asset search
- /api/market/movers - Top gainers/losers
- /api/news - News with filters
- /api/conflicts - Geopolitical events
- /api/supplychain/{symbol} - Company relationships
- /api/watchlist - CRUD operations
- /api/screener - Asset screening

## Prioritized Backlog

### P0 - Critical (Done)
- [x] Core terminal UI with navigation
- [x] Real-time stock quotes
- [x] Price charts
- [x] News feed with tagging
- [x] Conflict map
- [x] Supply chain graph

### P1 - High Priority (Next)
- [ ] Real NewsAPI integration (requires API key)
- [ ] GDELT real-time integration
- [ ] Price alerts system
- [ ] Export to CSV functionality
- [ ] User authentication

### P2 - Medium Priority
- [ ] Advanced charting indicators
- [ ] Options chain data
- [ ] Earnings calendar
- [ ] SEC filings integration for supply chain
- [ ] Custom screener filters

### P3 - Nice to Have
- [ ] Dark/Light theme toggle
- [ ] Mobile responsive design
- [ ] WebSocket for real-time updates
- [ ] Push notifications
- [ ] Event replay feature

## Next Tasks
1. Add NewsAPI key to enable real news feed
2. Implement GDELT API integration for live conflict data
3. Add price alert system with notifications
4. Implement CSV export for watchlist and screener
5. Add user authentication (JWT or OAuth)
