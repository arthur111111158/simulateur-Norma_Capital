from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import yfinance as yf
import httpx
import asyncio
import numpy as np
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# API Keys
NEWS_API_KEY = os.environ.get('NEWS_API_KEY', '')

# Create the main app
app = FastAPI(title="Nexus Terminal API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class AssetQuote(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: Optional[int] = None
    market_cap: Optional[float] = None
    currency: str = "USD"
    asset_type: str  # stock, commodity, forex
    bid: Optional[float] = None
    ask: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None
    previous_close: Optional[float] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class HistoricalData(BaseModel):
    symbol: str
    data: List[Dict[str, Any]]
    interval: str
    period: str

class NewsArticle(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    url: str
    source: str
    published_at: datetime
    image_url: Optional[str] = None
    tags: List[str] = []
    sentiment: Optional[str] = None
    country: Optional[str] = None

class ConflictEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    event_type: str
    location: Dict[str, Any]
    country: str
    region: Optional[str] = None
    start_date: datetime
    status: str  # ongoing, resolved
    severity: int  # 1-10
    description: str
    sources: List[str] = []
    impact_score: float
    affected_assets: List[str] = []
    transmission_channels: List[str] = []

class SupplyChainNode(BaseModel):
    id: str
    name: str
    symbol: Optional[str] = None
    node_type: str  # company, supplier, customer
    tier: int  # 1, 2, 3
    country: str
    sector: Optional[str] = None
    relationship: str  # supplier, customer, partner
    dependency_percent: Optional[float] = None
    risk_level: str = "low"  # low, medium, high, critical

class WatchlistItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default"
    symbol: str
    name: str
    asset_type: str
    added_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WatchlistCreate(BaseModel):
    symbol: str
    name: str
    asset_type: str

# ==================== MARKET DATA SERVICE ====================

def get_yahoo_quote(symbol: str) -> Optional[AssetQuote]:
    """Get real-time quote from Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        if not info or 'regularMarketPrice' not in info:
            # Try fast_info for faster response
            fast = ticker.fast_info
            if fast:
                return AssetQuote(
                    symbol=symbol,
                    name=info.get('shortName', symbol),
                    price=fast.get('last_price', 0) or fast.get('previous_close', 0),
                    change=0,
                    change_percent=0,
                    asset_type=determine_asset_type(symbol),
                    currency=info.get('currency', 'USD')
                )
            return None
        
        price = info.get('regularMarketPrice', 0) or info.get('currentPrice', 0)
        prev_close = info.get('regularMarketPreviousClose', 0) or info.get('previousClose', price)
        change = price - prev_close if prev_close else 0
        change_pct = (change / prev_close * 100) if prev_close else 0
        
        return AssetQuote(
            symbol=symbol,
            name=info.get('shortName', info.get('longName', symbol)),
            price=price,
            change=round(change, 2),
            change_percent=round(change_pct, 2),
            volume=info.get('regularMarketVolume'),
            market_cap=info.get('marketCap'),
            currency=info.get('currency', 'USD'),
            asset_type=determine_asset_type(symbol),
            bid=info.get('bid'),
            ask=info.get('ask'),
            high=info.get('regularMarketDayHigh', info.get('dayHigh')),
            low=info.get('regularMarketDayLow', info.get('dayLow')),
            open=info.get('regularMarketOpen', info.get('open')),
            previous_close=prev_close
        )
    except Exception as e:
        logger.error(f"Error fetching quote for {symbol}: {e}")
        return None

def determine_asset_type(symbol: str) -> str:
    """Determine if symbol is stock, commodity, or forex"""
    # Forex pairs
    forex_pairs = ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X', 'AUDUSD=X', 'USDCAD=X', 'USDCHF=X', 'NZDUSD=X']
    if symbol in forex_pairs or '=X' in symbol:
        return 'forex'
    
    # Commodities
    commodities = ['GC=F', 'SI=F', 'CL=F', 'NG=F', 'HG=F', 'PL=F', 'PA=F', 'ZC=F', 'ZW=F', 'ZS=F', 'KC=F', 'CC=F', 'SB=F', 'CT=F']
    if symbol in commodities or '=F' in symbol:
        return 'commodity'
    
    return 'stock'

def get_historical_data(symbol: str, period: str = "1mo", interval: str = "1d") -> Optional[HistoricalData]:
    """Get historical OHLCV data"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            return None
        
        data = []
        for index, row in hist.iterrows():
            data.append({
                'date': index.isoformat(),
                'open': round(row['Open'], 2),
                'high': round(row['High'], 2),
                'low': round(row['Low'], 2),
                'close': round(row['Close'], 2),
                'volume': int(row['Volume']) if row['Volume'] else 0
            })
        
        return HistoricalData(symbol=symbol, data=data, interval=interval, period=period)
    except Exception as e:
        logger.error(f"Error fetching history for {symbol}: {e}")
        return None

# ==================== NEWS SERVICE ====================

async def fetch_news(query: str = None, country: str = None, category: str = None, page_size: int = 20) -> List[NewsArticle]:
    """Fetch news from NewsAPI"""
    if not NEWS_API_KEY:
        # Return mock news if no API key
        return get_mock_news()
    
    try:
        async with httpx.AsyncClient() as client:
            params = {
                'apiKey': NEWS_API_KEY,
                'pageSize': page_size,
                'language': 'en'
            }
            
            if query:
                params['q'] = query
                url = 'https://newsapi.org/v2/everything'
            else:
                url = 'https://newsapi.org/v2/top-headlines'
                if country:
                    params['country'] = country
                if category:
                    params['category'] = category
            
            response = await client.get(url, params=params, timeout=10.0)
            data = response.json()
            
            if data.get('status') != 'ok':
                return get_mock_news()
            
            articles = []
            for article in data.get('articles', []):
                # Extract tags from title/description
                tags = extract_tags(article.get('title', '') + ' ' + (article.get('description') or ''))
                
                articles.append(NewsArticle(
                    title=article.get('title', ''),
                    description=article.get('description'),
                    content=article.get('content'),
                    url=article.get('url', ''),
                    source=article.get('source', {}).get('name', 'Unknown'),
                    published_at=datetime.fromisoformat(article.get('publishedAt', '').replace('Z', '+00:00')) if article.get('publishedAt') else datetime.now(timezone.utc),
                    image_url=article.get('urlToImage'),
                    tags=tags,
                    country=country
                ))
            
            return articles
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return get_mock_news()

def extract_tags(text: str) -> List[str]:
    """Extract relevant tags from text"""
    tags = []
    text_lower = text.lower()
    
    # Check for tickers/companies
    companies = {
        'apple': 'AAPL', 'microsoft': 'MSFT', 'google': 'GOOGL', 'amazon': 'AMZN',
        'meta': 'META', 'tesla': 'TSLA', 'nvidia': 'NVDA', 'netflix': 'NFLX'
    }
    for company, ticker in companies.items():
        if company in text_lower:
            tags.append(ticker)
    
    # Check for commodities
    commodities = ['oil', 'gold', 'silver', 'natural gas', 'copper', 'wheat', 'corn']
    for commodity in commodities:
        if commodity in text_lower:
            tags.append(commodity.upper())
    
    # Check for macro topics
    macro = ['fed', 'interest rate', 'inflation', 'gdp', 'unemployment', 'trade war', 'tariff']
    for topic in macro:
        if topic in text_lower:
            tags.append('MACRO')
            break
    
    return list(set(tags))

def get_mock_news() -> List[NewsArticle]:
    """Return mock news for demo purposes"""
    return [
        NewsArticle(
            title="Fed Signals Potential Rate Cuts Amid Economic Uncertainty",
            description="Federal Reserve officials hint at possible interest rate reductions as inflation shows signs of cooling.",
            url="https://example.com/news/1",
            source="Financial Times",
            published_at=datetime.now(timezone.utc) - timedelta(hours=1),
            tags=["MACRO", "FED", "RATES"],
            sentiment="neutral"
        ),
        NewsArticle(
            title="Oil Prices Surge on Middle East Tensions",
            description="Crude oil futures jump 3% as geopolitical risks in the Middle East intensify.",
            url="https://example.com/news/2",
            source="Reuters",
            published_at=datetime.now(timezone.utc) - timedelta(hours=2),
            tags=["OIL", "COMMODITY", "GEOPOLITICS"],
            sentiment="negative"
        ),
        NewsArticle(
            title="Tech Giants Report Strong Q4 Earnings",
            description="Apple, Microsoft, and Google exceed analyst expectations with robust revenue growth.",
            url="https://example.com/news/3",
            source="Bloomberg",
            published_at=datetime.now(timezone.utc) - timedelta(hours=3),
            tags=["AAPL", "MSFT", "GOOGL", "TECH"],
            sentiment="positive"
        ),
        NewsArticle(
            title="Gold Hits Record High as Dollar Weakens",
            description="Safe-haven demand pushes gold prices to all-time highs amid currency volatility.",
            url="https://example.com/news/4",
            source="CNBC",
            published_at=datetime.now(timezone.utc) - timedelta(hours=4),
            tags=["GOLD", "COMMODITY", "USD"],
            sentiment="positive"
        ),
        NewsArticle(
            title="European Markets Rally on ECB Stimulus Hopes",
            description="European equities gain as traders anticipate continued monetary support from the ECB.",
            url="https://example.com/news/5",
            source="MarketWatch",
            published_at=datetime.now(timezone.utc) - timedelta(hours=5),
            tags=["EUROPE", "ECB", "MACRO"],
            sentiment="positive"
        )
    ]

# ==================== CONFLICT/GEOPOLITICAL SERVICE ====================

# Country to coordinates mapping for GDELT events
COUNTRY_COORDS = {
    "Ukraine": {"lat": 48.3794, "lng": 31.1656},
    "Russia": {"lat": 55.7558, "lng": 37.6173},
    "Israel": {"lat": 31.0461, "lng": 34.8516},
    "Palestine": {"lat": 31.9522, "lng": 35.2332},
    "Gaza": {"lat": 31.5, "lng": 34.47},
    "Iran": {"lat": 32.4279, "lng": 53.6880},
    "Yemen": {"lat": 15.5527, "lng": 48.5164},
    "Syria": {"lat": 34.8021, "lng": 38.9968},
    "Taiwan": {"lat": 23.6978, "lng": 120.9605},
    "China": {"lat": 35.8617, "lng": 104.1954},
    "North Korea": {"lat": 40.3399, "lng": 127.5101},
    "South Korea": {"lat": 35.9078, "lng": 127.7669},
    "Philippines": {"lat": 12.8797, "lng": 121.7740},
    "Myanmar": {"lat": 21.9162, "lng": 95.9560},
    "Sudan": {"lat": 12.8628, "lng": 30.2176},
    "Libya": {"lat": 26.3351, "lng": 17.2283},
    "Lebanon": {"lat": 33.8547, "lng": 35.8623},
    "Saudi Arabia": {"lat": 23.8859, "lng": 45.0792},
    "Iraq": {"lat": 33.2232, "lng": 43.6793},
    "Afghanistan": {"lat": 33.9391, "lng": 67.7100},
    "Pakistan": {"lat": 30.3753, "lng": 69.3451},
    "India": {"lat": 20.5937, "lng": 78.9629},
    "Venezuela": {"lat": 6.4238, "lng": -66.5897},
    "Mexico": {"lat": 23.6345, "lng": -102.5528},
    "United States": {"lat": 37.0902, "lng": -95.7129},
    "France": {"lat": 46.2276, "lng": 2.2137},
    "Germany": {"lat": 51.1657, "lng": 10.4515},
    "United Kingdom": {"lat": 55.3781, "lng": -3.4360},
}

# Event type mapping based on GDELT CAMEO codes
GDELT_EVENT_TYPES = {
    "PROTEST": "civil_unrest",
    "FIGHT": "armed_conflict",
    "ASSAULT": "armed_conflict",
    "COERCE": "sanctions",
    "THREATEN": "geopolitical_tension",
    "DEMAND": "geopolitical_tension",
    "DISAPPROVE": "diplomatic_tension",
    "REDUCE_RELATIONS": "diplomatic_tension",
    "MILITARY": "military_action",
}

# Country to affected assets mapping
COUNTRY_AFFECTED_ASSETS = {
    "Ukraine": ["ZW=F", "ZC=F", "NG=F", "EURUSD=X"],
    "Russia": ["NG=F", "CL=F", "EURUSD=X", "GC=F"],
    "Israel": ["CL=F", "GC=F", "XOM", "CVX"],
    "Palestine": ["CL=F", "GC=F"],
    "Gaza": ["CL=F", "GC=F"],
    "Iran": ["CL=F", "BNO", "GC=F"],
    "Yemen": ["CL=F", "MAERSK.CO", "ZIM"],
    "Syria": ["CL=F", "GC=F"],
    "Taiwan": ["TSM", "NVDA", "AMD", "INTC"],
    "China": ["FXI", "BABA", "TSM", "AAPL"],
    "North Korea": ["GC=F", "USDJPY=X"],
    "South Korea": ["005930.KS", "USDJPY=X"],
    "Philippines": ["FXI", "EWM"],
    "Saudi Arabia": ["CL=F", "XOM", "CVX"],
    "Venezuela": ["CL=F", "PBR"],
}

# Transmission channels by region/event type
TRANSMISSION_CHANNELS = {
    "armed_conflict": ["Energy", "Defense", "Safe Haven FX", "Agriculture"],
    "sanctions": ["Finance", "Energy", "Trade"],
    "geopolitical_tension": ["Trade", "Technology", "Defense"],
    "civil_unrest": ["Consumer Goods", "Trade", "Finance"],
    "shipping_chokepoint": ["Shipping", "Energy", "Consumer Goods"],
    "diplomatic_tension": ["Trade", "Finance"],
    "military_action": ["Energy", "Defense", "Safe Haven FX"],
}

async def fetch_gdelt_events() -> List[Dict[str, Any]]:
    """Fetch events from GDELT GEO API"""
    try:
        async with httpx.AsyncClient() as http_client:
            # GDELT GEO API for geopolitical events with location data
            url = "https://api.gdeltproject.org/api/v2/geo/geo"
            params = {
                "query": "war conflict",
                "format": "geojson"
            }
            
            response = await http_client.get(url, params=params, timeout=15.0)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    features = data.get("features", [])
                    logger.info(f"GDELT returned {len(features)} geo features")
                    return features[:50]  # Limit to 50 features for processing
                except Exception as parse_error:
                    logger.warning(f"GDELT JSON parse error: {parse_error}")
                    return []
            else:
                logger.warning(f"GDELT API returned status {response.status_code}")
                return []
    except Exception as e:
        logger.error(f"Error fetching GDELT events: {e}")
        return []

def parse_gdelt_geo_to_conflict(feature: Dict[str, Any], index: int) -> Optional[ConflictEvent]:
    """Parse a GDELT GEO feature into a ConflictEvent"""
    try:
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        
        country_name = properties.get("name", "")
        event_count = properties.get("count", 0)
        html_content = properties.get("html", "")
        
        # Skip if country not recognized
        if country_name not in COUNTRY_COORDS and country_name not in [
            "Afghanistan", "Pakistan", "India", "China", "Russia", "Ukraine", 
            "Israel", "Iran", "Syria", "Yemen", "Iraq", "Lebanon", "Gaza",
            "Taiwan", "North Korea", "South Korea", "Myanmar", "Philippines",
            "Sudan", "Libya", "Venezuela", "Mexico"
        ]:
            return None
        
        # Get coordinates from GeoJSON or fallback
        coords = geometry.get("coordinates", [0, 0])
        lat = coords[1] if len(coords) > 1 else COUNTRY_COORDS.get(country_name, {}).get("lat", 0)
        lng = coords[0] if coords else COUNTRY_COORDS.get(country_name, {}).get("lng", 0)
        
        # Extract title from HTML if available
        import re
        title_match = re.search(r'title="([^"]+)"', html_content)
        if title_match:
            title = title_match.group(1)[:150]
        else:
            title = f"Geopolitical Activity in {country_name}"
        
        # Determine severity based on event count
        severity = min(9, max(4, event_count // 200 + 4))
        
        # Determine event type from title/content
        event_type = "geopolitical_tension"
        content_lower = (title + html_content).lower()
        if any(word in content_lower for word in ["war", "attack", "strike", "bomb", "military", "combat", "savaş"]):
            event_type = "armed_conflict"
            severity = min(9, severity + 1)
        elif any(word in content_lower for word in ["sanction", "embargo", "restrict"]):
            event_type = "sanctions"
        elif any(word in content_lower for word in ["protest", "demonstration", "riot"]):
            event_type = "civil_unrest"
        elif any(word in content_lower for word in ["tension", "threat", "warning"]):
            event_type = "geopolitical_tension"
        
        # Get affected assets
        affected_assets = COUNTRY_AFFECTED_ASSETS.get(country_name, ["GC=F"])
        
        # Get transmission channels
        channels = TRANSMISSION_CHANNELS.get(event_type, ["Trade", "Finance"])
        
        # Calculate impact score
        impact_score = min(95, severity * 8 + len(affected_assets) * 3 + event_count // 100)
        
        # Determine region
        region_map = {
            "Ukraine": "Eastern Europe", "Russia": "Eastern Europe",
            "Israel": "Middle East", "Palestine": "Middle East", "Gaza": "Middle East",
            "Iran": "Middle East", "Yemen": "Middle East", "Syria": "Middle East",
            "Saudi Arabia": "Middle East", "Iraq": "Middle East", "Lebanon": "Middle East",
            "Taiwan": "Asia Pacific", "China": "Asia Pacific", "North Korea": "Asia Pacific",
            "South Korea": "Asia Pacific", "Philippines": "Southeast Asia", "Myanmar": "Southeast Asia",
            "Afghanistan": "Central Asia", "Pakistan": "South Asia", "India": "South Asia",
            "Sudan": "Africa", "Libya": "Africa",
            "Venezuela": "South America", "Mexico": "North America",
        }
        region = region_map.get(country_name, "Unknown")
        
        return ConflictEvent(
            id=f"gdelt_geo_{index}_{hash(country_name) % 100000}",
            title=title,
            event_type=event_type,
            location={"lat": lat, "lng": lng, "type": "point"},
            country=country_name,
            region=region,
            start_date=datetime.now(timezone.utc) - timedelta(hours=index),
            status="ongoing",
            severity=severity,
            description=f"GDELT reports {event_count} related events. {title[:200]}",
            sources=["GDELT", "Multiple News Sources"],
            impact_score=impact_score,
            affected_assets=affected_assets[:5],
            transmission_channels=channels[:4]
        )
    except Exception as e:
        logger.error(f"Error parsing GDELT geo feature: {e}")
        return None

async def fetch_conflicts() -> List[ConflictEvent]:
    """Fetch geopolitical events from GDELT API with fallback to baseline data"""
    try:
        # Fetch from GDELT GEO API
        gdelt_features = await fetch_gdelt_events()
        
        if gdelt_features:
            conflicts = []
            seen_countries = set()
            
            for i, feature in enumerate(gdelt_features):
                conflict = parse_gdelt_geo_to_conflict(feature, i)
                if conflict and conflict.country not in seen_countries:
                    seen_countries.add(conflict.country)
                    conflicts.append(conflict)
            
            # Add baseline conflicts for countries not covered by GDELT
            baseline_conflicts = get_baseline_conflicts()
            for bc in baseline_conflicts:
                if bc.country not in seen_countries:
                    conflicts.append(bc)
                    seen_countries.add(bc.country)
            
            if conflicts:
                # Sort by impact score descending
                conflicts.sort(key=lambda x: x.impact_score, reverse=True)
                logger.info(f"Returning {len(conflicts)} conflicts (GDELT + baseline)")
                return conflicts[:20]
        
        # Fallback to baseline if GDELT fails
        logger.info("Using baseline conflicts (GDELT unavailable)")
        return get_baseline_conflicts()
        
    except Exception as e:
        logger.error(f"Error in fetch_conflicts: {e}")
        return get_baseline_conflicts()

def get_baseline_conflicts() -> List[ConflictEvent]:
    """Return baseline persistent conflicts"""
    return [
        ConflictEvent(
            id="baseline_ukraine",
            title="Ukraine-Russia Conflict",
            event_type="armed_conflict",
            location={"lat": 48.3794, "lng": 31.1656, "type": "polygon"},
            country="Ukraine",
            region="Eastern Europe",
            start_date=datetime(2022, 2, 24, tzinfo=timezone.utc),
            status="ongoing",
            severity=9,
            description="Ongoing military conflict affecting energy supplies and grain exports.",
            sources=["UN", "OSCE", "NATO"],
            impact_score=85.5,
            affected_assets=["GC=F", "ZW=F", "NG=F", "EURUSD=X"],
            transmission_channels=["Energy", "Agriculture", "Defense", "Safe Haven FX"]
        ),
        ConflictEvent(
            id="baseline_redsea",
            title="Red Sea Shipping Disruptions",
            event_type="shipping_chokepoint",
            location={"lat": 13.5, "lng": 42.5, "type": "point"},
            country="Yemen",
            region="Middle East",
            start_date=datetime(2023, 11, 1, tzinfo=timezone.utc),
            status="ongoing",
            severity=7,
            description="Houthi attacks disrupting global shipping through the Red Sea.",
            sources=["IMO", "Reuters"],
            impact_score=72.0,
            affected_assets=["CL=F", "MAERSK.CO"],
            transmission_channels=["Shipping", "Energy", "Consumer Goods"]
        ),
        ConflictEvent(
            id="baseline_taiwan",
            title="Taiwan Strait Tensions",
            event_type="geopolitical_tension",
            location={"lat": 24.0, "lng": 121.0, "type": "polygon"},
            country="Taiwan",
            region="Asia Pacific",
            start_date=datetime(2022, 8, 1, tzinfo=timezone.utc),
            status="ongoing",
            severity=8,
            description="Elevated military tensions in the Taiwan Strait affecting semiconductor supply chains.",
            sources=["DoD", "CSIS"],
            impact_score=78.0,
            affected_assets=["TSM", "NVDA", "AMD", "INTC"],
            transmission_channels=["Semiconductors", "Technology", "Defense"]
        ),
        ConflictEvent(
            id="baseline_iran",
            title="Iran Sanctions & Regional Tensions",
            event_type="sanctions",
            location={"lat": 32.4279, "lng": 53.6880, "type": "polygon"},
            country="Iran",
            region="Middle East",
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            status="ongoing",
            severity=6,
            description="Expanded sanctions affecting oil exports and regional stability.",
            sources=["OFAC", "EU"],
            impact_score=65.0,
            affected_assets=["CL=F", "BNO"],
            transmission_channels=["Energy", "Finance"]
        ),
        ConflictEvent(
            id="baseline_southchinasea",
            title="South China Sea Disputes",
            event_type="territorial_dispute",
            location={"lat": 12.0, "lng": 114.0, "type": "polygon"},
            country="Philippines",
            region="Southeast Asia",
            start_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            status="ongoing",
            severity=5,
            description="Ongoing territorial disputes affecting regional shipping lanes.",
            sources=["ASEAN", "ICJ"],
            impact_score=55.0,
            affected_assets=["FXI", "EWM"],
            transmission_channels=["Shipping", "Trade"]
        )
    ]

# ==================== SUPPLY CHAIN SERVICE ====================

def get_supply_chain(symbol: str) -> List[SupplyChainNode]:
    """Get supply chain data for a company (mock data for demo)"""
    # In production, this would parse SEC filings and use supply chain databases
    supply_chains = {
        'AAPL': [
            SupplyChainNode(id="tsmc", name="Taiwan Semiconductor", symbol="TSM", node_type="supplier", tier=1, country="Taiwan", sector="Semiconductors", relationship="supplier", dependency_percent=25.0, risk_level="high"),
            SupplyChainNode(id="foxconn", name="Foxconn", symbol="2317.TW", node_type="supplier", tier=1, country="Taiwan", sector="Manufacturing", relationship="supplier", dependency_percent=50.0, risk_level="high"),
            SupplyChainNode(id="samsung", name="Samsung Display", symbol="005930.KS", node_type="supplier", tier=1, country="South Korea", sector="Displays", relationship="supplier", dependency_percent=30.0, risk_level="medium"),
            SupplyChainNode(id="att", name="AT&T", symbol="T", node_type="customer", tier=1, country="USA", sector="Telecom", relationship="customer", dependency_percent=15.0, risk_level="low"),
            SupplyChainNode(id="verizon", name="Verizon", symbol="VZ", node_type="customer", tier=1, country="USA", sector="Telecom", relationship="customer", dependency_percent=12.0, risk_level="low"),
            SupplyChainNode(id="bestbuy", name="Best Buy", symbol="BBY", node_type="customer", tier=1, country="USA", sector="Retail", relationship="customer", dependency_percent=8.0, risk_level="low"),
        ],
        'TSLA': [
            SupplyChainNode(id="panasonic", name="Panasonic", symbol="PCRFY", node_type="supplier", tier=1, country="Japan", sector="Batteries", relationship="supplier", dependency_percent=35.0, risk_level="high"),
            SupplyChainNode(id="catl", name="CATL", symbol="300750.SZ", node_type="supplier", tier=1, country="China", sector="Batteries", relationship="supplier", dependency_percent=25.0, risk_level="high"),
            SupplyChainNode(id="lg_energy", name="LG Energy Solution", symbol="373220.KS", node_type="supplier", tier=1, country="South Korea", sector="Batteries", relationship="supplier", dependency_percent=20.0, risk_level="medium"),
            SupplyChainNode(id="hertz", name="Hertz", symbol="HTZ", node_type="customer", tier=1, country="USA", sector="Rental", relationship="customer", dependency_percent=5.0, risk_level="low"),
        ],
        'NVDA': [
            SupplyChainNode(id="tsmc_nvda", name="Taiwan Semiconductor", symbol="TSM", node_type="supplier", tier=1, country="Taiwan", sector="Semiconductors", relationship="supplier", dependency_percent=100.0, risk_level="critical"),
            SupplyChainNode(id="sk_hynix", name="SK Hynix", symbol="000660.KS", node_type="supplier", tier=1, country="South Korea", sector="Memory", relationship="supplier", dependency_percent=40.0, risk_level="high"),
            SupplyChainNode(id="micron", name="Micron", symbol="MU", node_type="supplier", tier=1, country="USA", sector="Memory", relationship="supplier", dependency_percent=30.0, risk_level="medium"),
            SupplyChainNode(id="msft_nvda", name="Microsoft", symbol="MSFT", node_type="customer", tier=1, country="USA", sector="Technology", relationship="customer", dependency_percent=20.0, risk_level="low"),
            SupplyChainNode(id="meta_nvda", name="Meta Platforms", symbol="META", node_type="customer", tier=1, country="USA", sector="Technology", relationship="customer", dependency_percent=15.0, risk_level="low"),
            SupplyChainNode(id="amzn_nvda", name="Amazon Web Services", symbol="AMZN", node_type="customer", tier=1, country="USA", sector="Cloud", relationship="customer", dependency_percent=18.0, risk_level="low"),
        ]
    }
    
    return supply_chains.get(symbol.upper(), [])

# ==================== API ROUTES ====================

@api_router.get("/")
async def root():
    return {"message": "Nexus Terminal API", "version": "1.0.0"}

# Market Data Routes
@api_router.get("/market/quote/{symbol}", response_model=Optional[AssetQuote])
async def get_quote(symbol: str):
    """Get real-time quote for a symbol"""
    quote = get_yahoo_quote(symbol.upper())
    if not quote:
        raise HTTPException(status_code=404, detail=f"Quote not found for {symbol}")
    return quote

@api_router.get("/market/quotes")
async def get_multiple_quotes(symbols: str = Query(..., description="Comma-separated symbols")):
    """Get quotes for multiple symbols"""
    symbol_list = [s.strip().upper() for s in symbols.split(',')]
    quotes = []
    for symbol in symbol_list:
        quote = get_yahoo_quote(symbol)
        if quote:
            quotes.append(quote)
    return {"quotes": quotes}

@api_router.get("/market/history/{symbol}", response_model=Optional[HistoricalData])
async def get_history(
    symbol: str,
    period: str = Query("1mo", description="1d,5d,1mo,3mo,6mo,1y,2y,5y,max"),
    interval: str = Query("1d", description="1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo")
):
    """Get historical data for a symbol"""
    data = get_historical_data(symbol.upper(), period, interval)
    if not data:
        raise HTTPException(status_code=404, detail=f"History not found for {symbol}")
    return data

@api_router.get("/market/search")
async def search_assets(q: str = Query(..., min_length=1)):
    """Search for assets by name or symbol"""
    # Mock search results - in production would use a proper search index
    results = []
    q_upper = q.upper()
    
    # Popular stocks
    stocks = [
        {"symbol": "AAPL", "name": "Apple Inc.", "type": "stock"},
        {"symbol": "MSFT", "name": "Microsoft Corporation", "type": "stock"},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "type": "stock"},
        {"symbol": "AMZN", "name": "Amazon.com Inc.", "type": "stock"},
        {"symbol": "META", "name": "Meta Platforms Inc.", "type": "stock"},
        {"symbol": "TSLA", "name": "Tesla Inc.", "type": "stock"},
        {"symbol": "NVDA", "name": "NVIDIA Corporation", "type": "stock"},
        {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "type": "stock"},
        {"symbol": "V", "name": "Visa Inc.", "type": "stock"},
        {"symbol": "JNJ", "name": "Johnson & Johnson", "type": "stock"},
    ]
    
    # Commodities
    commodities = [
        {"symbol": "GC=F", "name": "Gold Futures", "type": "commodity"},
        {"symbol": "SI=F", "name": "Silver Futures", "type": "commodity"},
        {"symbol": "CL=F", "name": "Crude Oil Futures", "type": "commodity"},
        {"symbol": "NG=F", "name": "Natural Gas Futures", "type": "commodity"},
        {"symbol": "HG=F", "name": "Copper Futures", "type": "commodity"},
        {"symbol": "ZC=F", "name": "Corn Futures", "type": "commodity"},
        {"symbol": "ZW=F", "name": "Wheat Futures", "type": "commodity"},
    ]
    
    # Forex
    forex = [
        {"symbol": "EURUSD=X", "name": "EUR/USD", "type": "forex"},
        {"symbol": "GBPUSD=X", "name": "GBP/USD", "type": "forex"},
        {"symbol": "USDJPY=X", "name": "USD/JPY", "type": "forex"},
        {"symbol": "AUDUSD=X", "name": "AUD/USD", "type": "forex"},
        {"symbol": "USDCAD=X", "name": "USD/CAD", "type": "forex"},
        {"symbol": "USDCHF=X", "name": "USD/CHF", "type": "forex"},
    ]
    
    all_assets = stocks + commodities + forex
    
    for asset in all_assets:
        if q_upper in asset["symbol"] or q.lower() in asset["name"].lower():
            results.append(asset)
    
    return {"results": results[:10]}

@api_router.get("/market/movers")
async def get_movers():
    """Get market movers (top gainers and losers)"""
    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "JPM", "V", "JNJ"]
    quotes = []
    
    for symbol in symbols:
        quote = get_yahoo_quote(symbol)
        if quote:
            quotes.append(quote)
    
    # Sort by change percent
    quotes.sort(key=lambda x: x.change_percent, reverse=True)
    
    return {
        "gainers": [q.model_dump() for q in quotes[:5] if q.change_percent > 0],
        "losers": [q.model_dump() for q in reversed(quotes) if q.change_percent < 0][:5]
    }

# News Routes
@api_router.get("/news", response_model=List[NewsArticle])
async def get_news(
    q: Optional[str] = None,
    country: Optional[str] = None,
    category: Optional[str] = None,
    page_size: int = Query(20, ge=1, le=100)
):
    """Get news articles"""
    return await fetch_news(query=q, country=country, category=category, page_size=page_size)

@api_router.get("/news/breaking", response_model=List[NewsArticle])
async def get_breaking_news():
    """Get breaking/top headlines"""
    return await fetch_news(page_size=10)

# Conflicts/Geopolitical Routes
@api_router.get("/conflicts", response_model=List[ConflictEvent])
async def get_conflicts():
    """Get geopolitical conflicts and events"""
    return await fetch_conflicts()

@api_router.get("/conflicts/{conflict_id}")
async def get_conflict_detail(conflict_id: str):
    """Get detailed conflict information"""
    conflicts = await fetch_conflicts()
    for conflict in conflicts:
        if conflict.id == conflict_id:
            return conflict
    raise HTTPException(status_code=404, detail="Conflict not found")

# Supply Chain Routes
@api_router.get("/supplychain/{symbol}", response_model=List[SupplyChainNode])
async def get_company_supply_chain(symbol: str):
    """Get supply chain relationships for a company"""
    return get_supply_chain(symbol.upper())

# Watchlist Routes
@api_router.get("/watchlist", response_model=List[WatchlistItem])
async def get_watchlist():
    """Get user watchlist"""
    items = await db.watchlist.find({}, {"_id": 0}).to_list(100)
    return items

@api_router.post("/watchlist", response_model=WatchlistItem)
async def add_to_watchlist(item: WatchlistCreate):
    """Add item to watchlist"""
    watchlist_item = WatchlistItem(**item.model_dump())
    doc = watchlist_item.model_dump()
    doc['added_at'] = doc['added_at'].isoformat()
    await db.watchlist.insert_one(doc)
    return watchlist_item

@api_router.delete("/watchlist/{symbol}")
async def remove_from_watchlist(symbol: str):
    """Remove item from watchlist"""
    result = await db.watchlist.delete_one({"symbol": symbol.upper()})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found in watchlist")
    return {"message": "Removed from watchlist"}

# Screener Route
@api_router.get("/screener")
async def screen_assets(
    asset_type: str = Query("stock", description="stock, commodity, forex"),
    min_change: Optional[float] = None,
    max_change: Optional[float] = None,
    sector: Optional[str] = None
):
    """Screen assets based on criteria"""
    if asset_type == "stock":
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "JPM", "V", "JNJ", "WMT", "PG", "UNH", "HD", "MA"]
    elif asset_type == "commodity":
        symbols = ["GC=F", "SI=F", "CL=F", "NG=F", "HG=F", "ZC=F", "ZW=F"]
    else:
        symbols = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X", "USDCHF=X"]
    
    results = []
    for symbol in symbols:
        quote = get_yahoo_quote(symbol)
        if quote:
            if min_change is not None and quote.change_percent < min_change:
                continue
            if max_change is not None and quote.change_percent > max_change:
                continue
            results.append(quote)
    
    return {"results": [r.model_dump() for r in results]}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
