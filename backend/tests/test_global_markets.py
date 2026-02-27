"""
Test suite for Global Markets Bloomberg-like Terminal
Tests: Stock Universe, Technical Indicators, Impact Score, Screener with Region filters
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://multi-asset-hub-1.preview.emergentagent.com')


class TestMarketUniverse:
    """Tests for /api/market/universe endpoint - Global stock coverage"""
    
    def test_universe_returns_163_plus_stocks(self):
        """Test that universe contains 163+ stocks across US, Europe, Asia"""
        response = requests.get(f"{BASE_URL}/api/market/universe")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify total stocks is 163+
        total_stocks = data.get('total_stocks', 0)
        assert total_stocks >= 163, f"Expected 163+ stocks, got {total_stocks}"
        
        # Verify US stocks present (should be 48)
        us_stocks = data.get('us', [])
        assert len(us_stocks) >= 40, f"Expected 40+ US stocks, got {len(us_stocks)}"
        
        # Verify Europe stocks present (should be 55)
        europe_stocks = data.get('europe', [])
        assert len(europe_stocks) >= 50, f"Expected 50+ Europe stocks, got {len(europe_stocks)}"
        
        # Verify Asia stocks present (should be 60)
        asia_stocks = data.get('asia', [])
        assert len(asia_stocks) >= 50, f"Expected 50+ Asia stocks, got {len(asia_stocks)}"
        
        print(f"✓ Universe contains {total_stocks} stocks: US={len(us_stocks)}, Europe={len(europe_stocks)}, Asia={len(asia_stocks)}")
    
    def test_universe_structure(self):
        """Verify universe response structure"""
        response = requests.get(f"{BASE_URL}/api/market/universe")
        data = response.json()
        
        # Check required fields
        assert 'us' in data, "Missing 'us' field"
        assert 'europe' in data, "Missing 'europe' field"
        assert 'asia' in data, "Missing 'asia' field"
        assert 'indices' in data, "Missing 'indices' field"
        assert 'commodities' in data, "Missing 'commodities' field"
        assert 'forex' in data, "Missing 'forex' field"
        assert 'total_stocks' in data, "Missing 'total_stocks' field"
        
        # Check sample stock structure
        if data['us']:
            sample = data['us'][0]
            assert 'symbol' in sample, "US stock missing 'symbol'"
            assert 'name' in sample, "US stock missing 'name'"
            assert 'sector' in sample, "US stock missing 'sector'"
            assert 'region' in sample, "US stock missing 'region'"
            print(f"✓ Universe structure valid. Sample US stock: {sample['symbol']} - {sample['name']}")


class TestScreenerRegionFilter:
    """Tests for /api/screener with region filter"""
    
    def test_screener_europe_region(self):
        """Test screener returns European stocks when region=Europe"""
        response = requests.get(f"{BASE_URL}/api/screener?asset_type=stock&region=Europe")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        results = data.get('results', [])
        
        # Should return some European stocks
        assert len(results) > 0, "Expected European stocks, got none"
        
        # Verify all returned stocks have Europe region
        for stock in results:
            region = stock.get('region')
            assert region == 'Europe', f"Stock {stock.get('symbol')} has region '{region}', expected 'Europe'"
        
        print(f"✓ Screener returned {len(results)} European stocks")
    
    def test_screener_asia_region(self):
        """Test screener returns Asian stocks when region=Asia"""
        response = requests.get(f"{BASE_URL}/api/screener?asset_type=stock&region=Asia")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        results = data.get('results', [])
        
        # Should return some Asian stocks
        assert len(results) > 0, "Expected Asian stocks, got none"
        
        # Verify all returned stocks have Asia region
        for stock in results:
            region = stock.get('region')
            assert region == 'Asia', f"Stock {stock.get('symbol')} has region '{region}', expected 'Asia'"
        
        print(f"✓ Screener returned {len(results)} Asian stocks")
    
    def test_screener_us_region(self):
        """Test screener returns US stocks when region=US"""
        response = requests.get(f"{BASE_URL}/api/screener?asset_type=stock&region=US")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        results = data.get('results', [])
        
        # Should return some US stocks
        assert len(results) > 0, "Expected US stocks, got none"
        
        # Verify all returned stocks have US region
        for stock in results:
            region = stock.get('region')
            assert region == 'US', f"Stock {stock.get('symbol')} has region '{region}', expected 'US'"
        
        print(f"✓ Screener returned {len(results)} US stocks")
    
    def test_screener_sector_filter(self):
        """Test screener with sector filter"""
        response = requests.get(f"{BASE_URL}/api/screener?asset_type=stock&sector=Technology")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        results = data.get('results', [])
        
        print(f"✓ Screener sector filter returned {len(results)} Technology stocks")


class TestTechnicalIndicators:
    """Tests for /api/market/technical/{symbol} endpoint"""
    
    def test_technical_indicators_aapl(self):
        """Test technical indicators for AAPL"""
        response = requests.get(f"{BASE_URL}/api/market/technical/AAPL")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify required fields
        assert 'symbol' in data, "Missing 'symbol' field"
        assert data['symbol'] == 'AAPL', f"Expected symbol 'AAPL', got {data.get('symbol')}"
        
        # Check RSI
        assert 'rsi_14' in data, "Missing 'rsi_14' field"
        if data['rsi_14'] is not None:
            assert 0 <= data['rsi_14'] <= 100, f"RSI should be 0-100, got {data['rsi_14']}"
        
        # Check MACD
        assert 'macd' in data, "Missing 'macd' field"
        assert 'macd_signal' in data, "Missing 'macd_signal' field"
        
        # Check SMA
        assert 'sma_20' in data, "Missing 'sma_20' field"
        assert 'sma_50' in data, "Missing 'sma_50' field"
        
        # Check Bollinger Bands
        assert 'bollinger_upper' in data, "Missing 'bollinger_upper' field"
        assert 'bollinger_middle' in data, "Missing 'bollinger_middle' field"
        assert 'bollinger_lower' in data, "Missing 'bollinger_lower' field"
        
        # Check signal and trend
        assert 'signal' in data, "Missing 'signal' field"
        assert data['signal'] in ['buy', 'sell', 'hold', None], f"Invalid signal: {data['signal']}"
        
        assert 'trend' in data, "Missing 'trend' field"
        assert data['trend'] in ['bullish', 'bearish', 'neutral', None], f"Invalid trend: {data['trend']}"
        
        print(f"✓ Technical indicators for AAPL: RSI={data.get('rsi_14')}, MACD={data.get('macd')}, Signal={data.get('signal')}, Trend={data.get('trend')}")
    
    def test_technical_indicators_european_stock(self):
        """Test technical indicators for a European stock"""
        response = requests.get(f"{BASE_URL}/api/market/technical/MC.PA")  # LVMH
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get('symbol') == 'MC.PA', f"Expected symbol 'MC.PA', got {data.get('symbol')}"
        print(f"✓ Technical indicators for MC.PA (LVMH): RSI={data.get('rsi_14')}")


class TestImpactScore:
    """Tests for /api/impact/{symbol} endpoint"""
    
    def test_impact_score_aapl(self):
        """Test impact score for AAPL"""
        response = requests.get(f"{BASE_URL}/api/impact/AAPL")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify required fields
        assert 'asset' in data or 'score' in data, "Missing core impact score fields"
        
        # Check score
        assert 'score' in data, "Missing 'score' field"
        score = data['score']
        assert isinstance(score, (int, float)), f"Score should be numeric, got {type(score)}"
        assert 0 <= score <= 100, f"Score should be 0-100, got {score}"
        
        # Check risk_level
        assert 'risk_level' in data, "Missing 'risk_level' field"
        risk_level = data['risk_level']
        assert risk_level in ['low', 'medium', 'high', 'critical'], f"Invalid risk_level: {risk_level}"
        
        # Check factors
        assert 'factors' in data, "Missing 'factors' field"
        assert isinstance(data['factors'], list), f"Factors should be a list, got {type(data['factors'])}"
        
        print(f"✓ Impact score for AAPL: Score={score}, Risk={risk_level}, Factors count={len(data['factors'])}")
    
    def test_impact_score_tsm(self):
        """Test impact score for TSM (Taiwan Semiconductor) - high geopolitical risk"""
        response = requests.get(f"{BASE_URL}/api/impact/TSM")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert 'score' in data, "Missing 'score' field"
        assert 'risk_level' in data, "Missing 'risk_level' field"
        
        print(f"✓ Impact score for TSM: Score={data['score']}, Risk={data['risk_level']}")
    
    def test_impact_score_factors_structure(self):
        """Verify impact score factors structure"""
        response = requests.get(f"{BASE_URL}/api/impact/NVDA")
        assert response.status_code == 200
        
        data = response.json()
        factors = data.get('factors', [])
        
        if factors:
            factor = factors[0]
            # Check factor structure
            assert 'description' in factor or 'name' in factor or 'type' in factor, "Factor missing description/name/type"
            print(f"✓ Impact factors structure valid. Sample factor: {factor}")


class TestCoreEndpoints:
    """Tests for other core API endpoints"""
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        print("✓ API root endpoint working")
    
    def test_market_quote_aapl(self):
        """Test market quote for AAPL"""
        response = requests.get(f"{BASE_URL}/api/market/quote/AAPL")
        assert response.status_code == 200
        
        data = response.json()
        assert 'symbol' in data
        assert 'price' in data
        assert data['price'] > 0, "Price should be positive"
        print(f"✓ Quote for AAPL: ${data['price']}")
    
    def test_market_indices(self):
        """Test market indices endpoint"""
        response = requests.get(f"{BASE_URL}/api/market/indices")
        assert response.status_code == 200
        
        data = response.json()
        indices = data.get('indices', [])
        assert len(indices) > 0, "Expected some indices"
        print(f"✓ Indices endpoint returned {len(indices)} indices")
    
    def test_conflicts_endpoint(self):
        """Test conflicts endpoint"""
        response = requests.get(f"{BASE_URL}/api/conflicts")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Conflicts should be a list"
        if data:
            conflict = data[0]
            assert 'title' in conflict
            assert 'country' in conflict
            assert 'severity' in conflict
        print(f"✓ Conflicts endpoint returned {len(data)} conflicts")
    
    def test_news_endpoint(self):
        """Test news endpoint"""
        response = requests.get(f"{BASE_URL}/api/news")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "News should be a list"
        print(f"✓ News endpoint returned {len(data)} articles")
    
    def test_supply_chain_aapl(self):
        """Test supply chain for AAPL"""
        response = requests.get(f"{BASE_URL}/api/supplychain/AAPL")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Supply chain should be a list"
        assert len(data) > 0, "AAPL should have supply chain data"
        
        # Check node structure
        node = data[0]
        assert 'name' in node
        assert 'country' in node
        assert 'relationship' in node
        print(f"✓ Supply chain for AAPL: {len(data)} nodes")
    
    def test_watchlist_crud(self):
        """Test watchlist CRUD operations"""
        # Add to watchlist
        add_response = requests.post(
            f"{BASE_URL}/api/watchlist",
            json={"symbol": "TEST_MSFT", "name": "Microsoft Test", "asset_type": "stock"}
        )
        assert add_response.status_code == 200, f"Add to watchlist failed: {add_response.text}"
        
        # Get watchlist
        get_response = requests.get(f"{BASE_URL}/api/watchlist")
        assert get_response.status_code == 200
        
        watchlist = get_response.json()
        added = any(item['symbol'] == 'TEST_MSFT' for item in watchlist)
        assert added, "TEST_MSFT should be in watchlist"
        
        # Delete from watchlist
        del_response = requests.delete(f"{BASE_URL}/api/watchlist/TEST_MSFT")
        assert del_response.status_code == 200
        
        print("✓ Watchlist CRUD operations working")


class TestScreenerAssetTypes:
    """Test screener with different asset types"""
    
    def test_screener_stocks_default(self):
        """Test screener default stocks"""
        response = requests.get(f"{BASE_URL}/api/screener?asset_type=stock")
        assert response.status_code == 200
        
        data = response.json()
        results = data.get('results', [])
        assert len(results) > 0, "Expected some stocks"
        print(f"✓ Screener stocks: {len(results)} results")
    
    def test_screener_commodities(self):
        """Test screener commodities"""
        response = requests.get(f"{BASE_URL}/api/screener?asset_type=commodity")
        assert response.status_code == 200
        
        data = response.json()
        results = data.get('results', [])
        print(f"✓ Screener commodities: {len(results)} results")
    
    def test_screener_forex(self):
        """Test screener forex"""
        response = requests.get(f"{BASE_URL}/api/screener?asset_type=forex")
        assert response.status_code == 200
        
        data = response.json()
        results = data.get('results', [])
        print(f"✓ Screener forex: {len(results)} results")
    
    def test_screener_indices(self):
        """Test screener indices"""
        response = requests.get(f"{BASE_URL}/api/screener?asset_type=index")
        assert response.status_code == 200
        
        data = response.json()
        results = data.get('results', [])
        print(f"✓ Screener indices: {len(results)} results")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
