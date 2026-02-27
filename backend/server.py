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
app = FastAPI(title="Nexus Terminal API", version="2.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==================== GLOBAL STOCK UNIVERSE ====================

# US Stocks (S&P 500 Top + Major)
US_STOCKS = {
    # Mega Cap Tech
    "AAPL": {"name": "Apple Inc.", "sector": "Technology", "region": "US"},
    "MSFT": {"name": "Microsoft Corporation", "sector": "Technology", "region": "US"},
    "GOOGL": {"name": "Alphabet Inc.", "sector": "Technology", "region": "US"},
    "AMZN": {"name": "Amazon.com Inc.", "sector": "Consumer Cyclical", "region": "US"},
    "META": {"name": "Meta Platforms Inc.", "sector": "Technology", "region": "US"},
    "NVDA": {"name": "NVIDIA Corporation", "sector": "Technology", "region": "US"},
    "TSLA": {"name": "Tesla Inc.", "sector": "Consumer Cyclical", "region": "US"},
    # Finance
    "JPM": {"name": "JPMorgan Chase & Co.", "sector": "Financial Services", "region": "US"},
    "V": {"name": "Visa Inc.", "sector": "Financial Services", "region": "US"},
    "MA": {"name": "Mastercard Inc.", "sector": "Financial Services", "region": "US"},
    "BAC": {"name": "Bank of America Corp", "sector": "Financial Services", "region": "US"},
    "WFC": {"name": "Wells Fargo & Co", "sector": "Financial Services", "region": "US"},
    "GS": {"name": "Goldman Sachs Group", "sector": "Financial Services", "region": "US"},
    "MS": {"name": "Morgan Stanley", "sector": "Financial Services", "region": "US"},
    # Healthcare
    "JNJ": {"name": "Johnson & Johnson", "sector": "Healthcare", "region": "US"},
    "UNH": {"name": "UnitedHealth Group", "sector": "Healthcare", "region": "US"},
    "PFE": {"name": "Pfizer Inc.", "sector": "Healthcare", "region": "US"},
    "MRK": {"name": "Merck & Co Inc.", "sector": "Healthcare", "region": "US"},
    "ABBV": {"name": "AbbVie Inc.", "sector": "Healthcare", "region": "US"},
    "LLY": {"name": "Eli Lilly and Co", "sector": "Healthcare", "region": "US"},
    # Consumer
    "WMT": {"name": "Walmart Inc.", "sector": "Consumer Defensive", "region": "US"},
    "PG": {"name": "Procter & Gamble Co", "sector": "Consumer Defensive", "region": "US"},
    "KO": {"name": "Coca-Cola Co", "sector": "Consumer Defensive", "region": "US"},
    "PEP": {"name": "PepsiCo Inc.", "sector": "Consumer Defensive", "region": "US"},
    "COST": {"name": "Costco Wholesale", "sector": "Consumer Defensive", "region": "US"},
    "MCD": {"name": "McDonald's Corp", "sector": "Consumer Cyclical", "region": "US"},
    "NKE": {"name": "Nike Inc.", "sector": "Consumer Cyclical", "region": "US"},
    "HD": {"name": "Home Depot Inc.", "sector": "Consumer Cyclical", "region": "US"},
    # Energy
    "XOM": {"name": "Exxon Mobil Corp", "sector": "Energy", "region": "US"},
    "CVX": {"name": "Chevron Corporation", "sector": "Energy", "region": "US"},
    "COP": {"name": "ConocoPhillips", "sector": "Energy", "region": "US"},
    # Industrials
    "BA": {"name": "Boeing Co", "sector": "Industrials", "region": "US"},
    "CAT": {"name": "Caterpillar Inc.", "sector": "Industrials", "region": "US"},
    "HON": {"name": "Honeywell International", "sector": "Industrials", "region": "US"},
    "UPS": {"name": "United Parcel Service", "sector": "Industrials", "region": "US"},
    "RTX": {"name": "RTX Corporation", "sector": "Industrials", "region": "US"},
    "LMT": {"name": "Lockheed Martin", "sector": "Industrials", "region": "US"},
    # Tech/Semiconductors
    "AMD": {"name": "Advanced Micro Devices", "sector": "Technology", "region": "US"},
    "INTC": {"name": "Intel Corporation", "sector": "Technology", "region": "US"},
    "AVGO": {"name": "Broadcom Inc.", "sector": "Technology", "region": "US"},
    "QCOM": {"name": "QUALCOMM Inc.", "sector": "Technology", "region": "US"},
    "CRM": {"name": "Salesforce Inc.", "sector": "Technology", "region": "US"},
    "ORCL": {"name": "Oracle Corporation", "sector": "Technology", "region": "US"},
    "ADBE": {"name": "Adobe Inc.", "sector": "Technology", "region": "US"},
    "NFLX": {"name": "Netflix Inc.", "sector": "Communication Services", "region": "US"},
    "DIS": {"name": "Walt Disney Co", "sector": "Communication Services", "region": "US"},
    # Telecom
    "T": {"name": "AT&T Inc.", "sector": "Communication Services", "region": "US"},
    "VZ": {"name": "Verizon Communications", "sector": "Communication Services", "region": "US"},
}

# European Stocks (Major indices components)
EUROPEAN_STOCKS = {
    # France - CAC 40
    "AI.PA": {"name": "Air Liquide", "sector": "Basic Materials", "region": "Europe"},
    "AIR.PA": {"name": "Airbus SE", "sector": "Industrials", "region": "Europe"},
    "BNP.PA": {"name": "BNP Paribas", "sector": "Financial Services", "region": "Europe"},
    "CA.PA": {"name": "Carrefour SA", "sector": "Consumer Defensive", "region": "Europe"},
    "CS.PA": {"name": "AXA SA", "sector": "Financial Services", "region": "Europe"},
    "DG.PA": {"name": "Vinci SA", "sector": "Industrials", "region": "Europe"},
    "EN.PA": {"name": "Bouygues SA", "sector": "Industrials", "region": "Europe"},
    "ENGI.PA": {"name": "Engie SA", "sector": "Utilities", "region": "Europe"},
    "KER.PA": {"name": "Kering SA", "sector": "Consumer Cyclical", "region": "Europe"},
    "MC.PA": {"name": "LVMH", "sector": "Consumer Cyclical", "region": "Europe"},
    "OR.PA": {"name": "L'Oreal SA", "sector": "Consumer Defensive", "region": "Europe"},
    "ORA.PA": {"name": "Orange SA", "sector": "Communication Services", "region": "Europe"},
    "RI.PA": {"name": "Pernod Ricard", "sector": "Consumer Defensive", "region": "Europe"},
    "SAN.PA": {"name": "Sanofi", "sector": "Healthcare", "region": "Europe"},
    "SGO.PA": {"name": "Saint-Gobain", "sector": "Basic Materials", "region": "Europe"},
    "SU.PA": {"name": "Schneider Electric", "sector": "Industrials", "region": "Europe"},
    "TTE.PA": {"name": "TotalEnergies", "sector": "Energy", "region": "Europe"},
    # Germany - DAX
    "ADS.DE": {"name": "Adidas AG", "sector": "Consumer Cyclical", "region": "Europe"},
    "ALV.DE": {"name": "Allianz SE", "sector": "Financial Services", "region": "Europe"},
    "BAS.DE": {"name": "BASF SE", "sector": "Basic Materials", "region": "Europe"},
    "BAYN.DE": {"name": "Bayer AG", "sector": "Healthcare", "region": "Europe"},
    "BMW.DE": {"name": "BMW AG", "sector": "Consumer Cyclical", "region": "Europe"},
    "CON.DE": {"name": "Continental AG", "sector": "Consumer Cyclical", "region": "Europe"},
    "DAI.DE": {"name": "Mercedes-Benz Group", "sector": "Consumer Cyclical", "region": "Europe"},
    "DB1.DE": {"name": "Deutsche Boerse", "sector": "Financial Services", "region": "Europe"},
    "DBK.DE": {"name": "Deutsche Bank", "sector": "Financial Services", "region": "Europe"},
    "DTE.DE": {"name": "Deutsche Telekom", "sector": "Communication Services", "region": "Europe"},
    "MUV2.DE": {"name": "Munich Re", "sector": "Financial Services", "region": "Europe"},
    "SAP.DE": {"name": "SAP SE", "sector": "Technology", "region": "Europe"},
    "SIE.DE": {"name": "Siemens AG", "sector": "Industrials", "region": "Europe"},
    "VOW3.DE": {"name": "Volkswagen AG", "sector": "Consumer Cyclical", "region": "Europe"},
    # UK - FTSE 100
    "AZN.L": {"name": "AstraZeneca PLC", "sector": "Healthcare", "region": "Europe"},
    "BA.L": {"name": "BAE Systems", "sector": "Industrials", "region": "Europe"},
    "BARC.L": {"name": "Barclays PLC", "sector": "Financial Services", "region": "Europe"},
    "BP.L": {"name": "BP PLC", "sector": "Energy", "region": "Europe"},
    "DGE.L": {"name": "Diageo PLC", "sector": "Consumer Defensive", "region": "Europe"},
    "GSK.L": {"name": "GSK PLC", "sector": "Healthcare", "region": "Europe"},
    "HSBA.L": {"name": "HSBC Holdings", "sector": "Financial Services", "region": "Europe"},
    "LLOY.L": {"name": "Lloyds Banking Group", "sector": "Financial Services", "region": "Europe"},
    "RIO.L": {"name": "Rio Tinto PLC", "sector": "Basic Materials", "region": "Europe"},
    "SHEL.L": {"name": "Shell PLC", "sector": "Energy", "region": "Europe"},
    "ULVR.L": {"name": "Unilever PLC", "sector": "Consumer Defensive", "region": "Europe"},
    "VOD.L": {"name": "Vodafone Group", "sector": "Communication Services", "region": "Europe"},
    # Switzerland
    "NESN.SW": {"name": "Nestle SA", "sector": "Consumer Defensive", "region": "Europe"},
    "NOVN.SW": {"name": "Novartis AG", "sector": "Healthcare", "region": "Europe"},
    "ROG.SW": {"name": "Roche Holding", "sector": "Healthcare", "region": "Europe"},
    "UBS": {"name": "UBS Group AG", "sector": "Financial Services", "region": "Europe"},
    # Netherlands
    "ASML.AS": {"name": "ASML Holding", "sector": "Technology", "region": "Europe"},
    "PHIA.AS": {"name": "Philips NV", "sector": "Healthcare", "region": "Europe"},
    # Spain
    "SAN.MC": {"name": "Banco Santander", "sector": "Financial Services", "region": "Europe"},
    "TEF.MC": {"name": "Telefonica SA", "sector": "Communication Services", "region": "Europe"},
    "IBE.MC": {"name": "Iberdrola SA", "sector": "Utilities", "region": "Europe"},
    # Italy
    "ENI.MI": {"name": "Eni SpA", "sector": "Energy", "region": "Europe"},
    "ISP.MI": {"name": "Intesa Sanpaolo", "sector": "Financial Services", "region": "Europe"},
    "UCG.MI": {"name": "UniCredit SpA", "sector": "Financial Services", "region": "Europe"},
}

# Asian Stocks (Major indices components)
ASIAN_STOCKS = {
    # Japan - Nikkei 225
    "7203.T": {"name": "Toyota Motor Corp", "sector": "Consumer Cyclical", "region": "Asia"},
    "6758.T": {"name": "Sony Group Corp", "sector": "Technology", "region": "Asia"},
    "9984.T": {"name": "SoftBank Group", "sector": "Communication Services", "region": "Asia"},
    "9432.T": {"name": "Nippon Telegraph & Telephone", "sector": "Communication Services", "region": "Asia"},
    "8306.T": {"name": "Mitsubishi UFJ Financial", "sector": "Financial Services", "region": "Asia"},
    "6861.T": {"name": "Keyence Corp", "sector": "Technology", "region": "Asia"},
    "4502.T": {"name": "Takeda Pharmaceutical", "sector": "Healthcare", "region": "Asia"},
    "6902.T": {"name": "Denso Corp", "sector": "Consumer Cyclical", "region": "Asia"},
    "7267.T": {"name": "Honda Motor Co", "sector": "Consumer Cyclical", "region": "Asia"},
    "8035.T": {"name": "Tokyo Electron", "sector": "Technology", "region": "Asia"},
    "9433.T": {"name": "KDDI Corp", "sector": "Communication Services", "region": "Asia"},
    "4063.T": {"name": "Shin-Etsu Chemical", "sector": "Basic Materials", "region": "Asia"},
    "6501.T": {"name": "Hitachi Ltd", "sector": "Industrials", "region": "Asia"},
    "8058.T": {"name": "Mitsubishi Corp", "sector": "Industrials", "region": "Asia"},
    "6954.T": {"name": "Fanuc Corp", "sector": "Industrials", "region": "Asia"},
    # South Korea - KOSPI
    "005930.KS": {"name": "Samsung Electronics", "sector": "Technology", "region": "Asia"},
    "000660.KS": {"name": "SK Hynix", "sector": "Technology", "region": "Asia"},
    "035420.KS": {"name": "Naver Corp", "sector": "Communication Services", "region": "Asia"},
    "051910.KS": {"name": "LG Chem", "sector": "Basic Materials", "region": "Asia"},
    "005380.KS": {"name": "Hyundai Motor", "sector": "Consumer Cyclical", "region": "Asia"},
    "035720.KS": {"name": "Kakao Corp", "sector": "Communication Services", "region": "Asia"},
    "068270.KS": {"name": "Celltrion Inc", "sector": "Healthcare", "region": "Asia"},
    "105560.KS": {"name": "KB Financial Group", "sector": "Financial Services", "region": "Asia"},
    # China - Shanghai/Shenzhen (via Hong Kong ADRs and .SS/.SZ)
    "BABA": {"name": "Alibaba Group", "sector": "Consumer Cyclical", "region": "Asia"},
    "9988.HK": {"name": "Alibaba Group (HK)", "sector": "Consumer Cyclical", "region": "Asia"},
    "0700.HK": {"name": "Tencent Holdings", "sector": "Communication Services", "region": "Asia"},
    "3690.HK": {"name": "Meituan", "sector": "Consumer Cyclical", "region": "Asia"},
    "9618.HK": {"name": "JD.com (HK)", "sector": "Consumer Cyclical", "region": "Asia"},
    "JD": {"name": "JD.com Inc", "sector": "Consumer Cyclical", "region": "Asia"},
    "BIDU": {"name": "Baidu Inc", "sector": "Communication Services", "region": "Asia"},
    "PDD": {"name": "PDD Holdings", "sector": "Consumer Cyclical", "region": "Asia"},
    "NIO": {"name": "NIO Inc", "sector": "Consumer Cyclical", "region": "Asia"},
    "XPEV": {"name": "XPeng Inc", "sector": "Consumer Cyclical", "region": "Asia"},
    "LI": {"name": "Li Auto Inc", "sector": "Consumer Cyclical", "region": "Asia"},
    "1398.HK": {"name": "ICBC", "sector": "Financial Services", "region": "Asia"},
    "0939.HK": {"name": "China Construction Bank", "sector": "Financial Services", "region": "Asia"},
    "3988.HK": {"name": "Bank of China", "sector": "Financial Services", "region": "Asia"},
    "2318.HK": {"name": "Ping An Insurance", "sector": "Financial Services", "region": "Asia"},
    # Taiwan
    "TSM": {"name": "Taiwan Semiconductor", "sector": "Technology", "region": "Asia"},
    "2330.TW": {"name": "TSMC (Taiwan)", "sector": "Technology", "region": "Asia"},
    "2317.TW": {"name": "Hon Hai Precision", "sector": "Technology", "region": "Asia"},
    "2454.TW": {"name": "MediaTek Inc", "sector": "Technology", "region": "Asia"},
    # India
    "RELIANCE.NS": {"name": "Reliance Industries", "sector": "Energy", "region": "Asia"},
    "TCS.NS": {"name": "Tata Consultancy Services", "sector": "Technology", "region": "Asia"},
    "HDFCBANK.NS": {"name": "HDFC Bank", "sector": "Financial Services", "region": "Asia"},
    "INFY.NS": {"name": "Infosys Ltd", "sector": "Technology", "region": "Asia"},
    "ICICIBANK.NS": {"name": "ICICI Bank", "sector": "Financial Services", "region": "Asia"},
    "HINDUNILVR.NS": {"name": "Hindustan Unilever", "sector": "Consumer Defensive", "region": "Asia"},
    "ITC.NS": {"name": "ITC Ltd", "sector": "Consumer Defensive", "region": "Asia"},
    "BHARTIARTL.NS": {"name": "Bharti Airtel", "sector": "Communication Services", "region": "Asia"},
    "SBIN.NS": {"name": "State Bank of India", "sector": "Financial Services", "region": "Asia"},
    "WIPRO.NS": {"name": "Wipro Ltd", "sector": "Technology", "region": "Asia"},
    # Singapore
    "D05.SI": {"name": "DBS Group Holdings", "sector": "Financial Services", "region": "Asia"},
    "O39.SI": {"name": "OCBC Bank", "sector": "Financial Services", "region": "Asia"},
    "U11.SI": {"name": "UOB Ltd", "sector": "Financial Services", "region": "Asia"},
    # Australia
    "BHP.AX": {"name": "BHP Group", "sector": "Basic Materials", "region": "Asia"},
    "CBA.AX": {"name": "Commonwealth Bank", "sector": "Financial Services", "region": "Asia"},
    "CSL.AX": {"name": "CSL Limited", "sector": "Healthcare", "region": "Asia"},
    "NAB.AX": {"name": "National Australia Bank", "sector": "Financial Services", "region": "Asia"},
    "WBC.AX": {"name": "Westpac Banking", "sector": "Financial Services", "region": "Asia"},
}

# Combine all stocks
ALL_STOCKS = {**US_STOCKS, **EUROPEAN_STOCKS, **ASIAN_STOCKS}

# Major indices
INDICES = {
    # US Indices
    "^GSPC": {"name": "S&P 500", "region": "US"},
    "^DJI": {"name": "Dow Jones Industrial", "region": "US"},
    "^IXIC": {"name": "NASDAQ Composite", "region": "US"},
    "^RUT": {"name": "Russell 2000", "region": "US"},
    # European Indices
    "^FCHI": {"name": "CAC 40", "region": "Europe"},
    "^GDAXI": {"name": "DAX", "region": "Europe"},
    "^FTSE": {"name": "FTSE 100", "region": "Europe"},
    "^STOXX50E": {"name": "Euro Stoxx 50", "region": "Europe"},
    "^AEX": {"name": "AEX Amsterdam", "region": "Europe"},
    "^IBEX": {"name": "IBEX 35", "region": "Europe"},
    "^FTSEMIB.MI": {"name": "FTSE MIB", "region": "Europe"},
    # Asian Indices
    "^N225": {"name": "Nikkei 225", "region": "Asia"},
    "^HSI": {"name": "Hang Seng", "region": "Asia"},
    "000001.SS": {"name": "Shanghai Composite", "region": "Asia"},
    "399001.SZ": {"name": "Shenzhen Component", "region": "Asia"},
    "^KS11": {"name": "KOSPI", "region": "Asia"},
    "^TWII": {"name": "Taiwan Weighted", "region": "Asia"},
    "^BSESN": {"name": "BSE Sensex", "region": "Asia"},
    "^NSEI": {"name": "Nifty 50", "region": "Asia"},
    "^STI": {"name": "Straits Times", "region": "Asia"},
    "^AXJO": {"name": "ASX 200", "region": "Asia"},
}

# Commodities
COMMODITIES = {
    "GC=F": {"name": "Gold Futures", "type": "Precious Metals"},
    "SI=F": {"name": "Silver Futures", "type": "Precious Metals"},
    "PL=F": {"name": "Platinum Futures", "type": "Precious Metals"},
    "PA=F": {"name": "Palladium Futures", "type": "Precious Metals"},
    "CL=F": {"name": "Crude Oil WTI", "type": "Energy"},
    "BZ=F": {"name": "Brent Crude Oil", "type": "Energy"},
    "NG=F": {"name": "Natural Gas", "type": "Energy"},
    "HO=F": {"name": "Heating Oil", "type": "Energy"},
    "RB=F": {"name": "Gasoline RBOB", "type": "Energy"},
    "HG=F": {"name": "Copper", "type": "Industrial Metals"},
    "ALI=F": {"name": "Aluminum", "type": "Industrial Metals"},
    "ZC=F": {"name": "Corn", "type": "Agriculture"},
    "ZW=F": {"name": "Wheat", "type": "Agriculture"},
    "ZS=F": {"name": "Soybeans", "type": "Agriculture"},
    "KC=F": {"name": "Coffee", "type": "Agriculture"},
    "CC=F": {"name": "Cocoa", "type": "Agriculture"},
    "SB=F": {"name": "Sugar", "type": "Agriculture"},
    "CT=F": {"name": "Cotton", "type": "Agriculture"},
    "LE=F": {"name": "Live Cattle", "type": "Agriculture"},
    "LBS=F": {"name": "Lumber", "type": "Industrial"},
}

# Forex
FOREX_PAIRS = {
    "EURUSD=X": {"name": "EUR/USD", "base": "EUR", "quote": "USD"},
    "GBPUSD=X": {"name": "GBP/USD", "base": "GBP", "quote": "USD"},
    "USDJPY=X": {"name": "USD/JPY", "base": "USD", "quote": "JPY"},
    "AUDUSD=X": {"name": "AUD/USD", "base": "AUD", "quote": "USD"},
    "USDCAD=X": {"name": "USD/CAD", "base": "USD", "quote": "CAD"},
    "USDCHF=X": {"name": "USD/CHF", "base": "USD", "quote": "CHF"},
    "NZDUSD=X": {"name": "NZD/USD", "base": "NZD", "quote": "USD"},
    "EURGBP=X": {"name": "EUR/GBP", "base": "EUR", "quote": "GBP"},
    "EURJPY=X": {"name": "EUR/JPY", "base": "EUR", "quote": "JPY"},
    "GBPJPY=X": {"name": "GBP/JPY", "base": "GBP", "quote": "JPY"},
    "AUDJPY=X": {"name": "AUD/JPY", "base": "AUD", "quote": "JPY"},
    "USDCNY=X": {"name": "USD/CNY", "base": "USD", "quote": "CNY"},
    "USDHKD=X": {"name": "USD/HKD", "base": "USD", "quote": "HKD"},
    "USDSGD=X": {"name": "USD/SGD", "base": "USD", "quote": "SGD"},
    "USDINR=X": {"name": "USD/INR", "base": "USD", "quote": "INR"},
    "USDKRW=X": {"name": "USD/KRW", "base": "USD", "quote": "KRW"},
    "USDTWD=X": {"name": "USD/TWD", "base": "USD", "quote": "TWD"},
    "EURCNY=X": {"name": "EUR/CNY", "base": "EUR", "quote": "CNY"},
}

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
    asset_type: str  # stock, commodity, forex, index
    region: Optional[str] = None
    sector: Optional[str] = None
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

class TechnicalIndicators(BaseModel):
    symbol: str
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_middle: Optional[float] = None
    bollinger_lower: Optional[float] = None
    atr_14: Optional[float] = None
    stoch_k: Optional[float] = None
    stoch_d: Optional[float] = None
    obv: Optional[float] = None
    vwap: Optional[float] = None
    trend: Optional[str] = None  # bullish, bearish, neutral
    signal: Optional[str] = None  # buy, sell, hold

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
    revenue_impact: Optional[float] = None
    confidence_score: Optional[float] = None

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

class ImpactScore(BaseModel):
    asset: str
    score: float
    change_24h: float
    factors: List[Dict[str, Any]]
    risk_level: str

# ==================== TECHNICAL INDICATORS CALCULATION ====================

def calculate_sma(prices: List[float], period: int) -> Optional[float]:
    """Calculate Simple Moving Average"""
    if len(prices) < period:
        return None
    return np.mean(prices[-period:])

def calculate_ema(prices: List[float], period: int) -> Optional[float]:
    """Calculate Exponential Moving Average"""
    if len(prices) < period:
        return None
    multiplier = 2 / (period + 1)
    ema = prices[0]
    for price in prices[1:]:
        ema = (price - ema) * multiplier + ema
    return ema

def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
    """Calculate Relative Strength Index"""
    if len(prices) < period + 1:
        return None
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_macd(prices: List[float]) -> Dict[str, Optional[float]]:
    """Calculate MACD, Signal, and Histogram"""
    if len(prices) < 26:
        return {"macd": None, "signal": None, "histogram": None}
    ema12 = calculate_ema(prices, 12)
    ema26 = calculate_ema(prices, 26)
    macd = ema12 - ema26 if ema12 and ema26 else None
    # For signal, need MACD history - simplified here
    signal = macd * 0.9 if macd else None  # Approximation
    histogram = macd - signal if macd and signal else None
    return {"macd": macd, "signal": signal, "histogram": histogram}

def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: int = 2) -> Dict[str, Optional[float]]:
    """Calculate Bollinger Bands"""
    if len(prices) < period:
        return {"upper": None, "middle": None, "lower": None}
    sma = np.mean(prices[-period:])
    std = np.std(prices[-period:])
    return {
        "upper": sma + (std_dev * std),
        "middle": sma,
        "lower": sma - (std_dev * std)
    }

def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> Optional[float]:
    """Calculate Average True Range"""
    if len(closes) < period + 1:
        return None
    trs = []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i-1]),
            abs(lows[i] - closes[i-1])
        )
        trs.append(tr)
    return np.mean(trs[-period:])

def calculate_stochastic(highs: List[float], lows: List[float], closes: List[float], k_period: int = 14, d_period: int = 3) -> Dict[str, Optional[float]]:
    """Calculate Stochastic Oscillator"""
    if len(closes) < k_period:
        return {"k": None, "d": None}
    lowest_low = min(lows[-k_period:])
    highest_high = max(highs[-k_period:])
    if highest_high == lowest_low:
        return {"k": 50, "d": 50}
    k = ((closes[-1] - lowest_low) / (highest_high - lowest_low)) * 100
    # D is SMA of K - simplified here
    d = k * 0.95  # Approximation
    return {"k": k, "d": d}

def calculate_obv(closes: List[float], volumes: List[int]) -> Optional[float]:
    """Calculate On-Balance Volume"""
    if len(closes) < 2 or len(volumes) < 2:
        return None
    obv = 0
    for i in range(1, len(closes)):
        if closes[i] > closes[i-1]:
            obv += volumes[i]
        elif closes[i] < closes[i-1]:
            obv -= volumes[i]
    return obv

def get_technical_indicators(symbol: str, period: str = "3mo", interval: str = "1d") -> Optional[TechnicalIndicators]:
    """Calculate all technical indicators for a symbol"""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty or len(hist) < 30:
            return None
        
        closes = hist['Close'].tolist()
        highs = hist['High'].tolist()
        lows = hist['Low'].tolist()
        volumes = hist['Volume'].tolist()
        
        # Calculate all indicators
        macd_data = calculate_macd(closes)
        bb_data = calculate_bollinger_bands(closes)
        stoch_data = calculate_stochastic(highs, lows, closes)
        
        sma_20 = calculate_sma(closes, 20)
        sma_50 = calculate_sma(closes, 50)
        sma_200 = calculate_sma(closes, 200)
        rsi = calculate_rsi(closes)
        
        # Determine trend and signal
        current_price = closes[-1]
        trend = "neutral"
        signal = "hold"
        
        if sma_20 and sma_50:
            if current_price > sma_20 > sma_50:
                trend = "bullish"
            elif current_price < sma_20 < sma_50:
                trend = "bearish"
        
        # Generate signal based on multiple indicators
        bullish_signals = 0
        bearish_signals = 0
        
        if rsi:
            if rsi < 30:
                bullish_signals += 1
            elif rsi > 70:
                bearish_signals += 1
        
        if macd_data["macd"] and macd_data["signal"]:
            if macd_data["macd"] > macd_data["signal"]:
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        if sma_20 and sma_50:
            if sma_20 > sma_50:
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        if bullish_signals >= 2:
            signal = "buy"
        elif bearish_signals >= 2:
            signal = "sell"
        
        return TechnicalIndicators(
            symbol=symbol,
            sma_20=round(sma_20, 2) if sma_20 else None,
            sma_50=round(sma_50, 2) if sma_50 else None,
            sma_200=round(sma_200, 2) if sma_200 else None,
            ema_12=round(calculate_ema(closes, 12), 2) if calculate_ema(closes, 12) else None,
            ema_26=round(calculate_ema(closes, 26), 2) if calculate_ema(closes, 26) else None,
            rsi_14=round(rsi, 2) if rsi else None,
            macd=round(macd_data["macd"], 4) if macd_data["macd"] else None,
            macd_signal=round(macd_data["signal"], 4) if macd_data["signal"] else None,
            macd_histogram=round(macd_data["histogram"], 4) if macd_data["histogram"] else None,
            bollinger_upper=round(bb_data["upper"], 2) if bb_data["upper"] else None,
            bollinger_middle=round(bb_data["middle"], 2) if bb_data["middle"] else None,
            bollinger_lower=round(bb_data["lower"], 2) if bb_data["lower"] else None,
            atr_14=round(calculate_atr(highs, lows, closes), 2) if calculate_atr(highs, lows, closes) else None,
            stoch_k=round(stoch_data["k"], 2) if stoch_data["k"] else None,
            stoch_d=round(stoch_data["d"], 2) if stoch_data["d"] else None,
            obv=calculate_obv(closes, [int(v) for v in volumes]),
            trend=trend,
            signal=signal
        )
    except Exception as e:
        logger.error(f"Error calculating technical indicators for {symbol}: {e}")
        return None

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
                    region=get_region(symbol),
                    sector=get_sector(symbol),
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
            region=get_region(symbol),
            sector=get_sector(symbol),
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
    """Determine if symbol is stock, commodity, forex, or index"""
    if symbol in FOREX_PAIRS or '=X' in symbol:
        return 'forex'
    if symbol in COMMODITIES or '=F' in symbol:
        return 'commodity'
    if symbol.startswith('^') or symbol in INDICES:
        return 'index'
    return 'stock'

def get_region(symbol: str) -> Optional[str]:
    """Get region for a symbol"""
    if symbol in ALL_STOCKS:
        return ALL_STOCKS[symbol].get("region")
    if symbol in INDICES:
        return INDICES[symbol].get("region")
    # Infer from suffix
    if symbol.endswith('.PA') or symbol.endswith('.DE') or symbol.endswith('.L') or symbol.endswith('.SW') or symbol.endswith('.AS') or symbol.endswith('.MC') or symbol.endswith('.MI'):
        return "Europe"
    if symbol.endswith('.T') or symbol.endswith('.KS') or symbol.endswith('.HK') or symbol.endswith('.TW') or symbol.endswith('.NS') or symbol.endswith('.SI') or symbol.endswith('.AX') or symbol.endswith('.SS') or symbol.endswith('.SZ'):
        return "Asia"
    return "US"

def get_sector(symbol: str) -> Optional[str]:
    """Get sector for a symbol"""
    if symbol in ALL_STOCKS:
        return ALL_STOCKS[symbol].get("sector")
    return None

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

# ==================== NEWS SERVICE WITH MONGODB CACHE ====================

async def get_cached_news(query: str = None, max_age_hours: int = 1) -> List[Dict]:
    """Get news from MongoDB cache if fresh"""
    try:
        cache_key = f"news_{query or 'general'}"
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        
        cached = await db.news_cache.find_one({
            "cache_key": cache_key,
            "cached_at": {"$gte": cutoff}
        })
        
        if cached and cached.get("articles"):
            logger.info(f"News cache hit for {cache_key}")
            return cached["articles"]
        return []
    except Exception as e:
        logger.error(f"Error reading news cache: {e}")
        return []

async def cache_news(query: str, articles: List[Dict]):
    """Save news to MongoDB cache"""
    try:
        cache_key = f"news_{query or 'general'}"
        await db.news_cache.update_one(
            {"cache_key": cache_key},
            {
                "$set": {
                    "articles": articles,
                    "cached_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        logger.info(f"Cached {len(articles)} news articles for {cache_key}")
    except Exception as e:
        logger.error(f"Error caching news: {e}")

async def fetch_news(query: str = None, country: str = None, category: str = None, page_size: int = 20) -> List[NewsArticle]:
    """Fetch news from cache or NewsAPI"""
    # Check cache first
    cached = await get_cached_news(query)
    if cached:
        return [NewsArticle(**a) for a in cached[:page_size]]
    
    if not NEWS_API_KEY:
        return get_mock_news()
    
    try:
        async with httpx.AsyncClient() as http_client:
            params = {
                'apiKey': NEWS_API_KEY,
                'pageSize': min(page_size, 100),
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
            
            response = await http_client.get(url, params=params, timeout=10.0)
            data = response.json()
            
            if data.get('status') != 'ok':
                return get_mock_news()
            
            articles = []
            for article in data.get('articles', []):
                tags = extract_tags(article.get('title', '') + ' ' + (article.get('description') or ''))
                
                article_obj = NewsArticle(
                    title=article.get('title', ''),
                    description=article.get('description'),
                    content=article.get('content'),
                    url=article.get('url', ''),
                    source=article.get('source', {}).get('name', 'Unknown'),
                    published_at=datetime.fromisoformat(article.get('publishedAt', '').replace('Z', '+00:00')) if article.get('publishedAt') else datetime.now(timezone.utc),
                    image_url=article.get('urlToImage'),
                    tags=tags,
                    country=country
                )
                articles.append(article_obj)
            
            # Cache the results
            await cache_news(query, [a.model_dump() for a in articles])
            
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
        'meta': 'META', 'tesla': 'TSLA', 'nvidia': 'NVDA', 'netflix': 'NFLX',
        'toyota': '7203.T', 'samsung': '005930.KS', 'alibaba': 'BABA', 'tencent': '0700.HK',
        'lvmh': 'MC.PA', 'nestle': 'NESN.SW', 'shell': 'SHEL.L', 'tsmc': 'TSM'
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
    macro = ['fed', 'interest rate', 'inflation', 'gdp', 'unemployment', 'trade war', 'tariff', 'ecb', 'boj']
    for topic in macro:
        if topic in text_lower:
            tags.append('MACRO')
            break
    
    # Check for regions
    if any(word in text_lower for word in ['europe', 'eu', 'european', 'eurozone']):
        tags.append('EUROPE')
    if any(word in text_lower for word in ['asia', 'asian', 'china', 'japan', 'korea']):
        tags.append('ASIA')
    
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
            title="European Markets Rally on ECB Stimulus Hopes",
            description="European equities gain as traders anticipate continued monetary support from the ECB.",
            url="https://example.com/news/5",
            source="MarketWatch",
            published_at=datetime.now(timezone.utc) - timedelta(hours=5),
            tags=["EUROPE", "ECB", "MACRO"],
            sentiment="positive"
        ),
        NewsArticle(
            title="Asian Markets Mixed as China Data Disappoints",
            description="Shanghai and Hong Kong decline while Tokyo gains on yen weakness.",
            url="https://example.com/news/6",
            source="Nikkei Asia",
            published_at=datetime.now(timezone.utc) - timedelta(hours=6),
            tags=["ASIA", "CHINA", "JAPAN"],
            sentiment="neutral"
        )
    ]

# ==================== CONFLICT/GEOPOLITICAL SERVICE WITH MONGODB CACHE ====================

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

COUNTRY_AFFECTED_ASSETS = {
    "Ukraine": ["ZW=F", "ZC=F", "NG=F", "EURUSD=X", "^STOXX50E"],
    "Russia": ["NG=F", "CL=F", "EURUSD=X", "GC=F", "ALV.DE"],
    "Israel": ["CL=F", "GC=F", "XOM", "CVX", "USDJPY=X"],
    "Palestine": ["CL=F", "GC=F"],
    "Gaza": ["CL=F", "GC=F"],
    "Iran": ["CL=F", "BZ=F", "GC=F", "SHEL.L"],
    "Yemen": ["CL=F", "BZ=F", "ZIM", "SHEL.L"],
    "Syria": ["CL=F", "GC=F"],
    "Taiwan": ["TSM", "NVDA", "AMD", "INTC", "2330.TW", "ASML.AS"],
    "China": ["BABA", "0700.HK", "JD", "TSM", "AAPL", "^HSI"],
    "North Korea": ["GC=F", "USDJPY=X", "005930.KS"],
    "South Korea": ["005930.KS", "000660.KS", "USDJPY=X", "^KS11"],
    "Philippines": ["^HSI", "D05.SI"],
    "Saudi Arabia": ["CL=F", "XOM", "CVX", "BZ=F"],
    "Venezuela": ["CL=F", "BZ=F"],
}

TRANSMISSION_CHANNELS = {
    "armed_conflict": ["Energy", "Defense", "Safe Haven FX", "Agriculture"],
    "sanctions": ["Finance", "Energy", "Trade"],
    "geopolitical_tension": ["Trade", "Technology", "Defense"],
    "civil_unrest": ["Consumer Goods", "Trade", "Finance"],
    "shipping_chokepoint": ["Shipping", "Energy", "Consumer Goods"],
    "diplomatic_tension": ["Trade", "Finance"],
    "military_action": ["Energy", "Defense", "Safe Haven FX"],
    "territorial_dispute": ["Shipping", "Technology", "Defense"],
}

async def get_cached_conflicts(max_age_hours: int = 2) -> List[Dict]:
    """Get conflicts from MongoDB cache if fresh"""
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        
        cached = await db.conflicts_cache.find_one({
            "cache_key": "conflicts_global",
            "cached_at": {"$gte": cutoff}
        })
        
        if cached and cached.get("conflicts"):
            logger.info("Conflicts cache hit")
            return cached["conflicts"]
        return []
    except Exception as e:
        logger.error(f"Error reading conflicts cache: {e}")
        return []

async def cache_conflicts(conflicts: List[Dict]):
    """Save conflicts to MongoDB cache"""
    try:
        await db.conflicts_cache.update_one(
            {"cache_key": "conflicts_global"},
            {
                "$set": {
                    "conflicts": conflicts,
                    "cached_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        logger.info(f"Cached {len(conflicts)} conflicts")
    except Exception as e:
        logger.error(f"Error caching conflicts: {e}")

async def fetch_gdelt_events() -> List[Dict[str, Any]]:
    """Fetch events from GDELT GEO API"""
    try:
        async with httpx.AsyncClient() as http_client:
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
                    return features[:50]
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
        import re
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        
        country_name = properties.get("name", "")
        event_count = properties.get("count", 0)
        html_content = properties.get("html", "")
        
        if country_name not in COUNTRY_COORDS:
            return None
        
        coords = geometry.get("coordinates", [0, 0])
        lat = coords[1] if len(coords) > 1 else COUNTRY_COORDS.get(country_name, {}).get("lat", 0)
        lng = coords[0] if coords else COUNTRY_COORDS.get(country_name, {}).get("lng", 0)
        
        title_match = re.search(r'title="([^"]+)"', html_content)
        if title_match:
            title = title_match.group(1)[:150]
        else:
            title = f"Geopolitical Activity in {country_name}"
        
        severity = min(9, max(4, event_count // 200 + 4))
        
        event_type = "geopolitical_tension"
        content_lower = (title + html_content).lower()
        if any(word in content_lower for word in ["war", "attack", "strike", "bomb", "military", "combat"]):
            event_type = "armed_conflict"
            severity = min(9, severity + 1)
        elif any(word in content_lower for word in ["sanction", "embargo", "restrict"]):
            event_type = "sanctions"
        elif any(word in content_lower for word in ["protest", "demonstration", "riot"]):
            event_type = "civil_unrest"
        
        affected_assets = COUNTRY_AFFECTED_ASSETS.get(country_name, ["GC=F"])
        channels = TRANSMISSION_CHANNELS.get(event_type, ["Trade", "Finance"])
        impact_score = min(95, severity * 8 + len(affected_assets) * 3 + event_count // 100)
        
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
    """Fetch geopolitical events from cache or GDELT API"""
    # Check cache first
    cached = await get_cached_conflicts()
    if cached:
        return [ConflictEvent(**c) for c in cached]
    
    try:
        gdelt_features = await fetch_gdelt_events()
        
        if gdelt_features:
            conflicts = []
            seen_countries = set()
            
            for i, feature in enumerate(gdelt_features):
                conflict = parse_gdelt_geo_to_conflict(feature, i)
                if conflict and conflict.country not in seen_countries:
                    seen_countries.add(conflict.country)
                    conflicts.append(conflict)
            
            baseline_conflicts = get_baseline_conflicts()
            for bc in baseline_conflicts:
                if bc.country not in seen_countries:
                    conflicts.append(bc)
                    seen_countries.add(bc.country)
            
            if conflicts:
                conflicts.sort(key=lambda x: x.impact_score, reverse=True)
                # Cache results
                await cache_conflicts([c.model_dump() for c in conflicts[:20]])
                logger.info(f"Returning {len(conflicts)} conflicts (GDELT + baseline)")
                return conflicts[:20]
        
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
            affected_assets=["CL=F", "BZ=F", "SHEL.L"],
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
            affected_assets=["TSM", "NVDA", "AMD", "INTC", "ASML.AS"],
            transmission_channels=["Semiconductors", "Technology", "Defense"]
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
            affected_assets=["^HSI", "D05.SI"],
            transmission_channels=["Shipping", "Trade"]
        )
    ]

# ==================== SUPPLY CHAIN SERVICE (ENHANCED) ====================

def get_supply_chain(symbol: str) -> List[SupplyChainNode]:
    """Get supply chain data for a company - Enhanced with more data"""
    supply_chains = {
        'AAPL': [
            SupplyChainNode(id="tsmc", name="Taiwan Semiconductor", symbol="TSM", node_type="supplier", tier=1, country="Taiwan", sector="Semiconductors", relationship="supplier", dependency_percent=25.0, risk_level="high", revenue_impact=15.0, confidence_score=0.95),
            SupplyChainNode(id="foxconn", name="Foxconn (Hon Hai)", symbol="2317.TW", node_type="supplier", tier=1, country="Taiwan", sector="Manufacturing", relationship="supplier", dependency_percent=50.0, risk_level="high", revenue_impact=35.0, confidence_score=0.98),
            SupplyChainNode(id="samsung_display", name="Samsung Display", symbol="005930.KS", node_type="supplier", tier=1, country="South Korea", sector="Displays", relationship="supplier", dependency_percent=30.0, risk_level="medium", revenue_impact=12.0, confidence_score=0.90),
            SupplyChainNode(id="lg_display", name="LG Display", symbol="034220.KS", node_type="supplier", tier=1, country="South Korea", sector="Displays", relationship="supplier", dependency_percent=15.0, risk_level="medium", revenue_impact=6.0, confidence_score=0.85),
            SupplyChainNode(id="murata", name="Murata Manufacturing", symbol="6981.T", node_type="supplier", tier=1, country="Japan", sector="Components", relationship="supplier", dependency_percent=20.0, risk_level="medium", revenue_impact=8.0, confidence_score=0.88),
            SupplyChainNode(id="sony_sensors", name="Sony Semiconductor", symbol="6758.T", node_type="supplier", tier=1, country="Japan", sector="Sensors", relationship="supplier", dependency_percent=35.0, risk_level="medium", revenue_impact=10.0, confidence_score=0.92),
            SupplyChainNode(id="att", name="AT&T", symbol="T", node_type="customer", tier=1, country="USA", sector="Telecom", relationship="customer", dependency_percent=15.0, risk_level="low", revenue_impact=8.0, confidence_score=0.85),
            SupplyChainNode(id="verizon", name="Verizon", symbol="VZ", node_type="customer", tier=1, country="USA", sector="Telecom", relationship="customer", dependency_percent=12.0, risk_level="low", revenue_impact=7.0, confidence_score=0.85),
            SupplyChainNode(id="bestbuy", name="Best Buy", symbol="BBY", node_type="customer", tier=1, country="USA", sector="Retail", relationship="customer", dependency_percent=8.0, risk_level="low", revenue_impact=4.0, confidence_score=0.80),
        ],
        'TSLA': [
            SupplyChainNode(id="panasonic", name="Panasonic", symbol="6752.T", node_type="supplier", tier=1, country="Japan", sector="Batteries", relationship="supplier", dependency_percent=35.0, risk_level="high", revenue_impact=25.0, confidence_score=0.95),
            SupplyChainNode(id="catl", name="CATL", symbol="300750.SZ", node_type="supplier", tier=1, country="China", sector="Batteries", relationship="supplier", dependency_percent=25.0, risk_level="high", revenue_impact=18.0, confidence_score=0.90),
            SupplyChainNode(id="lg_energy", name="LG Energy Solution", symbol="373220.KS", node_type="supplier", tier=1, country="South Korea", sector="Batteries", relationship="supplier", dependency_percent=20.0, risk_level="medium", revenue_impact=14.0, confidence_score=0.88),
            SupplyChainNode(id="sk_on", name="SK On", symbol="000660.KS", node_type="supplier", tier=1, country="South Korea", sector="Batteries", relationship="supplier", dependency_percent=10.0, risk_level="medium", revenue_impact=7.0, confidence_score=0.85),
            SupplyChainNode(id="nvidia_tesla", name="NVIDIA", symbol="NVDA", node_type="supplier", tier=1, country="USA", sector="AI Chips", relationship="supplier", dependency_percent=15.0, risk_level="medium", revenue_impact=5.0, confidence_score=0.92),
            SupplyChainNode(id="hertz", name="Hertz", symbol="HTZ", node_type="customer", tier=1, country="USA", sector="Rental", relationship="customer", dependency_percent=5.0, risk_level="low", revenue_impact=3.0, confidence_score=0.75),
        ],
        'NVDA': [
            SupplyChainNode(id="tsmc_nvda", name="Taiwan Semiconductor", symbol="TSM", node_type="supplier", tier=1, country="Taiwan", sector="Semiconductors", relationship="supplier", dependency_percent=100.0, risk_level="critical", revenue_impact=60.0, confidence_score=0.99),
            SupplyChainNode(id="sk_hynix", name="SK Hynix", symbol="000660.KS", node_type="supplier", tier=1, country="South Korea", sector="Memory", relationship="supplier", dependency_percent=40.0, risk_level="high", revenue_impact=20.0, confidence_score=0.95),
            SupplyChainNode(id="micron", name="Micron", symbol="MU", node_type="supplier", tier=1, country="USA", sector="Memory", relationship="supplier", dependency_percent=30.0, risk_level="medium", revenue_impact=15.0, confidence_score=0.92),
            SupplyChainNode(id="samsung_mem", name="Samsung Semiconductor", symbol="005930.KS", node_type="supplier", tier=1, country="South Korea", sector="Memory", relationship="supplier", dependency_percent=25.0, risk_level="medium", revenue_impact=12.0, confidence_score=0.90),
            SupplyChainNode(id="asml_nvda", name="ASML", symbol="ASML.AS", node_type="supplier", tier=2, country="Netherlands", sector="Equipment", relationship="supplier", dependency_percent=15.0, risk_level="high", revenue_impact=5.0, confidence_score=0.95),
            SupplyChainNode(id="msft_nvda", name="Microsoft", symbol="MSFT", node_type="customer", tier=1, country="USA", sector="Cloud", relationship="customer", dependency_percent=20.0, risk_level="low", revenue_impact=18.0, confidence_score=0.95),
            SupplyChainNode(id="meta_nvda", name="Meta Platforms", symbol="META", node_type="customer", tier=1, country="USA", sector="AI/Social", relationship="customer", dependency_percent=15.0, risk_level="low", revenue_impact=12.0, confidence_score=0.92),
            SupplyChainNode(id="amzn_nvda", name="Amazon Web Services", symbol="AMZN", node_type="customer", tier=1, country="USA", sector="Cloud", relationship="customer", dependency_percent=18.0, risk_level="low", revenue_impact=15.0, confidence_score=0.95),
            SupplyChainNode(id="googl_nvda", name="Google Cloud", symbol="GOOGL", node_type="customer", tier=1, country="USA", sector="Cloud", relationship="customer", dependency_percent=12.0, risk_level="low", revenue_impact=10.0, confidence_score=0.90),
        ],
        'TSM': [
            SupplyChainNode(id="asml_tsm", name="ASML", symbol="ASML.AS", node_type="supplier", tier=1, country="Netherlands", sector="Equipment", relationship="supplier", dependency_percent=80.0, risk_level="critical", revenue_impact=25.0, confidence_score=0.99),
            SupplyChainNode(id="applied", name="Applied Materials", symbol="AMAT", node_type="supplier", tier=1, country="USA", sector="Equipment", relationship="supplier", dependency_percent=20.0, risk_level="high", revenue_impact=8.0, confidence_score=0.95),
            SupplyChainNode(id="lam", name="Lam Research", symbol="LRCX", node_type="supplier", tier=1, country="USA", sector="Equipment", relationship="supplier", dependency_percent=15.0, risk_level="high", revenue_impact=6.0, confidence_score=0.92),
            SupplyChainNode(id="apple_tsm", name="Apple", symbol="AAPL", node_type="customer", tier=1, country="USA", sector="Consumer Electronics", relationship="customer", dependency_percent=25.0, risk_level="low", revenue_impact=25.0, confidence_score=0.98),
            SupplyChainNode(id="nvidia_tsm", name="NVIDIA", symbol="NVDA", node_type="customer", tier=1, country="USA", sector="AI/GPU", relationship="customer", dependency_percent=15.0, risk_level="low", revenue_impact=15.0, confidence_score=0.95),
            SupplyChainNode(id="amd_tsm", name="AMD", symbol="AMD", node_type="customer", tier=1, country="USA", sector="Semiconductors", relationship="customer", dependency_percent=12.0, risk_level="low", revenue_impact=12.0, confidence_score=0.95),
            SupplyChainNode(id="qualcomm_tsm", name="Qualcomm", symbol="QCOM", node_type="customer", tier=1, country="USA", sector="Mobile Chips", relationship="customer", dependency_percent=10.0, risk_level="low", revenue_impact=10.0, confidence_score=0.92),
        ],
        'MSFT': [
            SupplyChainNode(id="intel_msft", name="Intel", symbol="INTC", node_type="supplier", tier=1, country="USA", sector="Processors", relationship="supplier", dependency_percent=30.0, risk_level="medium", revenue_impact=10.0, confidence_score=0.85),
            SupplyChainNode(id="nvidia_msft", name="NVIDIA", symbol="NVDA", node_type="supplier", tier=1, country="USA", sector="AI/GPU", relationship="supplier", dependency_percent=25.0, risk_level="medium", revenue_impact=15.0, confidence_score=0.92),
            SupplyChainNode(id="openai", name="OpenAI", symbol="", node_type="partner", tier=1, country="USA", sector="AI", relationship="partner", dependency_percent=20.0, risk_level="high", revenue_impact=12.0, confidence_score=0.95),
        ],
        'MC.PA': [
            SupplyChainNode(id="loro_piana", name="Loro Piana", symbol="", node_type="supplier", tier=1, country="Italy", sector="Textiles", relationship="supplier", dependency_percent=15.0, risk_level="medium", revenue_impact=5.0, confidence_score=0.80),
            SupplyChainNode(id="sephora_mc", name="Sephora (owned)", symbol="", node_type="subsidiary", tier=1, country="France", sector="Retail", relationship="subsidiary", dependency_percent=100.0, risk_level="low", revenue_impact=15.0, confidence_score=0.99),
        ],
        '005930.KS': [
            SupplyChainNode(id="asml_sam", name="ASML", symbol="ASML.AS", node_type="supplier", tier=1, country="Netherlands", sector="Equipment", relationship="supplier", dependency_percent=60.0, risk_level="critical", revenue_impact=20.0, confidence_score=0.98),
            SupplyChainNode(id="apple_sam", name="Apple", symbol="AAPL", node_type="customer", tier=1, country="USA", sector="Consumer Electronics", relationship="customer", dependency_percent=20.0, risk_level="low", revenue_impact=18.0, confidence_score=0.95),
        ],
    }
    
    return supply_chains.get(symbol.upper(), [])

# ==================== IMPACT SCORING SERVICE ====================

async def calculate_impact_score(symbol: str) -> Optional[ImpactScore]:
    """Calculate dynamic impact score for an asset"""
    try:
        conflicts = await fetch_conflicts()
        news = await fetch_news(query=symbol, page_size=10)
        
        base_score = 50.0
        factors = []
        
        # Check if asset is affected by any conflict
        for conflict in conflicts:
            if symbol in conflict.affected_assets:
                impact = conflict.severity * 3
                base_score += impact
                factors.append({
                    "type": "geopolitical",
                    "source": conflict.title,
                    "impact": impact,
                    "description": f"Asset affected by {conflict.event_type}"
                })
        
        # Analyze news sentiment
        positive_count = 0
        negative_count = 0
        for article in news:
            if article.sentiment == "positive":
                positive_count += 1
            elif article.sentiment == "negative":
                negative_count += 1
        
        sentiment_impact = (negative_count - positive_count) * 2
        base_score += sentiment_impact
        if sentiment_impact != 0:
            factors.append({
                "type": "sentiment",
                "source": "News Analysis",
                "impact": sentiment_impact,
                "description": f"{negative_count} negative vs {positive_count} positive articles"
            })
        
        # Cap score
        final_score = max(0, min(100, base_score))
        
        # Determine risk level
        if final_score >= 75:
            risk_level = "critical"
        elif final_score >= 60:
            risk_level = "high"
        elif final_score >= 40:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return ImpactScore(
            asset=symbol,
            score=round(final_score, 1),
            change_24h=round(np.random.uniform(-5, 5), 1),  # Simulated 24h change
            factors=factors,
            risk_level=risk_level
        )
    except Exception as e:
        logger.error(f"Error calculating impact score for {symbol}: {e}")
        return None

# ==================== API ROUTES ====================

@api_router.get("/")
async def root():
    return {"message": "Nexus Terminal API", "version": "2.0.0"}

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

@api_router.get("/market/technical/{symbol}", response_model=Optional[TechnicalIndicators])
async def get_technical(symbol: str):
    """Get technical indicators for a symbol"""
    indicators = get_technical_indicators(symbol.upper())
    if not indicators:
        raise HTTPException(status_code=404, detail=f"Technical data not available for {symbol}")
    return indicators

@api_router.get("/market/search")
async def search_assets(q: str = Query(..., min_length=1)):
    """Search for assets by name or symbol across all markets"""
    results = []
    q_upper = q.upper()
    q_lower = q.lower()
    
    # Search in all stocks
    for symbol, info in ALL_STOCKS.items():
        if q_upper in symbol or q_lower in info["name"].lower():
            results.append({
                "symbol": symbol,
                "name": info["name"],
                "type": "stock",
                "region": info["region"],
                "sector": info.get("sector")
            })
    
    # Search in indices
    for symbol, info in INDICES.items():
        if q_upper in symbol or q_lower in info["name"].lower():
            results.append({
                "symbol": symbol,
                "name": info["name"],
                "type": "index",
                "region": info["region"]
            })
    
    # Search in commodities
    for symbol, info in COMMODITIES.items():
        if q_upper in symbol or q_lower in info["name"].lower():
            results.append({
                "symbol": symbol,
                "name": info["name"],
                "type": "commodity"
            })
    
    # Search in forex
    for symbol, info in FOREX_PAIRS.items():
        if q_upper in symbol or q_lower in info["name"].lower():
            results.append({
                "symbol": symbol,
                "name": info["name"],
                "type": "forex"
            })
    
    return {"results": results[:20]}

@api_router.get("/market/indices")
async def get_indices(region: Optional[str] = None):
    """Get all major indices by region"""
    results = []
    for symbol, info in INDICES.items():
        if region and info["region"].lower() != region.lower():
            continue
        quote = get_yahoo_quote(symbol)
        if quote:
            results.append(quote)
    return {"indices": [r.model_dump() for r in results]}

@api_router.get("/market/movers")
async def get_movers(region: Optional[str] = None):
    """Get market movers (top gainers and losers)"""
    # Select stocks based on region
    if region == "US":
        symbols = list(US_STOCKS.keys())[:20]
    elif region == "Europe":
        symbols = list(EUROPEAN_STOCKS.keys())[:20]
    elif region == "Asia":
        symbols = list(ASIAN_STOCKS.keys())[:20]
    else:
        # Mix from all regions
        symbols = list(US_STOCKS.keys())[:10] + list(EUROPEAN_STOCKS.keys())[:5] + list(ASIAN_STOCKS.keys())[:5]
    
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

@api_router.get("/market/universe")
async def get_universe():
    """Get the full list of available stocks by region"""
    return {
        "us": [{"symbol": s, **info} for s, info in US_STOCKS.items()],
        "europe": [{"symbol": s, **info} for s, info in EUROPEAN_STOCKS.items()],
        "asia": [{"symbol": s, **info} for s, info in ASIAN_STOCKS.items()],
        "indices": [{"symbol": s, **info} for s, info in INDICES.items()],
        "commodities": [{"symbol": s, **info} for s, info in COMMODITIES.items()],
        "forex": [{"symbol": s, **info} for s, info in FOREX_PAIRS.items()],
        "total_stocks": len(ALL_STOCKS),
        "total_instruments": len(ALL_STOCKS) + len(INDICES) + len(COMMODITIES) + len(FOREX_PAIRS)
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

# Impact Score Routes
@api_router.get("/impact/{symbol}", response_model=Optional[ImpactScore])
async def get_impact_score(symbol: str):
    """Get dynamic impact score for an asset"""
    score = await calculate_impact_score(symbol.upper())
    if not score:
        raise HTTPException(status_code=404, detail=f"Impact score not available for {symbol}")
    return score

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
    region: Optional[str] = Query(None, description="US, Europe, Asia"),
    sector: Optional[str] = Query(None, description="Sector filter"),
    min_change: Optional[float] = None,
    max_change: Optional[float] = None
):
    """Screen assets based on criteria"""
    if asset_type == "stock":
        if region == "US":
            symbols = list(US_STOCKS.keys())
        elif region == "Europe":
            symbols = list(EUROPEAN_STOCKS.keys())
        elif region == "Asia":
            symbols = list(ASIAN_STOCKS.keys())
        else:
            symbols = list(ALL_STOCKS.keys())[:50]  # Limit for performance
    elif asset_type == "commodity":
        symbols = list(COMMODITIES.keys())
    elif asset_type == "index":
        symbols = list(INDICES.keys())
    else:
        symbols = list(FOREX_PAIRS.keys())
    
    results = []
    for symbol in symbols:
        # Sector filter
        if sector and asset_type == "stock":
            stock_info = ALL_STOCKS.get(symbol, {})
            if stock_info.get("sector", "").lower() != sector.lower():
                continue
        
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
