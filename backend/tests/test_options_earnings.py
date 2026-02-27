"""
Test suite for Options Chain, Earnings Calendar, and Supply Chain features
Tests for Bloomberg-like Terminal iteration 3
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# ==================== OPTIONS CHAIN TESTS ====================

class TestOptionsExpirations:
    """Tests for /api/options/expirations/{symbol} endpoint"""
    
    def test_options_expirations_aapl(self):
        """Test getting options expirations for AAPL"""
        response = requests.get(f"{BASE_URL}/api/options/expirations/AAPL")
        print(f"Response status: {response.status_code}")
        
        # Should return 200 with expiration dates
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"Response data: {data}")
        
        # Verify structure
        assert "symbol" in data, "Response should have 'symbol' field"
        assert "expirations" in data, "Response should have 'expirations' field"
        assert data["symbol"] == "AAPL", f"Symbol should be AAPL, got {data['symbol']}"
        
        # Verify expirations list
        assert isinstance(data["expirations"], list), "Expirations should be a list"
        assert len(data["expirations"]) > 0, "Should have at least one expiration date"
        
        # Verify date format (YYYY-MM-DD)
        first_exp = data["expirations"][0]
        try:
            datetime.strptime(first_exp, "%Y-%m-%d")
        except ValueError:
            pytest.fail(f"Expiration date {first_exp} is not in YYYY-MM-DD format")
        
        print(f"PASS: Found {len(data['expirations'])} expiration dates for AAPL")
    
    def test_options_expirations_invalid_symbol(self):
        """Test getting options expirations for invalid symbol"""
        response = requests.get(f"{BASE_URL}/api/options/expirations/INVALID123")
        print(f"Response status: {response.status_code}")
        
        # Should return 404 for invalid symbol
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: Invalid symbol returns 404")


class TestOptionsChain:
    """Tests for /api/options/chain/{symbol}?expiration={date} endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get a valid expiration date for testing"""
        response = requests.get(f"{BASE_URL}/api/options/expirations/AAPL")
        if response.status_code == 200:
            data = response.json()
            if data.get("expirations"):
                self.valid_expiration = data["expirations"][0]
            else:
                pytest.skip("No valid expiration dates available")
        else:
            pytest.skip("Could not get expiration dates")
    
    def test_options_chain_aapl(self):
        """Test getting options chain for AAPL with valid expiration"""
        response = requests.get(f"{BASE_URL}/api/options/chain/AAPL?expiration={self.valid_expiration}")
        print(f"Response status: {response.status_code}")
        
        # Should return 200 with chain data
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"Options chain keys: {data.keys()}")
        
        # Verify structure
        assert "symbol" in data, "Response should have 'symbol' field"
        assert "expiration_date" in data, "Response should have 'expiration_date' field"
        assert "calls" in data, "Response should have 'calls' field"
        assert "puts" in data, "Response should have 'puts' field"
        
        assert data["symbol"] == "AAPL", f"Symbol should be AAPL, got {data['symbol']}"
        assert data["expiration_date"] == self.valid_expiration
        
        # Verify calls and puts are lists
        assert isinstance(data["calls"], list), "Calls should be a list"
        assert isinstance(data["puts"], list), "Puts should be a list"
        
        # Verify at least some options exist
        assert len(data["calls"]) > 0 or len(data["puts"]) > 0, "Should have at least some options"
        
        # Verify option contract structure if calls exist
        if data["calls"]:
            call = data["calls"][0]
            assert "strike" in call, "Option should have 'strike' field"
            assert "contract_symbol" in call, "Option should have 'contract_symbol' field"
            print(f"First call option: strike={call.get('strike')}, last_price={call.get('last_price')}")
        
        print(f"PASS: Found {len(data['calls'])} calls and {len(data['puts'])} puts for AAPL")
    
    def test_options_chain_has_underlying_price(self):
        """Test that options chain includes underlying price"""
        response = requests.get(f"{BASE_URL}/api/options/chain/AAPL?expiration={self.valid_expiration}")
        
        if response.status_code == 200:
            data = response.json()
            # underlying_price is optional but should be present
            if "underlying_price" in data and data["underlying_price"] is not None:
                assert data["underlying_price"] > 0, "Underlying price should be positive"
                print(f"PASS: Underlying price is ${data['underlying_price']}")
            else:
                print("INFO: Underlying price not included in response")


# ==================== EARNINGS CALENDAR TESTS ====================

class TestEarningsCalendar:
    """Tests for /api/earnings/calendar endpoint"""
    
    def test_earnings_calendar_default(self):
        """Test getting earnings calendar with default parameters"""
        response = requests.get(f"{BASE_URL}/api/earnings/calendar")
        print(f"Response status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        print(f"Earnings calendar keys: {data.keys()}")
        
        # Verify structure
        assert "start_date" in data, "Response should have 'start_date' field"
        assert "end_date" in data, "Response should have 'end_date' field"
        assert "events" in data, "Response should have 'events' field"
        
        assert isinstance(data["events"], list), "Events should be a list"
        print(f"PASS: Earnings calendar returned {len(data['events'])} events")
    
    def test_earnings_calendar_60_days(self):
        """Test getting earnings calendar for 60 days"""
        response = requests.get(f"{BASE_URL}/api/earnings/calendar?days=60")
        print(f"Response status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        print(f"Found {len(data.get('events', []))} earnings events for 60 days")
        
        # Verify events have required fields
        if data["events"]:
            event = data["events"][0]
            assert "symbol" in event, "Event should have 'symbol' field"
            assert "company_name" in event, "Event should have 'company_name' field"
            assert "earnings_date" in event, "Event should have 'earnings_date' field"
            print(f"First event: {event.get('symbol')} - {event.get('company_name')}")
        
        print(f"PASS: Earnings calendar with 60 days works")
    
    def test_earnings_calendar_us_region(self):
        """Test filtering earnings by US region"""
        response = requests.get(f"{BASE_URL}/api/earnings/calendar?days=30&region=US")
        print(f"Response status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        events = data.get("events", [])
        
        # If there are events, they should be US region
        if events:
            for event in events[:5]:
                region = event.get("region")
                print(f"Event: {event.get('symbol')} - Region: {region}")
                # Note: region might be None if not set
        
        print(f"PASS: US region filter returned {len(events)} events")
    
    def test_earnings_calendar_europe_region(self):
        """Test filtering earnings by Europe region"""
        response = requests.get(f"{BASE_URL}/api/earnings/calendar?days=30&region=Europe")
        print(f"Response status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        print(f"PASS: Europe region filter returned {len(data.get('events', []))} events")
    
    def test_earnings_calendar_asia_region(self):
        """Test filtering earnings by Asia region"""
        response = requests.get(f"{BASE_URL}/api/earnings/calendar?days=30&region=Asia")
        print(f"Response status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        print(f"PASS: Asia region filter returned {len(data.get('events', []))} events")


class TestEarningsSymbol:
    """Tests for /api/earnings/symbol/{symbol} endpoint"""
    
    def test_earnings_symbol_aapl(self):
        """Test getting earnings for AAPL"""
        response = requests.get(f"{BASE_URL}/api/earnings/symbol/AAPL")
        print(f"Response status: {response.status_code}")
        
        # May return 200 or 404 depending on if earnings data is available
        if response.status_code == 200:
            data = response.json()
            print(f"AAPL earnings data: {data}")
            
            assert "symbol" in data, "Response should have 'symbol' field"
            assert data["symbol"] == "AAPL"
            
            if "earnings_date" in data and data["earnings_date"]:
                print(f"PASS: AAPL next earnings date: {data['earnings_date']}")
            else:
                print("INFO: No earnings date available for AAPL")
        elif response.status_code == 404:
            print("INFO: No earnings data available for AAPL (404)")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")
    
    def test_earnings_symbol_invalid(self):
        """Test getting earnings for invalid symbol"""
        response = requests.get(f"{BASE_URL}/api/earnings/symbol/INVALID123")
        print(f"Response status: {response.status_code}")
        
        # Should return 404 for invalid symbol
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("PASS: Invalid symbol returns 404")


# ==================== SUPPLY CHAIN TESTS ====================

class TestSupplyChain:
    """Tests for /api/supplychain/{symbol} endpoint"""
    
    def test_supply_chain_aapl(self):
        """Test getting supply chain for AAPL (predefined)"""
        response = requests.get(f"{BASE_URL}/api/supplychain/AAPL")
        print(f"Response status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "AAPL should have supply chain data"
        
        # Verify structure of a supply chain node
        node = data[0]
        assert "id" in node, "Node should have 'id' field"
        assert "name" in node, "Node should have 'name' field"
        assert "relationship" in node, "Node should have 'relationship' field"
        assert "country" in node, "Node should have 'country' field"
        
        # Count suppliers and customers
        suppliers = [n for n in data if n.get("relationship") == "supplier"]
        customers = [n for n in data if n.get("relationship") == "customer"]
        
        print(f"PASS: AAPL has {len(suppliers)} suppliers and {len(customers)} customers")
    
    def test_supply_chain_jnj(self):
        """Test getting supply chain for JNJ (fallback via yfinance)"""
        response = requests.get(f"{BASE_URL}/api/supplychain/JNJ")
        print(f"Response status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        print(f"PASS: JNJ supply chain returned {len(data)} nodes")
    
    def test_supply_chain_tsla(self):
        """Test getting supply chain for TSLA (predefined)"""
        response = requests.get(f"{BASE_URL}/api/supplychain/TSLA")
        print(f"Response status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "TSLA should have supply chain data"
        
        print(f"PASS: TSLA supply chain returned {len(data)} nodes")


# ==================== NAVIGATION TESTS ====================

class TestHealthAndNavigation:
    """Basic health check and navigation endpoint tests"""
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        print(f"Response status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("PASS: API health check passed")
    
    def test_market_universe(self):
        """Test market universe endpoint"""
        response = requests.get(f"{BASE_URL}/api/market/universe")
        print(f"Response status: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Universe returns us, europe, asia, commodities, forex, indices keys
        assert "us" in data or "europe" in data or "asia" in data, "Response should have region fields"
        print(f"PASS: Market universe has US: {len(data.get('us', []))}, Europe: {len(data.get('europe', []))}, Asia: {len(data.get('asia', []))} stocks")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
