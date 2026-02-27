"""
Test suite for Shareholders History and Supply Chain APIs
Features tested:
- /api/shareholders/{symbol}/history - Historical shareholding changes
- /api/supplychain/{symbol} - Supply chain data for DAX/FTSE companies
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestShareholdersHistoryAPI:
    """Tests for shareholders history endpoint - static/mocked data for ~40 companies"""
    
    def test_shareholders_history_mc_pa(self):
        """Test shareholders history for MC.PA (LVMH - France CAC40)"""
        response = requests.get(f"{BASE_URL}/api/shareholders/MC.PA/history")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "symbol" in data
        assert data["symbol"] == "MC.PA"
        assert "history" in data
        assert len(data["history"]) > 0, "Expected history data for MC.PA"
        
        # Verify structure of history records
        record = data["history"][0]
        assert "date" in record, "Expected 'date' in history record"
        assert "holder" in record, "Expected 'holder' in history record"
        assert "percent" in record, "Expected 'percent' in history record"
        assert "change" in record, "Expected 'change' in history record"
        
        print(f"MC.PA history: {len(data['history'])} records found")
        # Verify Famille Arnault is present
        holders = [r["holder"] for r in data["history"]]
        assert any("Arnault" in h for h in holders), "Expected Famille Arnault in MC.PA shareholders"

    def test_shareholders_history_vow3_de(self):
        """Test shareholders history for VOW3.DE (Volkswagen - Germany DAX)"""
        response = requests.get(f"{BASE_URL}/api/shareholders/VOW3.DE/history")
        assert response.status_code == 200
        
        data = response.json()
        assert data["symbol"] == "VOW3.DE"
        assert len(data["history"]) > 0, "Expected history data for VOW3.DE"
        
        holders = [r["holder"] for r in data["history"]]
        print(f"VOW3.DE history holders: {set(holders)}")
        
    def test_shareholders_history_hsba_l(self):
        """Test shareholders history for HSBA.L (HSBC - UK FTSE)"""
        response = requests.get(f"{BASE_URL}/api/shareholders/HSBA.L/history")
        assert response.status_code == 200
        
        data = response.json()
        assert data["symbol"] == "HSBA.L"
        assert len(data["history"]) > 0, "Expected history data for HSBA.L"
        
        # Check for Ping An Insurance (major shareholder)
        holders = [r["holder"] for r in data["history"]]
        print(f"HSBA.L history holders: {set(holders)}")

    def test_shareholders_history_bmw_de(self):
        """Test shareholders history for BMW.DE"""
        response = requests.get(f"{BASE_URL}/api/shareholders/BMW.DE/history")
        assert response.status_code == 200
        
        data = response.json()
        assert data["symbol"] == "BMW.DE"
        assert len(data["history"]) > 0, "Expected history data for BMW.DE"
        
        # Check for Quandt/Klatten family
        holders = [r["holder"] for r in data["history"]]
        assert any("Quandt" in h for h in holders), "Expected Quandt/Klatten family in BMW.DE shareholders"

    def test_shareholders_history_unknown_symbol(self):
        """Test history for unknown symbol returns empty list"""
        response = requests.get(f"{BASE_URL}/api/shareholders/UNKNOWN999/history")
        assert response.status_code == 200  # Should return 200 with empty history
        
        data = response.json()
        assert data["symbol"] == "UNKNOWN999"
        assert data["history"] == [], "Expected empty history for unknown symbol"


class TestSupplyChainAPI:
    """Tests for supply chain endpoint - DAX/FTSE companies"""
    
    def test_supplychain_bmw_de(self):
        """Test supply chain for BMW.DE (DAX company)"""
        response = requests.get(f"{BASE_URL}/api/supplychain/BMW.DE")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Expected list of supply chain nodes"
        assert len(data) > 0, "Expected supply chain data for BMW.DE"
        
        # Verify structure
        node = data[0]
        assert "id" in node
        assert "name" in node
        assert "node_type" in node
        assert "tier" in node
        assert "country" in node
        assert "relationship" in node
        assert "risk_level" in node
        
        print(f"BMW.DE supply chain: {len(data)} nodes")
        
        # Check for suppliers and customers
        relationships = [n["relationship"] for n in data]
        print(f"Relationships: {set(relationships)}")
        
    def test_supplychain_sap_de(self):
        """Test supply chain for SAP.DE (DAX company)"""
        response = requests.get(f"{BASE_URL}/api/supplychain/SAP.DE")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Expected supply chain data for SAP.DE"
        print(f"SAP.DE supply chain: {len(data)} nodes")

    def test_supplychain_hsba_l(self):
        """Test supply chain for HSBA.L (FTSE company)"""
        response = requests.get(f"{BASE_URL}/api/supplychain/HSBA.L")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # HSBA.L may or may not have supply chain data
        print(f"HSBA.L supply chain: {len(data)} nodes")

    def test_supplychain_bp_l(self):
        """Test supply chain for BP.L (FTSE company)"""
        response = requests.get(f"{BASE_URL}/api/supplychain/BP.L")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Expected supply chain data for BP.L"
        print(f"BP.L supply chain: {len(data)} nodes")

    def test_supplychain_mc_pa(self):
        """Test supply chain for MC.PA (CAC40 - LVMH)"""
        response = requests.get(f"{BASE_URL}/api/supplychain/MC.PA")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Expected supply chain data for MC.PA"
        print(f"MC.PA supply chain: {len(data)} nodes")
        
        # Check subsidiaries (Sephora, Tiffany, etc.)
        names = [n["name"] for n in data]
        print(f"MC.PA supply chain nodes: {names[:5]}")


class TestShareholdersMainAPI:
    """Tests for main shareholders endpoint"""
    
    def test_shareholders_mc_pa(self):
        """Test shareholders data for MC.PA"""
        response = requests.get(f"{BASE_URL}/api/shareholders/MC.PA")
        assert response.status_code == 200
        
        data = response.json()
        assert "symbol" in data
        assert "company_name" in data
        assert "insiders_percent" in data
        assert "institutions_percent" in data
        assert "major_holders" in data
        assert isinstance(data["major_holders"], list)
        
        print(f"MC.PA shareholders - insiders: {data['insiders_percent']}%, institutions: {data['institutions_percent']}%")
        
    def test_shareholders_hsba_l(self):
        """Test shareholders data for HSBA.L"""
        response = requests.get(f"{BASE_URL}/api/shareholders/HSBA.L")
        assert response.status_code == 200
        
        data = response.json()
        assert data["symbol"] == "HSBA.L"
        assert "major_holders" in data
        print(f"HSBA.L shareholders found: {len(data.get('major_holders', []))} major holders")


class TestHistoryChartData:
    """Tests for historical data to verify candlestick chart data"""
    
    def test_history_has_ohlc_data(self):
        """Test that history endpoint returns OHLC data for candlestick charts"""
        response = requests.get(f"{BASE_URL}/api/market/history/MC.PA?period=1mo&interval=1d")
        assert response.status_code == 200
        
        data = response.json()
        assert "symbol" in data
        assert "data" in data
        assert len(data["data"]) > 0, "Expected historical data points"
        
        # Verify OHLC fields
        point = data["data"][0]
        assert "date" in point, "Expected 'date' field"
        assert "open" in point, "Expected 'open' field for candlestick"
        assert "high" in point, "Expected 'high' field for candlestick"
        assert "low" in point, "Expected 'low' field for candlestick"
        assert "close" in point, "Expected 'close' field for candlestick"
        assert "volume" in point, "Expected 'volume' field"
        
        print(f"History data for MC.PA: {len(data['data'])} points with OHLC data")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
