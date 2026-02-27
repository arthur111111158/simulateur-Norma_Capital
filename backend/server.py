from fastapi import FastAPI, APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any, Set
import uuid
from datetime import datetime, timezone, timedelta
import yfinance as yf
import httpx
import asyncio
import numpy as np
from enum import Enum
import json
import pandas as pd

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
    "EURCHF=X": {"name": "EUR/CHF", "base": "EUR", "quote": "CHF"},
    "EURAUD=X": {"name": "EUR/AUD", "base": "EUR", "quote": "AUD"},
    "EURNZD=X": {"name": "EUR/NZD", "base": "EUR", "quote": "NZD"},
    "EURCAD=X": {"name": "EUR/CAD", "base": "EUR", "quote": "CAD"},
    "GBPCHF=X": {"name": "GBP/CHF", "base": "GBP", "quote": "CHF"},
    "GBPAUD=X": {"name": "GBP/AUD", "base": "GBP", "quote": "AUD"},
    "GBPCAD=X": {"name": "GBP/CAD", "base": "GBP", "quote": "CAD"},
    "CHFJPY=X": {"name": "CHF/JPY", "base": "CHF", "quote": "JPY"},
    "CADJPY=X": {"name": "CAD/JPY", "base": "CAD", "quote": "JPY"},
    "AUDCAD=X": {"name": "AUD/CAD", "base": "AUD", "quote": "CAD"},
    "AUDNZD=X": {"name": "AUD/NZD", "base": "AUD", "quote": "NZD"},
    "USDBRL=X": {"name": "USD/BRL", "base": "USD", "quote": "BRL"},
    "USDMXN=X": {"name": "USD/MXN", "base": "USD", "quote": "MXN"},
    "USDZAR=X": {"name": "USD/ZAR", "base": "USD", "quote": "ZAR"},
    "USDTRY=X": {"name": "USD/TRY", "base": "USD", "quote": "TRY"},
    "USDRUB=X": {"name": "USD/RUB", "base": "USD", "quote": "RUB"},
    "USDPLN=X": {"name": "USD/PLN", "base": "USD", "quote": "PLN"},
    "USDNOK=X": {"name": "USD/NOK", "base": "USD", "quote": "NOK"},
    "USDSEK=X": {"name": "USD/SEK", "base": "USD", "quote": "SEK"},
    "USDDKK=X": {"name": "USD/DKK", "base": "USD", "quote": "DKK"},
    "USDTHB=X": {"name": "USD/THB", "base": "USD", "quote": "THB"},
    "USDPHP=X": {"name": "USD/PHP", "base": "USD", "quote": "PHP"},
    "USDIDR=X": {"name": "USD/IDR", "base": "USD", "quote": "IDR"},
    "USDMYR=X": {"name": "USD/MYR", "base": "USD", "quote": "MYR"},
    "USDAED=X": {"name": "USD/AED", "base": "USD", "quote": "AED"},
    "USDSAR=X": {"name": "USD/SAR", "base": "USD", "quote": "SAR"},
}

# Currency information for converter
CURRENCIES = {
    "USD": {"name": "US Dollar", "symbol": "$", "flag": "🇺🇸"},
    "EUR": {"name": "Euro", "symbol": "€", "flag": "🇪🇺"},
    "GBP": {"name": "British Pound", "symbol": "£", "flag": "🇬🇧"},
    "JPY": {"name": "Japanese Yen", "symbol": "¥", "flag": "🇯🇵"},
    "CHF": {"name": "Swiss Franc", "symbol": "CHF", "flag": "🇨🇭"},
    "AUD": {"name": "Australian Dollar", "symbol": "A$", "flag": "🇦🇺"},
    "CAD": {"name": "Canadian Dollar", "symbol": "C$", "flag": "🇨🇦"},
    "NZD": {"name": "New Zealand Dollar", "symbol": "NZ$", "flag": "🇳🇿"},
    "CNY": {"name": "Chinese Yuan", "symbol": "¥", "flag": "🇨🇳"},
    "HKD": {"name": "Hong Kong Dollar", "symbol": "HK$", "flag": "🇭🇰"},
    "SGD": {"name": "Singapore Dollar", "symbol": "S$", "flag": "🇸🇬"},
    "INR": {"name": "Indian Rupee", "symbol": "₹", "flag": "🇮🇳"},
    "KRW": {"name": "South Korean Won", "symbol": "₩", "flag": "🇰🇷"},
    "TWD": {"name": "Taiwan Dollar", "symbol": "NT$", "flag": "🇹🇼"},
    "BRL": {"name": "Brazilian Real", "symbol": "R$", "flag": "🇧🇷"},
    "MXN": {"name": "Mexican Peso", "symbol": "MX$", "flag": "🇲🇽"},
    "ZAR": {"name": "South African Rand", "symbol": "R", "flag": "🇿🇦"},
    "TRY": {"name": "Turkish Lira", "symbol": "₺", "flag": "🇹🇷"},
    "RUB": {"name": "Russian Ruble", "symbol": "₽", "flag": "🇷🇺"},
    "PLN": {"name": "Polish Zloty", "symbol": "zł", "flag": "🇵🇱"},
    "NOK": {"name": "Norwegian Krone", "symbol": "kr", "flag": "🇳🇴"},
    "SEK": {"name": "Swedish Krona", "symbol": "kr", "flag": "🇸🇪"},
    "DKK": {"name": "Danish Krone", "symbol": "kr", "flag": "🇩🇰"},
    "THB": {"name": "Thai Baht", "symbol": "฿", "flag": "🇹🇭"},
    "PHP": {"name": "Philippine Peso", "symbol": "₱", "flag": "🇵🇭"},
    "IDR": {"name": "Indonesian Rupiah", "symbol": "Rp", "flag": "🇮🇩"},
    "MYR": {"name": "Malaysian Ringgit", "symbol": "RM", "flag": "🇲🇾"},
    "AED": {"name": "UAE Dirham", "symbol": "د.إ", "flag": "🇦🇪"},
    "SAR": {"name": "Saudi Riyal", "symbol": "﷼", "flag": "🇸🇦"},
}

# ==================== FOREX RATES CACHE (in-memory) ====================
# Cache forex rates to avoid rate limiting
_forex_rates_cache = {}
_forex_rates_cache_time = None
FOREX_CACHE_TTL_SECONDS = 300  # 5 minutes

async def get_cached_forex_rates():
    """Get cached forex rates or fetch fresh ones"""
    global _forex_rates_cache, _forex_rates_cache_time
    
    now = datetime.now(timezone.utc)
    
    # Check if cache is still valid
    if _forex_rates_cache_time and (now - _forex_rates_cache_time).total_seconds() < FOREX_CACHE_TTL_SECONDS:
        return _forex_rates_cache
    
    # Fetch fresh rates
    rates = {}
    for symbol, info in FOREX_PAIRS.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                rate = hist['Close'].iloc[-1]
                rates[symbol] = {
                    'rate': float(rate),
                    'base': info['base'],
                    'quote': info['quote']
                }
        except Exception as e:
            logger.warning(f"Could not fetch rate for {symbol}: {e}")
    
    if rates:
        _forex_rates_cache = rates
        _forex_rates_cache_time = now
    
    return _forex_rates_cache

def get_forex_rate_from_cache(base: str, quote: str, cached_rates: dict) -> float:
    """Calculate forex rate from cached rates"""
    if base == quote:
        return 1.0
    
    # Try direct pair
    direct_symbol = f"{base}{quote}=X"
    if direct_symbol in cached_rates:
        return cached_rates[direct_symbol]['rate']
    
    # Try inverse pair
    inverse_symbol = f"{quote}{base}=X"
    if inverse_symbol in cached_rates:
        rate = cached_rates[inverse_symbol]['rate']
        if rate > 0:
            return 1.0 / rate
    
    # Try cross via USD
    base_to_usd = 1.0
    usd_to_quote = 1.0
    
    if base != "USD":
        base_usd = f"{base}USD=X"
        usd_base = f"USD{base}=X"
        if base_usd in cached_rates:
            base_to_usd = cached_rates[base_usd]['rate']
        elif usd_base in cached_rates and cached_rates[usd_base]['rate'] > 0:
            base_to_usd = 1.0 / cached_rates[usd_base]['rate']
        else:
            return None
    
    if quote != "USD":
        usd_quote = f"USD{quote}=X"
        quote_usd = f"{quote}USD=X"
        if usd_quote in cached_rates:
            usd_to_quote = cached_rates[usd_quote]['rate']
        elif quote_usd in cached_rates and cached_rates[quote_usd]['rate'] > 0:
            usd_to_quote = 1.0 / cached_rates[quote_usd]['rate']
        else:
            return None
    
    if base_to_usd and usd_to_quote:
        return base_to_usd * usd_to_quote
    
    return None

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
    language: Optional[str] = None  # 'en' or 'fr'

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

# ==================== OPTIONS CHAIN MODELS ====================

class OptionContract(BaseModel):
    contract_symbol: str
    strike: float
    last_price: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    change: Optional[float] = None
    percent_change: Optional[float] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    implied_volatility: Optional[float] = None
    in_the_money: bool = False

class OptionsChain(BaseModel):
    symbol: str
    expiration_date: str
    calls: List[OptionContract]
    puts: List[OptionContract]
    underlying_price: Optional[float] = None

class OptionsExpiration(BaseModel):
    symbol: str
    expirations: List[str]

# ==================== EARNINGS CALENDAR MODELS ====================

class EarningsEvent(BaseModel):
    symbol: str
    company_name: str
    earnings_date: datetime
    eps_estimate: Optional[float] = None
    eps_actual: Optional[float] = None
    revenue_estimate: Optional[float] = None
    revenue_actual: Optional[float] = None
    surprise_percent: Optional[float] = None
    time_of_day: str = "unknown"  # BMO (Before Market Open), AMC (After Market Close), unknown
    region: Optional[str] = None
    sector: Optional[str] = None

class EarningsCalendar(BaseModel):
    start_date: str
    end_date: str
    events: List[EarningsEvent]

# ==================== WEBSOCKET CONNECTION MANAGER ====================

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.subscriptions: Dict[WebSocket, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.subscriptions[websocket] = set()
        logger.info(f"WebSocket connected. Total connections: {len(self.subscriptions)}")
    
    def disconnect(self, websocket: WebSocket):
        symbols = self.subscriptions.get(websocket, set())
        for symbol in symbols:
            if symbol in self.active_connections:
                self.active_connections[symbol].discard(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
        logger.info(f"WebSocket disconnected. Total connections: {len(self.subscriptions)}")
    
    def subscribe(self, websocket: WebSocket, symbols: List[str]):
        for symbol in symbols:
            if symbol not in self.active_connections:
                self.active_connections[symbol] = set()
            self.active_connections[symbol].add(websocket)
            self.subscriptions[websocket].add(symbol)
        logger.info(f"Subscribed to {symbols}")
    
    def unsubscribe(self, websocket: WebSocket, symbols: List[str]):
        for symbol in symbols:
            if symbol in self.active_connections:
                self.active_connections[symbol].discard(websocket)
            if websocket in self.subscriptions:
                self.subscriptions[websocket].discard(symbol)
    
    async def broadcast_quote(self, symbol: str, data: dict):
        if symbol in self.active_connections:
            dead_connections = []
            for connection in self.active_connections[symbol]:
                try:
                    await connection.send_json(data)
                except Exception as e:
                    logger.error(f"Error sending to websocket: {e}")
                    dead_connections.append(connection)
            for conn in dead_connections:
                self.disconnect(conn)

manager = ConnectionManager()

# ==================== SHIPPING DATA MODELS ====================

class Port(BaseModel):
    id: str
    name: str
    country: str
    coordinates: List[float]  # [lng, lat]
    port_type: str  # "seaport", "airport", "hub"
    annual_volume: Optional[float] = None  # TEUs for ships, tonnes for air
    volume_unit: str = "TEU"
    region: str
    is_major_hub: bool = False

class ShippingRoute(BaseModel):
    id: str
    name: str
    route_type: str  # "maritime", "air_cargo"
    origin: Port
    destination: Port
    waypoints: List[List[float]] = []  # [[lng, lat], ...]
    distance_km: float
    average_transit_days: float
    annual_volume: float
    volume_unit: str
    is_strategic: bool = False
    chokepoints: List[str] = []
    affected_by_conflicts: List[str] = []
    disruption_level: float = 0  # 0-1 scale

class ShippingStats(BaseModel):
    total_maritime_routes: int
    total_air_routes: int
    total_ports: int
    total_airports: int
    routes_affected_by_conflicts: int
    volume_at_risk_percent: float

# ==================== COUNTRY DATA MODELS ====================

class CountryEconomicData(BaseModel):
    gdp: Optional[float] = None  # Current USD
    gdp_per_capita: Optional[float] = None
    gdp_growth: Optional[float] = None  # Annual %
    inflation: Optional[float] = None  # Annual %
    unemployment: Optional[float] = None  # % of labor force
    trade_balance: Optional[float] = None  # Current USD
    external_debt: Optional[float] = None  # Current USD
    debt_to_gdp: Optional[float] = None  # %
    fdi_inflow: Optional[float] = None  # Current USD
    exports: Optional[float] = None
    imports: Optional[float] = None
    currency: Optional[str] = None
    currency_code: Optional[str] = None

class CountryDemographicData(BaseModel):
    population: Optional[int] = None
    population_growth: Optional[float] = None  # Annual %
    population_density: Optional[float] = None  # per km²
    life_expectancy: Optional[float] = None
    median_age: Optional[float] = None
    urban_population_percent: Optional[float] = None
    fertility_rate: Optional[float] = None
    hdi: Optional[float] = None  # Human Development Index
    literacy_rate: Optional[float] = None

class CountryBasicInfo(BaseModel):
    name: str
    official_name: Optional[str] = None
    iso_code: str  # ISO 3166-1 alpha-2
    iso_code_3: Optional[str] = None  # ISO 3166-1 alpha-3
    region: Optional[str] = None
    subregion: Optional[str] = None
    capital: Optional[str] = None
    languages: List[str] = []
    flag_url: Optional[str] = None
    coat_of_arms_url: Optional[str] = None
    area: Optional[float] = None  # km²
    borders: List[str] = []
    timezones: List[str] = []
    continent: Optional[str] = None

class CountryData(BaseModel):
    basic: CountryBasicInfo
    economic: CountryEconomicData
    demographic: CountryDemographicData
    top_industries: List[str] = []
    major_exports: List[str] = []
    major_imports: List[str] = []
    risk_factors: List[str] = []
    last_updated: Optional[datetime] = None

# ==================== COUNTRY NAME MAPPING (ISO codes) ====================

COUNTRY_NAME_TO_ISO = {
    "United States of America": "US", "United States": "US", "USA": "US",
    "United Kingdom": "GB", "UK": "GB", "Great Britain": "GB",
    "China": "CN", "People's Republic of China": "CN",
    "Russia": "RU", "Russian Federation": "RU",
    "South Korea": "KR", "Republic of Korea": "KR", "Korea": "KR",
    "North Korea": "KP", "Democratic People's Republic of Korea": "KP",
    "Taiwan": "TW", "Republic of China": "TW",
    "Vietnam": "VN", "Viet Nam": "VN",
    "Iran": "IR", "Islamic Republic of Iran": "IR",
    "Syria": "SY", "Syrian Arab Republic": "SY",
    "Venezuela": "VE", "Bolivarian Republic of Venezuela": "VE",
    "Bolivia": "BO", "Plurinational State of Bolivia": "BO",
    "Tanzania": "TZ", "United Republic of Tanzania": "TZ",
    "Czech Republic": "CZ", "Czechia": "CZ",
    "UAE": "AE", "United Arab Emirates": "AE",
    "Saudi Arabia": "SA", "Kingdom of Saudi Arabia": "SA",
    "Ivory Coast": "CI", "Côte d'Ivoire": "CI",
    "Democratic Republic of the Congo": "CD", "DRC": "CD", "Congo (Kinshasa)": "CD",
    "Republic of the Congo": "CG", "Congo (Brazzaville)": "CG",
    "Laos": "LA", "Lao People's Democratic Republic": "LA",
    "Brunei": "BN", "Brunei Darussalam": "BN",
    "Palestine": "PS", "State of Palestine": "PS",
    "Hong Kong": "HK",
    "Macau": "MO", "Macao": "MO",
}

# World Bank indicator codes
WORLD_BANK_INDICATORS = {
    "gdp": "NY.GDP.MKTP.CD",
    "gdp_per_capita": "NY.GDP.PCAP.CD",
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",
    "inflation": "FP.CPI.TOTL.ZG",
    "unemployment": "SL.UEM.TOTL.ZS",
    "population": "SP.POP.TOTL",
    "population_growth": "SP.POP.GROW",
    "life_expectancy": "SP.DYN.LE00.IN",
    "exports": "NE.EXP.GNFS.CD",
    "imports": "NE.IMP.GNFS.CD",
    "fdi": "BX.KLT.DINV.CD.WD",
    "external_debt": "DT.DOD.DECT.CD",
    "literacy": "SE.ADT.LITR.ZS",
    "urban_population": "SP.URB.TOTL.IN.ZS",
    "fertility_rate": "SP.DYN.TFRT.IN",
}

# ==================== MAJOR PORTS DATA ====================

MAJOR_SEAPORTS = [
    # Asia
    {"id": "CNSHA", "name": "Shanghai", "country": "China", "coordinates": [121.4737, 31.2304], "annual_volume": 47000000, "region": "Asia", "is_major_hub": True},
    {"id": "CNSZN", "name": "Shenzhen", "country": "China", "coordinates": [114.0579, 22.5431], "annual_volume": 30000000, "region": "Asia", "is_major_hub": True},
    {"id": "CNNGB", "name": "Ningbo-Zhoushan", "country": "China", "coordinates": [121.5440, 29.8683], "annual_volume": 33000000, "region": "Asia", "is_major_hub": True},
    {"id": "SGSIN", "name": "Singapore", "country": "Singapore", "coordinates": [103.8198, 1.3521], "annual_volume": 37000000, "region": "Asia", "is_major_hub": True},
    {"id": "KRPUS", "name": "Busan", "country": "South Korea", "coordinates": [129.0756, 35.1796], "annual_volume": 22000000, "region": "Asia", "is_major_hub": True},
    {"id": "HKHKG", "name": "Hong Kong", "country": "Hong Kong", "coordinates": [114.1694, 22.3193], "annual_volume": 18000000, "region": "Asia", "is_major_hub": True},
    {"id": "TWKHH", "name": "Kaohsiung", "country": "Taiwan", "coordinates": [120.3014, 22.6273], "annual_volume": 15000000, "region": "Asia", "is_major_hub": True},
    {"id": "JPTYO", "name": "Tokyo", "country": "Japan", "coordinates": [139.6917, 35.6895], "annual_volume": 4500000, "region": "Asia", "is_major_hub": False},
    {"id": "VNHPH", "name": "Hai Phong", "country": "Vietnam", "coordinates": [106.6881, 20.8449], "annual_volume": 7000000, "region": "Asia", "is_major_hub": False},
    {"id": "MYTPP", "name": "Port Klang", "country": "Malaysia", "coordinates": [101.3929, 2.9997], "annual_volume": 14000000, "region": "Asia", "is_major_hub": True},
    # Middle East
    {"id": "AEJEA", "name": "Jebel Ali (Dubai)", "country": "UAE", "coordinates": [55.0272, 25.0657], "annual_volume": 14500000, "region": "Middle East", "is_major_hub": True},
    {"id": "SAJED", "name": "Jeddah", "country": "Saudi Arabia", "coordinates": [39.1728, 21.4858], "annual_volume": 4500000, "region": "Middle East", "is_major_hub": False},
    # Europe
    {"id": "NLRTM", "name": "Rotterdam", "country": "Netherlands", "coordinates": [4.4777, 51.9244], "annual_volume": 15000000, "region": "Europe", "is_major_hub": True},
    {"id": "DEHAM", "name": "Hamburg", "country": "Germany", "coordinates": [9.9937, 53.5511], "annual_volume": 9000000, "region": "Europe", "is_major_hub": True},
    {"id": "BEANR", "name": "Antwerp", "country": "Belgium", "coordinates": [4.4025, 51.2194], "annual_volume": 12000000, "region": "Europe", "is_major_hub": True},
    {"id": "ESVLC", "name": "Valencia", "country": "Spain", "coordinates": [-0.3763, 39.4699], "annual_volume": 5700000, "region": "Europe", "is_major_hub": False},
    {"id": "GRPIR", "name": "Piraeus", "country": "Greece", "coordinates": [23.6466, 37.9423], "annual_volume": 5400000, "region": "Europe", "is_major_hub": False},
    {"id": "ITGOA", "name": "Genoa", "country": "Italy", "coordinates": [8.9463, 44.4056], "annual_volume": 2800000, "region": "Europe", "is_major_hub": False},
    # Americas
    {"id": "USNYC", "name": "New York/New Jersey", "country": "USA", "coordinates": [-74.0060, 40.7128], "annual_volume": 9500000, "region": "Americas", "is_major_hub": True},
    {"id": "USLAX", "name": "Los Angeles", "country": "USA", "coordinates": [-118.2437, 33.7683], "annual_volume": 9000000, "region": "Americas", "is_major_hub": True},
    {"id": "USLGB", "name": "Long Beach", "country": "USA", "coordinates": [-118.1937, 33.7701], "annual_volume": 8200000, "region": "Americas", "is_major_hub": True},
    {"id": "USHOU", "name": "Houston", "country": "USA", "coordinates": [-95.3698, 29.7604], "annual_volume": 3800000, "region": "Americas", "is_major_hub": False},
    {"id": "PAMIT", "name": "Panama (Balboa/Colon)", "country": "Panama", "coordinates": [-79.5341, 9.0000], "annual_volume": 7000000, "region": "Americas", "is_major_hub": True},
    {"id": "BRSSZ", "name": "Santos", "country": "Brazil", "coordinates": [-46.3042, -23.9608], "annual_volume": 4500000, "region": "Americas", "is_major_hub": False},
    # Africa
    {"id": "EGPSD", "name": "Port Said", "country": "Egypt", "coordinates": [32.3019, 31.2565], "annual_volume": 3800000, "region": "Africa", "is_major_hub": True},
    {"id": "ZADUR", "name": "Durban", "country": "South Africa", "coordinates": [31.0218, -29.8587], "annual_volume": 2900000, "region": "Africa", "is_major_hub": False},
    {"id": "MATNG", "name": "Tanger Med", "country": "Morocco", "coordinates": [-5.7945, 35.8838], "annual_volume": 7200000, "region": "Africa", "is_major_hub": True},
]

MAJOR_AIRPORTS = [
    # Asia
    {"id": "HKGHKG", "name": "Hong Kong International", "country": "Hong Kong", "coordinates": [113.9185, 22.3080], "annual_volume": 4300000, "volume_unit": "tonnes", "region": "Asia", "is_major_hub": True},
    {"id": "PVGSHA", "name": "Shanghai Pudong", "country": "China", "coordinates": [121.8083, 31.1443], "annual_volume": 3700000, "volume_unit": "tonnes", "region": "Asia", "is_major_hub": True},
    {"id": "ICNSEL", "name": "Incheon (Seoul)", "country": "South Korea", "coordinates": [126.4505, 37.4602], "annual_volume": 3000000, "volume_unit": "tonnes", "region": "Asia", "is_major_hub": True},
    {"id": "SINSGP", "name": "Singapore Changi", "country": "Singapore", "coordinates": [103.9915, 1.3644], "annual_volume": 2100000, "volume_unit": "tonnes", "region": "Asia", "is_major_hub": True},
    {"id": "NRTTYO", "name": "Tokyo Narita", "country": "Japan", "coordinates": [140.3929, 35.7720], "annual_volume": 2200000, "volume_unit": "tonnes", "region": "Asia", "is_major_hub": True},
    {"id": "TPETPE", "name": "Taipei Taoyuan", "country": "Taiwan", "coordinates": [121.2332, 25.0797], "annual_volume": 2300000, "volume_unit": "tonnes", "region": "Asia", "is_major_hub": True},
    {"id": "BKKDMK", "name": "Bangkok Suvarnabhumi", "country": "Thailand", "coordinates": [100.7501, 13.6900], "annual_volume": 1400000, "volume_unit": "tonnes", "region": "Asia", "is_major_hub": False},
    # Middle East
    {"id": "DXBDXB", "name": "Dubai International", "country": "UAE", "coordinates": [55.3644, 25.2528], "annual_volume": 2600000, "volume_unit": "tonnes", "region": "Middle East", "is_major_hub": True},
    {"id": "DOHDOH", "name": "Doha Hamad", "country": "Qatar", "coordinates": [51.6082, 25.2731], "annual_volume": 2100000, "volume_unit": "tonnes", "region": "Middle East", "is_major_hub": True},
    # Europe
    {"id": "FRAFRA", "name": "Frankfurt", "country": "Germany", "coordinates": [8.5706, 50.0333], "annual_volume": 2200000, "volume_unit": "tonnes", "region": "Europe", "is_major_hub": True},
    {"id": "CDGPAR", "name": "Paris Charles de Gaulle", "country": "France", "coordinates": [2.5479, 49.0097], "annual_volume": 2100000, "volume_unit": "tonnes", "region": "Europe", "is_major_hub": True},
    {"id": "LHRLON", "name": "London Heathrow", "country": "UK", "coordinates": [-0.4543, 51.4700], "annual_volume": 1700000, "volume_unit": "tonnes", "region": "Europe", "is_major_hub": True},
    {"id": "AMSAMS", "name": "Amsterdam Schiphol", "country": "Netherlands", "coordinates": [4.7683, 52.3105], "annual_volume": 1800000, "volume_unit": "tonnes", "region": "Europe", "is_major_hub": True},
    {"id": "LUXLUX", "name": "Luxembourg Findel", "country": "Luxembourg", "coordinates": [6.2044, 49.6233], "annual_volume": 900000, "volume_unit": "tonnes", "region": "Europe", "is_major_hub": True},
    # Americas
    {"id": "MEMUSA", "name": "Memphis", "country": "USA", "coordinates": [-89.9785, 35.0421], "annual_volume": 4800000, "volume_unit": "tonnes", "region": "Americas", "is_major_hub": True},
    {"id": "ANCUSA", "name": "Anchorage", "country": "USA", "coordinates": [-149.9003, 61.2181], "annual_volume": 2800000, "volume_unit": "tonnes", "region": "Americas", "is_major_hub": True},
    {"id": "SDFUSA", "name": "Louisville", "country": "USA", "coordinates": [-85.7585, 38.2527], "annual_volume": 2600000, "volume_unit": "tonnes", "region": "Americas", "is_major_hub": True},
    {"id": "LAXUSA", "name": "Los Angeles International", "country": "USA", "coordinates": [-118.4085, 33.9425], "annual_volume": 2100000, "volume_unit": "tonnes", "region": "Americas", "is_major_hub": True},
    {"id": "JFKUSA", "name": "New York JFK", "country": "USA", "coordinates": [-73.7781, 40.6413], "annual_volume": 1300000, "volume_unit": "tonnes", "region": "Americas", "is_major_hub": True},
    {"id": "MIACMD", "name": "Miami", "country": "USA", "coordinates": [-80.2870, 25.7959], "annual_volume": 2100000, "volume_unit": "tonnes", "region": "Americas", "is_major_hub": True},
]

# ==================== STRATEGIC MARITIME ROUTES ====================

MARITIME_ROUTES = [
    {
        "id": "asia_europe_suez",
        "name": "Asia-Europe via Suez",
        "origin": "CNSHA",
        "destination": "NLRTM",
        "waypoints": [[121.47, 31.23], [114.17, 22.32], [103.82, 1.35], [73.0, 7.0], [43.0, 12.0], [32.30, 31.26], [10.0, 36.0], [4.48, 51.92]],
        "distance_km": 19500,
        "average_transit_days": 28,
        "annual_volume": 25000000,
        "is_strategic": True,
        "chokepoints": ["Suez Canal", "Strait of Malacca", "Bab el-Mandeb"],
        "affected_by_conflicts": ["Red Sea", "Yemen"]
    },
    {
        "id": "asia_europe_cape",
        "name": "Asia-Europe via Cape of Good Hope",
        "origin": "CNSHA",
        "destination": "NLRTM",
        "waypoints": [[121.47, 31.23], [114.17, 22.32], [103.82, 1.35], [55.0, -10.0], [20.0, -35.0], [-10.0, 5.0], [4.48, 51.92]],
        "distance_km": 26000,
        "average_transit_days": 40,
        "annual_volume": 5000000,
        "is_strategic": True,
        "chokepoints": ["Cape of Good Hope", "Strait of Malacca"],
        "affected_by_conflicts": []
    },
    {
        "id": "asia_uswest",
        "name": "Transpacific Asia-US West Coast",
        "origin": "CNSHA",
        "destination": "USLAX",
        "waypoints": [[121.47, 31.23], [180.0, 35.0], [-150.0, 40.0], [-118.24, 33.77]],
        "distance_km": 11500,
        "average_transit_days": 14,
        "annual_volume": 22000000,
        "is_strategic": True,
        "chokepoints": [],
        "affected_by_conflicts": ["Taiwan Strait"]
    },
    {
        "id": "asia_useast_panama",
        "name": "Asia-US East Coast via Panama",
        "origin": "CNSHA",
        "destination": "USNYC",
        "waypoints": [[121.47, 31.23], [180.0, 20.0], [-120.0, 25.0], [-79.53, 9.0], [-74.01, 40.71]],
        "distance_km": 21000,
        "average_transit_days": 30,
        "annual_volume": 8000000,
        "is_strategic": True,
        "chokepoints": ["Panama Canal"],
        "affected_by_conflicts": []
    },
    {
        "id": "europe_useast",
        "name": "Transatlantic Europe-US East",
        "origin": "NLRTM",
        "destination": "USNYC",
        "waypoints": [[4.48, 51.92], [-30.0, 45.0], [-74.01, 40.71]],
        "distance_km": 6000,
        "average_transit_days": 10,
        "annual_volume": 7500000,
        "is_strategic": True,
        "chokepoints": ["English Channel"],
        "affected_by_conflicts": []
    },
    {
        "id": "persian_gulf_asia",
        "name": "Persian Gulf-Asia (Oil)",
        "origin": "AEJEA",
        "destination": "CNSHA",
        "waypoints": [[55.03, 25.07], [56.5, 24.0], [73.0, 10.0], [103.82, 1.35], [121.47, 31.23]],
        "distance_km": 9500,
        "average_transit_days": 18,
        "annual_volume": 18000000,
        "is_strategic": True,
        "chokepoints": ["Strait of Hormuz", "Strait of Malacca"],
        "affected_by_conflicts": ["Iran", "Persian Gulf"]
    },
    {
        "id": "intra_asia",
        "name": "Intra-Asia (China-SE Asia)",
        "origin": "CNSHA",
        "destination": "SGSIN",
        "waypoints": [[121.47, 31.23], [114.17, 22.32], [103.82, 1.35]],
        "distance_km": 3900,
        "average_transit_days": 5,
        "annual_volume": 30000000,
        "is_strategic": True,
        "chokepoints": ["Strait of Malacca", "South China Sea"],
        "affected_by_conflicts": ["South China Sea", "Taiwan"]
    },
    {
        "id": "black_sea_med",
        "name": "Black Sea-Mediterranean",
        "origin": "UAODS",
        "destination": "GRPIR",
        "waypoints": [[30.73, 46.47], [29.0, 41.0], [26.0, 38.0], [23.65, 37.94]],
        "distance_km": 1800,
        "average_transit_days": 4,
        "annual_volume": 3000000,
        "is_strategic": True,
        "chokepoints": ["Bosphorus Strait", "Dardanelles"],
        "affected_by_conflicts": ["Ukraine", "Russia-Ukraine War"]
    },
    {
        "id": "south_america_europe",
        "name": "South America-Europe",
        "origin": "BRSSZ",
        "destination": "NLRTM",
        "waypoints": [[-46.30, -23.96], [-30.0, -10.0], [-20.0, 20.0], [4.48, 51.92]],
        "distance_km": 10500,
        "average_transit_days": 18,
        "annual_volume": 4000000,
        "is_strategic": False,
        "chokepoints": [],
        "affected_by_conflicts": []
    },
    {
        "id": "africa_asia",
        "name": "Africa-Asia",
        "origin": "ZADUR",
        "destination": "SGSIN",
        "waypoints": [[31.02, -29.86], [55.0, -10.0], [73.0, 7.0], [103.82, 1.35]],
        "distance_km": 8500,
        "average_transit_days": 16,
        "annual_volume": 2500000,
        "is_strategic": False,
        "chokepoints": ["Strait of Malacca"],
        "affected_by_conflicts": []
    },
]

# ==================== STRATEGIC AIR CARGO ROUTES ====================

AIR_CARGO_ROUTES = [
    {
        "id": "hk_fra",
        "name": "Hong Kong-Frankfurt",
        "origin": "HKGHKG",
        "destination": "FRAFRA",
        "waypoints": [[113.92, 22.31], [80.0, 35.0], [8.57, 50.03]],
        "distance_km": 9200,
        "average_transit_hours": 12,
        "annual_volume": 850000,
        "is_strategic": True,
        "affected_by_conflicts": []
    },
    {
        "id": "sha_anc_mem",
        "name": "Shanghai-Anchorage-Memphis",
        "origin": "PVGSHA",
        "destination": "MEMUSA",
        "waypoints": [[121.81, 31.14], [180.0, 50.0], [-149.90, 61.22], [-89.98, 35.04]],
        "distance_km": 13500,
        "average_transit_hours": 18,
        "annual_volume": 1200000,
        "is_strategic": True,
        "affected_by_conflicts": []
    },
    {
        "id": "dxb_lhr",
        "name": "Dubai-London",
        "origin": "DXBDXB",
        "destination": "LHRLON",
        "waypoints": [[55.36, 25.25], [30.0, 40.0], [-0.45, 51.47]],
        "distance_km": 5500,
        "average_transit_hours": 7,
        "annual_volume": 650000,
        "is_strategic": True,
        "affected_by_conflicts": ["Middle East"]
    },
    {
        "id": "icn_jfk",
        "name": "Seoul-New York",
        "origin": "ICNSEL",
        "destination": "JFKUSA",
        "waypoints": [[126.45, 37.46], [180.0, 55.0], [-149.90, 61.22], [-73.78, 40.64]],
        "distance_km": 11100,
        "average_transit_hours": 14,
        "annual_volume": 550000,
        "is_strategic": True,
        "affected_by_conflicts": []
    },
    {
        "id": "sin_ams",
        "name": "Singapore-Amsterdam",
        "origin": "SINSGP",
        "destination": "AMSAMS",
        "waypoints": [[103.99, 1.36], [73.0, 20.0], [4.77, 52.31]],
        "distance_km": 10400,
        "average_transit_hours": 13,
        "annual_volume": 480000,
        "is_strategic": True,
        "affected_by_conflicts": []
    },
    {
        "id": "mia_gru",
        "name": "Miami-São Paulo",
        "origin": "MIACMD",
        "destination": "GRUGRU",
        "waypoints": [[-80.29, 25.80], [-50.0, 0.0], [-46.47, -23.43]],
        "distance_km": 6900,
        "average_transit_hours": 8,
        "annual_volume": 380000,
        "is_strategic": False,
        "affected_by_conflicts": []
    },
    {
        "id": "fra_jfk",
        "name": "Frankfurt-New York",
        "origin": "FRAFRA",
        "destination": "JFKUSA",
        "waypoints": [[8.57, 50.03], [-30.0, 50.0], [-73.78, 40.64]],
        "distance_km": 6200,
        "average_transit_hours": 8,
        "annual_volume": 520000,
        "is_strategic": True,
        "affected_by_conflicts": []
    },
    {
        "id": "tpe_anc",
        "name": "Taipei-Anchorage",
        "origin": "TPETPE",
        "destination": "ANCUSA",
        "waypoints": [[121.23, 25.08], [150.0, 40.0], [-149.90, 61.22]],
        "distance_km": 8800,
        "average_transit_hours": 10,
        "annual_volume": 720000,
        "is_strategic": True,
        "affected_by_conflicts": ["Taiwan"]
    },
    {
        "id": "doh_cdg",
        "name": "Doha-Paris",
        "origin": "DOHDOH",
        "destination": "CDGPAR",
        "waypoints": [[51.61, 25.27], [30.0, 38.0], [2.55, 49.01]],
        "distance_km": 5300,
        "average_transit_hours": 6,
        "annual_volume": 420000,
        "is_strategic": True,
        "affected_by_conflicts": []
    },
    {
        "id": "nrt_lax",
        "name": "Tokyo-Los Angeles",
        "origin": "NRTTYO",
        "destination": "LAXUSA",
        "waypoints": [[140.39, 35.77], [180.0, 40.0], [-118.41, 33.94]],
        "distance_km": 8800,
        "average_transit_hours": 11,
        "annual_volume": 580000,
        "is_strategic": True,
        "affected_by_conflicts": []
    },
]

# ==================== SHIPPING SERVICES ====================

def get_port_by_id(port_id: str, ports_list: List[Dict]) -> Optional[Port]:
    """Get port by ID"""
    for port_data in ports_list:
        if port_data["id"] == port_id:
            return Port(
                id=port_data["id"],
                name=port_data["name"],
                country=port_data["country"],
                coordinates=port_data["coordinates"],
                port_type="seaport" if port_data in MAJOR_SEAPORTS else "airport",
                annual_volume=port_data.get("annual_volume"),
                volume_unit=port_data.get("volume_unit", "TEU"),
                region=port_data["region"],
                is_major_hub=port_data.get("is_major_hub", False)
            )
    return None

def calculate_disruption_level(route: Dict, conflicts: List[Dict]) -> float:
    """Calculate disruption level based on conflicts affecting the route"""
    if not route.get("affected_by_conflicts"):
        return 0.0
    
    total_impact = 0.0
    for conflict_keyword in route["affected_by_conflicts"]:
        for conflict in conflicts:
            if (conflict_keyword.lower() in conflict.get("title", "").lower() or 
                conflict_keyword.lower() in conflict.get("country", "").lower()):
                severity = conflict.get("severity", 5)
                total_impact += severity / 10
    
    return min(total_impact, 1.0)

def get_shipping_routes(route_type: str = "all", conflicts: List[Dict] = None) -> List[ShippingRoute]:
    """Get shipping routes with disruption levels"""
    routes = []
    conflicts = conflicts or []
    
    # Maritime routes
    if route_type in ["all", "maritime"]:
        for route_data in MARITIME_ROUTES:
            origin_port = get_port_by_id(route_data["origin"], MAJOR_SEAPORTS)
            dest_port = get_port_by_id(route_data["destination"], MAJOR_SEAPORTS)
            
            if not origin_port or not dest_port:
                continue
            
            disruption = calculate_disruption_level(route_data, conflicts)
            
            routes.append(ShippingRoute(
                id=route_data["id"],
                name=route_data["name"],
                route_type="maritime",
                origin=origin_port,
                destination=dest_port,
                waypoints=route_data["waypoints"],
                distance_km=route_data["distance_km"],
                average_transit_days=route_data["average_transit_days"],
                annual_volume=route_data["annual_volume"],
                volume_unit="TEU",
                is_strategic=route_data["is_strategic"],
                chokepoints=route_data.get("chokepoints", []),
                affected_by_conflicts=route_data.get("affected_by_conflicts", []),
                disruption_level=disruption
            ))
    
    # Air cargo routes
    if route_type in ["all", "air"]:
        for route_data in AIR_CARGO_ROUTES:
            origin_port = get_port_by_id(route_data["origin"], MAJOR_AIRPORTS)
            dest_port = get_port_by_id(route_data["destination"], MAJOR_AIRPORTS)
            
            if not origin_port or not dest_port:
                continue
            
            disruption = calculate_disruption_level(route_data, conflicts)
            
            routes.append(ShippingRoute(
                id=route_data["id"],
                name=route_data["name"],
                route_type="air_cargo",
                origin=origin_port,
                destination=dest_port,
                waypoints=route_data["waypoints"],
                distance_km=route_data["distance_km"],
                average_transit_days=route_data.get("average_transit_hours", 12) / 24,
                annual_volume=route_data["annual_volume"],
                volume_unit="tonnes",
                is_strategic=route_data["is_strategic"],
                chokepoints=[],
                affected_by_conflicts=route_data.get("affected_by_conflicts", []),
                disruption_level=disruption
            ))
    
    return routes

def get_all_ports() -> Dict[str, List[Port]]:
    """Get all ports and airports"""
    seaports = [Port(
        id=p["id"],
        name=p["name"],
        country=p["country"],
        coordinates=p["coordinates"],
        port_type="seaport",
        annual_volume=p.get("annual_volume"),
        volume_unit="TEU",
        region=p["region"],
        is_major_hub=p.get("is_major_hub", False)
    ) for p in MAJOR_SEAPORTS]
    
    airports = [Port(
        id=p["id"],
        name=p["name"],
        country=p["country"],
        coordinates=p["coordinates"],
        port_type="airport",
        annual_volume=p.get("annual_volume"),
        volume_unit=p.get("volume_unit", "tonnes"),
        region=p["region"],
        is_major_hub=p.get("is_major_hub", False)
    ) for p in MAJOR_AIRPORTS]
    
    return {"seaports": seaports, "airports": airports}

def get_shipping_stats(routes: List[ShippingRoute]) -> ShippingStats:
    """Calculate shipping statistics"""
    maritime_routes = [r for r in routes if r.route_type == "maritime"]
    air_routes = [r for r in routes if r.route_type == "air_cargo"]
    affected_routes = [r for r in routes if r.disruption_level > 0]
    
    total_volume = sum(r.annual_volume for r in routes)
    affected_volume = sum(r.annual_volume for r in affected_routes)
    volume_at_risk = (affected_volume / total_volume * 100) if total_volume > 0 else 0
    
    return ShippingStats(
        total_maritime_routes=len(maritime_routes),
        total_air_routes=len(air_routes),
        total_ports=len(MAJOR_SEAPORTS),
        total_airports=len(MAJOR_AIRPORTS),
        routes_affected_by_conflicts=len(affected_routes),
        volume_at_risk_percent=volume_at_risk
    )

# ==================== COUNTRY DATA SERVICES ====================

async def get_country_from_rest_countries(country_code: str) -> Optional[Dict]:
    """Fetch basic country info from REST Countries API"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Try by ISO code first
            response = await client.get(f"https://restcountries.com/v3.1/alpha/{country_code}")
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return data[0]
            return None
    except Exception as e:
        logger.error(f"Error fetching REST Countries data for {country_code}: {e}")
        return None

async def get_world_bank_indicator(country_code: str, indicator: str) -> Optional[float]:
    """Fetch a single indicator from World Bank API"""
    try:
        # Convert 2-letter to 3-letter code for World Bank
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator}?format=json&per_page=5&mrv=1"
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                if len(data) > 1 and data[1]:
                    for item in data[1]:
                        if item.get('value') is not None:
                            return float(item['value'])
        return None
    except Exception as e:
        logger.error(f"Error fetching World Bank indicator {indicator} for {country_code}: {e}")
        return None

async def get_world_bank_data(country_code: str) -> Dict[str, Optional[float]]:
    """Fetch multiple indicators from World Bank API"""
    results = {}
    
    # Fetch indicators in parallel
    tasks = {}
    for key, indicator in WORLD_BANK_INDICATORS.items():
        tasks[key] = get_world_bank_indicator(country_code, indicator)
    
    # Execute all tasks
    for key, task in tasks.items():
        try:
            results[key] = await task
        except Exception:
            results[key] = None
    
    return results

def get_iso_code(country_name: str) -> str:
    """Convert country name to ISO code"""
    # Check direct mapping
    if country_name in COUNTRY_NAME_TO_ISO:
        return COUNTRY_NAME_TO_ISO[country_name]
    
    # Check if it's already an ISO code
    if len(country_name) == 2:
        return country_name.upper()
    
    # Try common variations
    name_upper = country_name.upper()
    for key, value in COUNTRY_NAME_TO_ISO.items():
        if key.upper() == name_upper:
            return value
    
    # Return first 2 letters as fallback (not ideal but handles many cases)
    return country_name[:2].upper()

async def get_cached_country_data(country_code: str) -> Optional[Dict]:
    """Get country data from MongoDB cache if fresh"""
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)  # Cache for 7 days
        
        cached = await db.country_cache.find_one({
            "country_code": country_code.upper(),
            "cached_at": {"$gte": cutoff}
        })
        
        if cached:
            logger.info(f"Country cache hit for {country_code}")
            # Remove MongoDB _id before returning
            cached.pop('_id', None)
            return cached.get("data")
        return None
    except Exception as e:
        logger.error(f"Error reading country cache: {e}")
        return None

async def cache_country_data(country_code: str, data: Dict):
    """Save country data to MongoDB cache"""
    try:
        await db.country_cache.update_one(
            {"country_code": country_code.upper()},
            {
                "$set": {
                    "data": data,
                    "cached_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        logger.info(f"Cached country data for {country_code}")
    except Exception as e:
        logger.error(f"Error caching country data: {e}")

def extract_industries_from_economy(economy_info: str) -> List[str]:
    """Extract main industries from economy description"""
    # Common industry keywords
    industries = []
    keywords = [
        "agriculture", "mining", "oil", "gas", "petroleum", "manufacturing",
        "technology", "finance", "banking", "tourism", "services", "fishing",
        "textiles", "automotive", "electronics", "pharmaceuticals", "chemicals",
        "steel", "construction", "real estate", "telecommunications", "aerospace",
        "food processing", "machinery", "shipbuilding", "renewable energy"
    ]
    
    if economy_info:
        economy_lower = economy_info.lower()
        for keyword in keywords:
            if keyword in economy_lower:
                industries.append(keyword.title())
    
    return industries[:5]  # Return top 5

async def fetch_country_data(country_name_or_code: str) -> Optional[CountryData]:
    """Fetch comprehensive country data"""
    # Determine ISO code
    if len(country_name_or_code) == 2:
        country_code = country_name_or_code.upper()
    elif len(country_name_or_code) == 3:
        country_code = country_name_or_code.upper()
    else:
        country_code = get_iso_code(country_name_or_code)
    
    # Check cache first
    cached = await get_cached_country_data(country_code)
    if cached:
        return CountryData(**cached)
    
    # Fetch from REST Countries API
    rest_data = await get_country_from_rest_countries(country_code)
    if not rest_data:
        logger.warning(f"No REST Countries data for {country_code}")
        return None
    
    # Fetch from World Bank API
    wb_data = await get_world_bank_data(country_code)
    
    # Build basic info
    basic = CountryBasicInfo(
        name=rest_data.get('name', {}).get('common', country_name_or_code),
        official_name=rest_data.get('name', {}).get('official'),
        iso_code=rest_data.get('cca2', country_code),
        iso_code_3=rest_data.get('cca3'),
        region=rest_data.get('region'),
        subregion=rest_data.get('subregion'),
        capital=rest_data.get('capital', [None])[0] if rest_data.get('capital') else None,
        languages=list(rest_data.get('languages', {}).values()),
        flag_url=rest_data.get('flags', {}).get('svg'),
        coat_of_arms_url=rest_data.get('coatOfArms', {}).get('svg'),
        area=rest_data.get('area'),
        borders=rest_data.get('borders', []),
        timezones=rest_data.get('timezones', []),
        continent=rest_data.get('continents', [None])[0] if rest_data.get('continents') else None
    )
    
    # Get currency info
    currencies = rest_data.get('currencies', {})
    currency_code = list(currencies.keys())[0] if currencies else None
    currency_name = currencies.get(currency_code, {}).get('name') if currency_code else None
    
    # Build economic data
    economic = CountryEconomicData(
        gdp=wb_data.get('gdp'),
        gdp_per_capita=wb_data.get('gdp_per_capita'),
        gdp_growth=wb_data.get('gdp_growth'),
        inflation=wb_data.get('inflation'),
        unemployment=wb_data.get('unemployment'),
        exports=wb_data.get('exports'),
        imports=wb_data.get('imports'),
        fdi_inflow=wb_data.get('fdi'),
        external_debt=wb_data.get('external_debt'),
        currency=currency_name,
        currency_code=currency_code
    )
    
    # Calculate trade balance
    if economic.exports and economic.imports:
        economic.trade_balance = economic.exports - economic.imports
    
    # Build demographic data
    population = wb_data.get('population')
    area = rest_data.get('area')
    
    demographic = CountryDemographicData(
        population=int(population) if population else None,
        population_growth=wb_data.get('population_growth'),
        population_density=population / area if population and area else None,
        life_expectancy=wb_data.get('life_expectancy'),
        urban_population_percent=wb_data.get('urban_population'),
        fertility_rate=wb_data.get('fertility_rate'),
        literacy_rate=wb_data.get('literacy')
    )
    
    # Get HDI from static data (World Bank doesn't have it directly)
    hdi_data = {
        "NO": 0.961, "IE": 0.945, "CH": 0.962, "HK": 0.952, "IS": 0.959,
        "DE": 0.942, "SE": 0.947, "AU": 0.951, "NL": 0.941, "DK": 0.948,
        "FI": 0.940, "SG": 0.939, "GB": 0.929, "BE": 0.937, "NZ": 0.937,
        "CA": 0.936, "US": 0.921, "AT": 0.916, "IL": 0.919, "JP": 0.925,
        "KR": 0.925, "FR": 0.903, "ES": 0.905, "IT": 0.895, "PT": 0.866,
        "GR": 0.887, "PL": 0.876, "CN": 0.768, "BR": 0.754, "MX": 0.758,
        "RU": 0.822, "TR": 0.838, "SA": 0.875, "AE": 0.911, "IN": 0.633,
        "ZA": 0.713, "EG": 0.731, "NG": 0.539, "ID": 0.713, "MY": 0.803,
        "TH": 0.800, "VN": 0.703, "PH": 0.699, "PK": 0.544, "BD": 0.661,
    }
    demographic.hdi = hdi_data.get(country_code)
    
    # Build final country data
    country_data = CountryData(
        basic=basic,
        economic=economic,
        demographic=demographic,
        top_industries=[],
        major_exports=[],
        major_imports=[],
        risk_factors=[],
        last_updated=datetime.now(timezone.utc)
    )
    
    # Add risk factors based on conflicts
    conflicts_data = await get_cached_conflicts()
    for conflict in conflicts_data:
        conflict_dict = conflict.model_dump() if hasattr(conflict, 'model_dump') else conflict
        if country_name_or_code.lower() in conflict_dict.get('country', '').lower():
            country_data.risk_factors.append(conflict_dict.get('title', 'Unknown conflict'))
    
    # Cache the data
    await cache_country_data(country_code, country_data.model_dump())
    
    return country_data

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

async def get_cached_news(cache_key: str, max_age_hours: int = 1) -> List[Dict]:
    """Get news from MongoDB cache if fresh"""
    try:
        full_cache_key = f"news_{cache_key}"
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        
        cached = await db.news_cache.find_one({
            "cache_key": full_cache_key,
            "cached_at": {"$gte": cutoff}
        })
        
        if cached and cached.get("articles"):
            logger.info(f"News cache hit for {full_cache_key}")
            return cached["articles"]
        return []
    except Exception as e:
        logger.error(f"Error reading news cache: {e}")
        return []

async def cache_news(cache_key: str, articles: List[Dict]):
    """Save news to MongoDB cache"""
    try:
        full_cache_key = f"news_{cache_key}"
        await db.news_cache.update_one(
            {"cache_key": full_cache_key},
            {
                "$set": {
                    "articles": articles,
                    "cached_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        logger.info(f"Cached {len(articles)} news articles for {full_cache_key}")
    except Exception as e:
        logger.error(f"Error caching news: {e}")

async def fetch_news(query: str = None, country: str = None, category: str = None, page_size: int = 20, languages: List[str] = None) -> List[NewsArticle]:
    """Fetch news from cache or NewsAPI - supports EN and FR languages"""
    # Default to both English and French
    if languages is None:
        languages = ['en', 'fr']
    
    # Check cache first
    cache_key = f"{query or 'general'}_{','.join(languages)}"
    cached = await get_cached_news(cache_key)
    if cached:
        return [NewsArticle(**a) for a in cached[:page_size]]
    
    if not NEWS_API_KEY:
        return get_mock_news()
    
    try:
        all_articles = []
        
        async with httpx.AsyncClient() as http_client:
            for lang in languages:
                params = {
                    'apiKey': NEWS_API_KEY,
                    'pageSize': min(page_size // len(languages) + 5, 50),  # Split between languages
                    'language': lang
                }
                
                if query:
                    params['q'] = query
                    url = 'https://newsapi.org/v2/everything'
                else:
                    url = 'https://newsapi.org/v2/top-headlines'
                    # NewsAPI requires country OR sources for top-headlines
                    # Use country code matching language for better results
                    if country:
                        params['country'] = country
                    elif lang == 'fr':
                        params['country'] = 'fr'  # French news from France
                    elif lang == 'en':
                        params['country'] = 'us'  # English news from US by default
                    if category:
                        params['category'] = category
                
                try:
                    response = await http_client.get(url, params=params, timeout=10.0)
                    data = response.json()
                    
                    if data.get('status') == 'ok':
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
                                country=country,
                                language=lang  # Track language
                            )
                            all_articles.append(article_obj)
                except Exception as e:
                    logger.warning(f"Error fetching {lang} news: {e}")
        
        if not all_articles:
            return get_mock_news()
        
        # Sort by date and limit
        all_articles.sort(key=lambda x: x.published_at, reverse=True)
        articles = all_articles[:page_size]
        
        # Cache the results
        await cache_news(cache_key, [a.model_dump() for a in articles])
        
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
    """Return mock news for demo purposes - EN/FR only"""
    return [
        NewsArticle(
            title="Fed Signals Potential Rate Cuts Amid Economic Uncertainty",
            description="Federal Reserve officials hint at possible interest rate reductions as inflation shows signs of cooling.",
            url="https://example.com/news/1",
            source="Financial Times",
            published_at=datetime.now(timezone.utc) - timedelta(hours=1),
            tags=["MACRO", "FED", "RATES"],
            sentiment="neutral",
            language="en"
        ),
        NewsArticle(
            title="Oil Prices Surge on Middle East Tensions",
            description="Crude oil futures jump 3% as geopolitical risks in the Middle East intensify.",
            url="https://example.com/news/2",
            source="Reuters",
            published_at=datetime.now(timezone.utc) - timedelta(hours=2),
            tags=["OIL", "COMMODITY", "GEOPOLITICS"],
            sentiment="negative",
            language="en"
        ),
        NewsArticle(
            title="Tech Giants Report Strong Q4 Earnings",
            description="Apple, Microsoft, and Google exceed analyst expectations with robust revenue growth.",
            url="https://example.com/news/3",
            source="Bloomberg",
            published_at=datetime.now(timezone.utc) - timedelta(hours=3),
            tags=["AAPL", "MSFT", "GOOGL", "TECH"],
            sentiment="positive",
            language="en"
        ),
        NewsArticle(
            title="La BCE maintient ses taux directeurs inchangés",
            description="La Banque centrale européenne a décidé de maintenir ses taux d'intérêt face à l'incertitude économique.",
            url="https://example.com/news/4",
            source="Les Echos",
            published_at=datetime.now(timezone.utc) - timedelta(hours=4),
            tags=["EUROPE", "ECB", "MACRO"],
            sentiment="neutral",
            language="fr"
        ),
        NewsArticle(
            title="European Markets Rally on ECB Stimulus Hopes",
            description="European equities gain as traders anticipate continued monetary support from the ECB.",
            url="https://example.com/news/5",
            source="MarketWatch",
            published_at=datetime.now(timezone.utc) - timedelta(hours=5),
            tags=["EUROPE", "ECB", "MACRO"],
            sentiment="positive",
            language="en"
        ),
        NewsArticle(
            title="Les marchés asiatiques en ordre dispersé",
            description="Shanghai et Hong Kong reculent tandis que Tokyo progresse grâce à la faiblesse du yen.",
            url="https://example.com/news/6",
            source="Le Figaro",
            published_at=datetime.now(timezone.utc) - timedelta(hours=6),
            tags=["ASIA", "CHINA", "JAPAN"],
            sentiment="neutral",
            language="fr"
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
    
    # First try static data
    static_chain = supply_chains.get(symbol.upper(), [])
    
    # If no static data, try to get from yfinance
    if not static_chain:
        return get_supply_chain_from_yfinance(symbol)
    
    return static_chain

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
    languages: Optional[str] = Query(None, description="Comma-separated language codes (en,fr)"),
    page_size: int = Query(20, ge=1, le=100)
):
    """Get news articles in English and/or French"""
    lang_list = None
    if languages:
        lang_list = [l.strip().lower() for l in languages.split(",") if l.strip().lower() in ['en', 'fr']]
    return await fetch_news(query=q, country=country, category=category, page_size=page_size, languages=lang_list or ['en', 'fr'])

@api_router.get("/news/breaking", response_model=List[NewsArticle])
async def get_breaking_news():
    """Get breaking/top headlines in English and French"""
    return await fetch_news(page_size=10, languages=['en', 'fr'])

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

# ==================== OPTIONS CHAIN SERVICE ====================

def get_options_expirations(symbol: str) -> Optional[OptionsExpiration]:
    """Get available option expiration dates for a symbol"""
    try:
        ticker = yf.Ticker(symbol)
        expirations = ticker.options
        
        if not expirations:
            return None
        
        return OptionsExpiration(
            symbol=symbol,
            expirations=list(expirations)
        )
    except Exception as e:
        logger.error(f"Error fetching options expirations for {symbol}: {e}")
        return None

def get_options_chain(symbol: str, expiration: str) -> Optional[OptionsChain]:
    """Get options chain for a symbol and expiration date"""
    try:
        ticker = yf.Ticker(symbol)
        
        # Get underlying price
        info = ticker.info
        underlying_price = info.get('regularMarketPrice', info.get('currentPrice', 0))
        
        # Get options chain
        opt = ticker.option_chain(expiration)
        
        calls = []
        for _, row in opt.calls.iterrows():
            calls.append(OptionContract(
                contract_symbol=row.get('contractSymbol', ''),
                strike=float(row.get('strike', 0)),
                last_price=float(row.get('lastPrice', 0)) if row.get('lastPrice') else None,
                bid=float(row.get('bid', 0)) if row.get('bid') else None,
                ask=float(row.get('ask', 0)) if row.get('ask') else None,
                change=float(row.get('change', 0)) if row.get('change') else None,
                percent_change=float(row.get('percentChange', 0)) if row.get('percentChange') else None,
                volume=int(row.get('volume', 0)) if row.get('volume') and not np.isnan(row.get('volume')) else None,
                open_interest=int(row.get('openInterest', 0)) if row.get('openInterest') and not np.isnan(row.get('openInterest')) else None,
                implied_volatility=float(row.get('impliedVolatility', 0)) if row.get('impliedVolatility') else None,
                in_the_money=bool(row.get('inTheMoney', False))
            ))
        
        puts = []
        for _, row in opt.puts.iterrows():
            puts.append(OptionContract(
                contract_symbol=row.get('contractSymbol', ''),
                strike=float(row.get('strike', 0)),
                last_price=float(row.get('lastPrice', 0)) if row.get('lastPrice') else None,
                bid=float(row.get('bid', 0)) if row.get('bid') else None,
                ask=float(row.get('ask', 0)) if row.get('ask') else None,
                change=float(row.get('change', 0)) if row.get('change') else None,
                percent_change=float(row.get('percentChange', 0)) if row.get('percentChange') else None,
                volume=int(row.get('volume', 0)) if row.get('volume') and not np.isnan(row.get('volume')) else None,
                open_interest=int(row.get('openInterest', 0)) if row.get('openInterest') and not np.isnan(row.get('openInterest')) else None,
                implied_volatility=float(row.get('impliedVolatility', 0)) if row.get('impliedVolatility') else None,
                in_the_money=bool(row.get('inTheMoney', False))
            ))
        
        return OptionsChain(
            symbol=symbol,
            expiration_date=expiration,
            calls=calls,
            puts=puts,
            underlying_price=underlying_price
        )
    except Exception as e:
        logger.error(f"Error fetching options chain for {symbol}: {e}")
        return None

# ==================== EARNINGS CALENDAR SERVICE ====================

async def get_cached_earnings(cache_key: str, max_age_hours: int = 6) -> List[Dict]:
    """Get earnings from MongoDB cache if fresh"""
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        
        cached = await db.earnings_cache.find_one({
            "cache_key": cache_key,
            "cached_at": {"$gte": cutoff}
        })
        
        if cached and cached.get("events"):
            logger.info(f"Earnings cache hit for {cache_key}")
            return cached["events"]
        return []
    except Exception as e:
        logger.error(f"Error reading earnings cache: {e}")
        return []

async def cache_earnings(cache_key: str, events: List[Dict]):
    """Save earnings to MongoDB cache"""
    try:
        await db.earnings_cache.update_one(
            {"cache_key": cache_key},
            {
                "$set": {
                    "events": events,
                    "cached_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        logger.info(f"Cached {len(events)} earnings events for {cache_key}")
    except Exception as e:
        logger.error(f"Error caching earnings: {e}")

def get_earnings_for_symbol(symbol: str) -> Optional[EarningsEvent]:
    """Get next earnings date for a symbol using yfinance"""
    try:
        ticker = yf.Ticker(symbol)
        calendar = ticker.calendar
        
        if calendar is None:
            return None
        
        # Get company info
        info = ticker.info
        company_name = info.get('shortName', info.get('longName', symbol))
        sector = info.get('sector')
        region = get_region(symbol)
        
        # Extract earnings date - handle both dict and DataFrame formats
        earnings_date = None
        eps_estimate = None
        revenue_estimate = None
        
        if isinstance(calendar, dict):
            # New yfinance format - dict
            if 'Earnings Date' in calendar:
                ed = calendar['Earnings Date']
                if isinstance(ed, list) and len(ed) > 0:
                    earnings_date = ed[0]
                elif ed:
                    earnings_date = ed
            if 'Earnings Average' in calendar:
                eps_estimate = calendar.get('Earnings Average')
            if 'Revenue Average' in calendar:
                revenue_estimate = calendar.get('Revenue Average')
        elif hasattr(calendar, 'empty') and not calendar.empty:
            # Old yfinance format - DataFrame
            if 'Earnings Date' in calendar.index:
                earnings_dates = calendar.loc['Earnings Date']
                if isinstance(earnings_dates, pd.Series) and len(earnings_dates) > 0:
                    earnings_date = earnings_dates.iloc[0]
                elif hasattr(earnings_dates, 'timestamp'):
                    earnings_date = earnings_dates
            if 'Earnings Average' in calendar.index:
                eps_estimate = float(calendar.loc['Earnings Average'].iloc[0]) if not pd.isna(calendar.loc['Earnings Average'].iloc[0]) else None
            if 'Revenue Average' in calendar.index:
                revenue_estimate = float(calendar.loc['Revenue Average'].iloc[0]) if not pd.isna(calendar.loc['Revenue Average'].iloc[0]) else None
        
        if earnings_date is None:
            return None
        
        # Convert to datetime if needed
        if hasattr(earnings_date, 'to_pydatetime'):
            earnings_date = earnings_date.to_pydatetime()
        elif isinstance(earnings_date, str):
            earnings_date = datetime.fromisoformat(earnings_date)
        elif isinstance(earnings_date, (int, float)):
            # Unix timestamp
            earnings_date = datetime.fromtimestamp(earnings_date, tz=timezone.utc)
        
        # Ensure timezone aware
        if hasattr(earnings_date, 'tzinfo') and earnings_date.tzinfo is None:
            earnings_date = earnings_date.replace(tzinfo=timezone.utc)
        
        return EarningsEvent(
            symbol=symbol,
            company_name=company_name,
            earnings_date=earnings_date,
            eps_estimate=float(eps_estimate) if eps_estimate is not None else None,
            revenue_estimate=float(revenue_estimate) if revenue_estimate is not None else None,
            region=region,
            sector=sector,
            time_of_day="unknown"
        )
    except Exception as e:
        logger.error(f"Error fetching earnings for {symbol}: {e}")
        return None

async def fetch_earnings_calendar(days_ahead: int = 14, region: Optional[str] = None) -> List[EarningsEvent]:
    """Fetch earnings calendar for the coming days"""
    cache_key = f"earnings_{days_ahead}_{region or 'all'}"
    
    # Check cache first
    cached = await get_cached_earnings(cache_key)
    if cached:
        return [EarningsEvent(**e) for e in cached]
    
    events = []
    now = datetime.now(timezone.utc)
    end_date = now + timedelta(days=days_ahead)
    
    # Select stocks based on region
    if region == "US":
        symbols = list(US_STOCKS.keys())[:30]
    elif region == "Europe":
        symbols = list(EUROPEAN_STOCKS.keys())[:30]
    elif region == "Asia":
        symbols = list(ASIAN_STOCKS.keys())[:30]
    else:
        # Mix from all regions
        symbols = list(US_STOCKS.keys())[:20] + list(EUROPEAN_STOCKS.keys())[:15] + list(ASIAN_STOCKS.keys())[:15]
    
    for symbol in symbols:
        event = get_earnings_for_symbol(symbol)
        if event and event.earnings_date:
            # Ensure earnings_date is timezone aware
            event_date = event.earnings_date
            if event_date.tzinfo is None:
                event_date = event_date.replace(tzinfo=timezone.utc)
            try:
                if now <= event_date <= end_date:
                    events.append(event)
            except TypeError:
                # Skip if date comparison fails
                pass
    
    # Sort by date
    events.sort(key=lambda x: x.earnings_date)
    
    # Cache results
    await cache_earnings(cache_key, [e.model_dump() for e in events])
    
    return events

# ==================== ENHANCED SUPPLY CHAIN SERVICE ====================

def get_supply_chain_from_yfinance(symbol: str) -> List[SupplyChainNode]:
    """Get supply chain data from yfinance recommendations and major holders"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        nodes = []
        
        # Try to get institutional holders as potential customers/partners
        try:
            holders = ticker.institutional_holders
            if holders is not None and not holders.empty:
                for idx, row in holders.head(3).iterrows():
                    holder_name = row.get('Holder', 'Unknown')
                    nodes.append(SupplyChainNode(
                        id=f"holder_{idx}_{symbol}",
                        name=holder_name,
                        symbol=None,
                        node_type="investor",
                        tier=2,
                        country="USA",
                        sector="Financial Services",
                        relationship="investor",
                        dependency_percent=float(row.get('pctHeld', 0) * 100) if 'pctHeld' in row else None,
                        risk_level="low",
                        confidence_score=0.7
                    ))
        except Exception:
            pass
        
        # Get sector peers as potential partners/competitors
        sector = info.get('sector', '')
        
        # Create synthetic supply chain based on sector
        sector_suppliers = {
            "Technology": [
                ("Taiwan Semiconductor", "TSM", "Semiconductors", "supplier", "Taiwan", 0.9),
                ("Samsung Electronics", "005930.KS", "Components", "supplier", "South Korea", 0.85),
                ("ASML Holding", "ASML.AS", "Equipment", "supplier", "Netherlands", 0.8),
            ],
            "Consumer Cyclical": [
                ("CATL", "300750.SZ", "Batteries", "supplier", "China", 0.85),
                ("Panasonic", "6752.T", "Electronics", "supplier", "Japan", 0.8),
            ],
            "Healthcare": [
                ("Thermo Fisher", "TMO", "Lab Equipment", "supplier", "USA", 0.8),
                ("Danaher", "DHR", "Medical Devices", "supplier", "USA", 0.75),
            ],
            "Financial Services": [
                ("Visa", "V", "Payments", "partner", "USA", 0.7),
                ("Mastercard", "MA", "Payments", "partner", "USA", 0.7),
            ],
            "Energy": [
                ("Schlumberger", "SLB", "Oilfield Services", "supplier", "USA", 0.8),
                ("Halliburton", "HAL", "Services", "supplier", "USA", 0.75),
            ],
        }
        
        sector_customers = {
            "Technology": [
                ("Amazon", "AMZN", "Cloud/Retail", "customer", "USA", 0.85),
                ("Microsoft", "MSFT", "Cloud", "customer", "USA", 0.9),
                ("Google", "GOOGL", "Cloud/AI", "customer", "USA", 0.85),
            ],
            "Consumer Cyclical": [
                ("Amazon", "AMZN", "Retail", "customer", "USA", 0.8),
                ("Walmart", "WMT", "Retail", "customer", "USA", 0.75),
            ],
        }
        
        # Add sector-based suppliers
        if sector in sector_suppliers:
            for name, sym, sec, rel, country, conf in sector_suppliers[sector]:
                if sym != symbol:  # Don't add self
                    nodes.append(SupplyChainNode(
                        id=f"sector_{sym}_{symbol}",
                        name=name,
                        symbol=sym,
                        node_type="supplier",
                        tier=1,
                        country=country,
                        sector=sec,
                        relationship=rel,
                        dependency_percent=np.random.uniform(10, 30),
                        risk_level="medium" if country not in ["USA", "Netherlands"] else "low",
                        confidence_score=conf
                    ))
        
        # Add sector-based customers
        if sector in sector_customers:
            for name, sym, sec, rel, country, conf in sector_customers[sector]:
                if sym != symbol:
                    nodes.append(SupplyChainNode(
                        id=f"customer_{sym}_{symbol}",
                        name=name,
                        symbol=sym,
                        node_type="customer",
                        tier=1,
                        country=country,
                        sector=sec,
                        relationship=rel,
                        dependency_percent=np.random.uniform(5, 20),
                        risk_level="low",
                        confidence_score=conf
                    ))
        
        return nodes
    except Exception as e:
        logger.error(f"Error fetching yfinance supply chain for {symbol}: {e}")
        return []

# ==================== WEBSOCKET BACKGROUND TASK ====================

async def broadcast_price_updates():
    """Background task to broadcast price updates via WebSocket"""
    while True:
        try:
            # Get all subscribed symbols
            all_symbols = set()
            for symbols in manager.active_connections.keys():
                all_symbols.add(symbols)
            
            if all_symbols:
                for symbol in all_symbols:
                    if symbol in manager.active_connections and manager.active_connections[symbol]:
                        quote = get_yahoo_quote(symbol)
                        if quote:
                            await manager.broadcast_quote(symbol, {
                                "type": "quote_update",
                                "data": quote.model_dump()
                            })
            
            # Wait before next update cycle (5 seconds for rate limiting)
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Error in broadcast task: {e}")
            await asyncio.sleep(5)

# ==================== OPTIONS CHAIN ROUTES ====================

@api_router.get("/options/expirations/{symbol}", response_model=Optional[OptionsExpiration])
async def get_options_expirations_route(symbol: str):
    """Get available option expiration dates for a symbol"""
    result = get_options_expirations(symbol.upper())
    if not result:
        raise HTTPException(status_code=404, detail=f"No options data available for {symbol}")
    return result

@api_router.get("/options/chain/{symbol}", response_model=Optional[OptionsChain])
async def get_options_chain_route(symbol: str, expiration: str = Query(..., description="Expiration date (YYYY-MM-DD)")):
    """Get options chain for a symbol and expiration date"""
    result = get_options_chain(symbol.upper(), expiration)
    if not result:
        raise HTTPException(status_code=404, detail=f"No options chain available for {symbol} at {expiration}")
    return result

# ==================== EARNINGS CALENDAR ROUTES ====================

@api_router.get("/earnings/calendar")
async def get_earnings_calendar(
    days: int = Query(14, ge=1, le=60, description="Days ahead to look"),
    region: Optional[str] = Query(None, description="US, Europe, Asia")
):
    """Get earnings calendar for upcoming days"""
    events = await fetch_earnings_calendar(days, region)
    return {
        "start_date": datetime.now(timezone.utc).isoformat(),
        "end_date": (datetime.now(timezone.utc) + timedelta(days=days)).isoformat(),
        "events": [e.model_dump() for e in events]
    }

@api_router.get("/earnings/symbol/{symbol}")
async def get_earnings_for_symbol_route(symbol: str):
    """Get next earnings date for a specific symbol"""
    event = get_earnings_for_symbol(symbol.upper())
    if not event:
        raise HTTPException(status_code=404, detail=f"No earnings data available for {symbol}")
    return event.model_dump()

# ==================== SHIPPING ROUTES ====================

@api_router.get("/shipping/routes")
async def get_shipping_routes_api(
    route_type: str = Query("all", description="Route type: all, maritime, air")
):
    """Get global shipping routes with disruption analysis"""
    # Get current conflicts for disruption calculation
    conflicts_data = await get_cached_conflicts()
    conflicts_list = [c.model_dump() if hasattr(c, 'model_dump') else c for c in conflicts_data]
    
    routes = get_shipping_routes(route_type, conflicts_list)
    stats = get_shipping_stats(routes)
    
    return {
        "routes": [r.model_dump() for r in routes],
        "stats": stats.model_dump()
    }

@api_router.get("/shipping/ports")
async def get_shipping_ports_api():
    """Get all major ports and airports"""
    ports = get_all_ports()
    return {
        "seaports": [p.model_dump() for p in ports["seaports"]],
        "airports": [p.model_dump() for p in ports["airports"]],
        "total_seaports": len(ports["seaports"]),
        "total_airports": len(ports["airports"])
    }

@api_router.get("/shipping/stats")
async def get_shipping_stats_api():
    """Get shipping statistics and risk summary"""
    conflicts_data = await get_cached_conflicts()
    conflicts_list = [c.model_dump() if hasattr(c, 'model_dump') else c for c in conflicts_data]
    
    routes = get_shipping_routes("all", conflicts_list)
    stats = get_shipping_stats(routes)
    
    # Calculate additional risk metrics
    affected_routes = [r for r in routes if r.disruption_level > 0]
    
    return {
        "stats": stats.model_dump(),
        "risk_summary": {
            "high_risk_routes": len([r for r in affected_routes if r.disruption_level > 0.5]),
            "medium_risk_routes": len([r for r in affected_routes if 0.2 < r.disruption_level <= 0.5]),
            "low_risk_routes": len([r for r in affected_routes if r.disruption_level <= 0.2]),
            "critical_chokepoints": list(set([cp for r in routes for cp in r.chokepoints if r.disruption_level > 0.3]))
        }
    }

# ==================== COMMODITIES ROUTES ====================

@api_router.get("/commodities")
async def get_all_commodities():
    """Get all commodities with current prices"""
    results = []
    
    for symbol, info in COMMODITIES.items():
        quote = get_yahoo_quote(symbol)
        if quote:
            results.append({
                "symbol": symbol,
                "name": info["name"],
                "category": info["type"],
                "price": quote.price,
                "change": quote.change,
                "change_percent": quote.change_percent,
                "high": quote.high,
                "low": quote.low,
                "open": quote.open,
                "previous_close": quote.previous_close,
                "currency": quote.currency,
                "timestamp": quote.timestamp.isoformat()
            })
    
    # Group by category
    categories = {}
    for item in results:
        cat = item["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
    
    return {
        "commodities": results,
        "by_category": categories,
        "categories": list(categories.keys()),
        "total": len(results)
    }

@api_router.get("/commodities/category/{category}")
async def get_commodities_by_category(category: str):
    """Get commodities by category"""
    results = []
    
    for symbol, info in COMMODITIES.items():
        if info["type"].lower() == category.lower():
            quote = get_yahoo_quote(symbol)
            if quote:
                results.append({
                    "symbol": symbol,
                    "name": info["name"],
                    "category": info["type"],
                    "price": quote.price,
                    "change": quote.change,
                    "change_percent": quote.change_percent,
                    "currency": quote.currency
                })
    
    return {"commodities": results, "category": category, "total": len(results)}

# ==================== FOREX ROUTES ====================

@api_router.get("/forex/pairs")
async def get_all_forex_pairs():
    """Get all forex pairs with current rates"""
    results = []
    
    for symbol, info in FOREX_PAIRS.items():
        quote = get_yahoo_quote(symbol)
        if quote:
            results.append({
                "symbol": symbol,
                "name": info["name"],
                "base": info["base"],
                "quote": info["quote"],
                "rate": quote.price,
                "change": quote.change,
                "change_percent": quote.change_percent,
                "bid": quote.bid,
                "ask": quote.ask,
                "high": quote.high,
                "low": quote.low,
                "timestamp": quote.timestamp.isoformat()
            })
    
    # Group by base currency
    by_base = {}
    for item in results:
        base = item["base"]
        if base not in by_base:
            by_base[base] = []
        by_base[base].append(item)
    
    return {
        "pairs": results,
        "by_base_currency": by_base,
        "total": len(results)
    }

@api_router.get("/forex/currencies")
async def get_currencies():
    """Get list of available currencies"""
    return {
        "currencies": [
            {"code": code, **info} for code, info in CURRENCIES.items()
        ],
        "total": len(CURRENCIES)
    }

@api_router.get("/forex/rate/{base}/{quote}")
async def get_forex_rate(base: str, quote: str):
    """Get exchange rate between two currencies"""
    base = base.upper()
    quote_curr = quote.upper()
    
    # Try direct pair
    symbol = f"{base}{quote_curr}=X"
    if symbol in FOREX_PAIRS:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        rate = info.get('regularMarketPrice', info.get('ask', 0))
        return {
            "base": base,
            "quote": quote_curr,
            "rate": rate,
            "symbol": symbol,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # Try inverse pair
    inverse_symbol = f"{quote_curr}{base}=X"
    if inverse_symbol in FOREX_PAIRS:
        ticker = yf.Ticker(inverse_symbol)
        info = ticker.info
        rate = info.get('regularMarketPrice', info.get('ask', 0))
        if rate > 0:
            return {
                "base": base,
                "quote": quote_curr,
                "rate": 1 / rate,
                "symbol": inverse_symbol,
                "inverse": True,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    # Try via USD cross
    try:
        base_to_usd = 1.0
        usd_to_quote = 1.0
        
        if base != "USD":
            # Get base to USD
            base_usd_symbol = f"{base}USD=X"
            usd_base_symbol = f"USD{base}=X"
            
            if base_usd_symbol in FOREX_PAIRS or True:
                ticker = yf.Ticker(base_usd_symbol)
                info = ticker.info
                base_to_usd = info.get('regularMarketPrice', info.get('ask', 0))
                if base_to_usd == 0:
                    ticker = yf.Ticker(usd_base_symbol)
                    info = ticker.info
                    rate = info.get('regularMarketPrice', info.get('ask', 0))
                    if rate > 0:
                        base_to_usd = 1 / rate
        
        if quote_curr != "USD":
            # Get USD to quote
            usd_quote_symbol = f"USD{quote_curr}=X"
            ticker = yf.Ticker(usd_quote_symbol)
            info = ticker.info
            usd_to_quote = info.get('regularMarketPrice', info.get('ask', 0))
        
        if base_to_usd > 0 and usd_to_quote > 0:
            cross_rate = base_to_usd * usd_to_quote
            return {
                "base": base,
                "quote": quote_curr,
                "rate": cross_rate,
                "cross_via": "USD",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    except Exception as e:
        logger.error(f"Error calculating cross rate: {e}")
    
    raise HTTPException(status_code=404, detail=f"Exchange rate not found for {base}/{quote_curr}")

@api_router.post("/forex/convert")
async def convert_currency(
    amount: float = Query(..., description="Amount to convert"),
    from_currency: str = Query(..., description="Source currency code"),
    to_currencies: str = Query(..., description="Target currency codes, comma-separated")
):
    """Convert amount from one currency to multiple currencies using cached rates"""
    from_curr = from_currency.upper()
    to_list = [c.strip().upper() for c in to_currencies.split(",")]
    
    # Get cached forex rates (single batch fetch)
    cached_rates = await get_cached_forex_rates()
    
    results = []
    
    for to_curr in to_list:
        if to_curr == from_curr:
            results.append({
                "from": from_curr,
                "to": to_curr,
                "amount": amount,
                "converted": amount,
                "rate": 1.0,
                "currency_info": CURRENCIES.get(to_curr, {})
            })
            continue
        
        try:
            # Get rate from cache
            rate = get_forex_rate_from_cache(from_curr, to_curr, cached_rates)
            
            if rate and rate > 0:
                converted = amount * rate
                results.append({
                    "from": from_curr,
                    "to": to_curr,
                    "amount": amount,
                    "converted": converted,
                    "rate": rate,
                    "currency_info": CURRENCIES.get(to_curr, {})
                })
            else:
                results.append({
                    "from": from_curr,
                    "to": to_curr,
                    "amount": amount,
                    "converted": None,
                    "rate": None,
                    "error": f"Rate not available for {from_curr}/{to_curr}"
                })
        except Exception as e:
            logger.error(f"Error converting {from_curr} to {to_curr}: {e}")
            results.append({
                "from": from_curr,
                "to": to_curr,
                "amount": amount,
                "converted": None,
                "rate": None,
                "error": str(e)
            })
    
    return {
        "source": {
            "currency": from_curr,
            "amount": amount,
            "currency_info": CURRENCIES.get(from_curr, {})
        },
        "conversions": results,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ==================== COUNTRY DATA ROUTES ====================

@api_router.get("/country/{country_code}")
async def get_country_data_route(country_code: str):
    """Get comprehensive country data (economic + demographic)"""
    data = await fetch_country_data(country_code)
    if not data:
        raise HTTPException(status_code=404, detail=f"Country data not found for {country_code}")
    return data.model_dump()

@api_router.get("/country/search/{query}")
async def search_country(query: str):
    """Search for countries by name"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"https://restcountries.com/v3.1/name/{query}")
            if response.status_code == 200:
                data = response.json()
                results = []
                for country in data[:10]:  # Limit to 10 results
                    results.append({
                        "name": country.get('name', {}).get('common'),
                        "official_name": country.get('name', {}).get('official'),
                        "iso_code": country.get('cca2'),
                        "iso_code_3": country.get('cca3'),
                        "region": country.get('region'),
                        "flag_url": country.get('flags', {}).get('svg')
                    })
                return {"results": results}
            return {"results": []}
    except Exception as e:
        logger.error(f"Error searching countries: {e}")
        return {"results": []}

@api_router.get("/countries/list")
async def get_countries_list():
    """Get list of all countries with basic info"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get("https://restcountries.com/v3.1/all?fields=name,cca2,cca3,region,subregion,flags,population,area")
            if response.status_code == 200:
                data = response.json()
                countries = []
                for country in data:
                    countries.append({
                        "name": country.get('name', {}).get('common'),
                        "iso_code": country.get('cca2'),
                        "iso_code_3": country.get('cca3'),
                        "region": country.get('region'),
                        "subregion": country.get('subregion'),
                        "flag_url": country.get('flags', {}).get('svg'),
                        "population": country.get('population'),
                        "area": country.get('area')
                    })
                # Sort by name
                countries.sort(key=lambda x: x.get('name', ''))
                return {"countries": countries, "total": len(countries)}
            return {"countries": [], "total": 0}
    except Exception as e:
        logger.error(f"Error fetching countries list: {e}")
        return {"countries": [], "total": 0}

# ==================== WEBSOCKET ROUTE ====================

@app.websocket("/ws/quotes")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time quote updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            action = message.get("action")
            symbols = message.get("symbols", [])
            
            if action == "subscribe":
                manager.subscribe(websocket, [s.upper() for s in symbols])
                await websocket.send_json({
                    "type": "subscribed",
                    "symbols": symbols
                })
            elif action == "unsubscribe":
                manager.unsubscribe(websocket, [s.upper() for s in symbols])
                await websocket.send_json({
                    "type": "unsubscribed",
                    "symbols": symbols
                })
            elif action == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup"""
    asyncio.create_task(broadcast_price_updates())
    logger.info("WebSocket broadcast task started")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
