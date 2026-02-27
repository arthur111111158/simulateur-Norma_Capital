"""
Test suite for Country Data API - Economic and Demographic Data
Tests for:
- Country data by ISO code (/api/country/{code})
- Country search (/api/country/search/{query})
- Countries list (/api/countries/list)
- Response structure and data validation
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestCountryDataAPI:
    """Tests for country data endpoints - economic and demographic info"""

    def test_get_france_country_data(self):
        """Test /api/country/FR returns France with complete data"""
        response = requests.get(f"{BASE_URL}/api/country/FR", timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Verify basic info
        assert "basic" in data, "Missing 'basic' field"
        assert data["basic"]["name"] == "France", f"Expected France, got {data['basic'].get('name')}"
        assert data["basic"]["iso_code"] == "FR", "ISO code should be FR"
        assert data["basic"]["region"] == "Europe", "France should be in Europe"
        assert data["basic"]["capital"] == "Paris", "Capital should be Paris"
        
        # Verify economic data exists
        assert "economic" in data, "Missing 'economic' field"
        assert data["economic"]["gdp"] is not None, "GDP should not be None"
        assert data["economic"]["gdp"] > 0, "GDP should be positive"
        assert data["economic"]["currency_code"] == "EUR", "Currency should be EUR"
        
        # Verify demographic data exists
        assert "demographic" in data, "Missing 'demographic' field"
        assert data["demographic"]["population"] is not None, "Population should not be None"
        assert data["demographic"]["population"] > 60000000, "France population should be > 60M"
        print(f"✓ France data returned successfully: GDP={data['economic']['gdp']:.2e}, Pop={data['demographic']['population']:,}")

    def test_get_us_country_data(self):
        """Test /api/country/US returns United States data"""
        response = requests.get(f"{BASE_URL}/api/country/US", timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        assert data["basic"]["name"] == "United States"
        assert data["basic"]["iso_code"] == "US"
        assert data["basic"]["region"] == "Americas"
        assert data["basic"]["capital"] == "Washington, D.C."
        
        # Economic validation
        assert data["economic"]["gdp"] is not None
        assert data["economic"]["gdp"] > 20e12, "US GDP should be > $20T"
        assert data["economic"]["gdp_per_capita"] is not None
        assert data["economic"]["currency_code"] == "USD"
        
        # Demographic validation
        assert data["demographic"]["population"] > 300000000, "US population > 300M"
        print(f"✓ US data returned: GDP=${data['economic']['gdp']:.2e}, GDP/capita=${data['economic']['gdp_per_capita']:.0f}")

    def test_get_china_country_data(self):
        """Test /api/country/CN returns China data"""
        response = requests.get(f"{BASE_URL}/api/country/CN", timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        assert data["basic"]["name"] == "China"
        assert data["basic"]["iso_code"] == "CN"
        assert data["basic"]["region"] == "Asia"
        assert data["basic"]["capital"] == "Beijing"
        
        # China economic checks
        assert data["economic"]["gdp"] is not None
        assert data["economic"]["gdp"] > 10e12, "China GDP should be > $10T"
        assert data["economic"]["currency_code"] == "CNY"
        
        # Demographics
        assert data["demographic"]["population"] > 1e9, "China population > 1B"
        print(f"✓ China data returned: Pop={data['demographic']['population']:,}")

    def test_get_japan_country_data(self):
        """Test /api/country/JP returns Japan data"""
        response = requests.get(f"{BASE_URL}/api/country/JP", timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        assert data["basic"]["name"] == "Japan"
        assert data["basic"]["iso_code"] == "JP"
        assert data["basic"]["capital"] == "Tokyo"
        assert data["basic"]["region"] == "Asia"
        
        # Economic
        assert data["economic"]["gdp"] is not None
        assert data["economic"]["currency_code"] == "JPY"
        
        # Demographic - Japan has high life expectancy
        assert data["demographic"]["life_expectancy"] is not None
        assert data["demographic"]["life_expectancy"] > 80, "Japan life expectancy > 80"
        print(f"✓ Japan data returned: Life Exp={data['demographic']['life_expectancy']:.1f} years")

    def test_country_data_structure_complete(self):
        """Test that country data has all required fields in structure"""
        response = requests.get(f"{BASE_URL}/api/country/DE", timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        
        # Check basic info fields
        basic_required = ["name", "official_name", "iso_code", "region", "capital", "flag_url", "area"]
        for field in basic_required:
            assert field in data["basic"], f"Missing basic field: {field}"
        
        # Check economic fields
        economic_required = ["gdp", "gdp_per_capita", "gdp_growth", "inflation", "unemployment", 
                           "exports", "imports", "fdi_inflow", "currency", "currency_code"]
        for field in economic_required:
            assert field in data["economic"], f"Missing economic field: {field}"
        
        # Check demographic fields
        demographic_required = ["population", "population_growth", "population_density",
                               "life_expectancy", "urban_population_percent", "fertility_rate", "hdi"]
        for field in demographic_required:
            assert field in data["demographic"], f"Missing demographic field: {field}"
        
        print("✓ All required fields present in country data structure")

    def test_economic_data_values(self):
        """Test that economic indicators have realistic values"""
        response = requests.get(f"{BASE_URL}/api/country/GB", timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        econ = data["economic"]
        
        # GDP should be positive if present
        if econ["gdp"] is not None:
            assert econ["gdp"] > 0, "GDP should be positive"
        
        # GDP per capita should be positive if present
        if econ["gdp_per_capita"] is not None:
            assert econ["gdp_per_capita"] > 0, "GDP per capita should be positive"
        
        # Unemployment typically 0-30%
        if econ["unemployment"] is not None:
            assert 0 <= econ["unemployment"] <= 50, f"Unemployment {econ['unemployment']}% seems invalid"
        
        print(f"✓ UK economic data validated: GDP={econ['gdp']}, Unemployment={econ['unemployment']}%")

    def test_demographic_data_values(self):
        """Test that demographic data has realistic values"""
        response = requests.get(f"{BASE_URL}/api/country/IN", timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        demo = data["demographic"]
        
        # Population should be positive
        assert demo["population"] is not None and demo["population"] > 0
        
        # Life expectancy typically 40-95
        if demo["life_expectancy"] is not None:
            assert 40 <= demo["life_expectancy"] <= 100, f"Life expectancy {demo['life_expectancy']} seems invalid"
        
        # Urban population 0-100%
        if demo["urban_population_percent"] is not None:
            assert 0 <= demo["urban_population_percent"] <= 100
        
        # HDI 0-1
        if demo["hdi"] is not None:
            assert 0 <= demo["hdi"] <= 1, f"HDI {demo['hdi']} should be 0-1"
        
        print(f"✓ India demographic data validated: Pop={demo['population']:,}, HDI={demo.get('hdi')}")


class TestCountrySearchAPI:
    """Tests for country search endpoint"""

    def test_search_germany(self):
        """Test /api/country/search/germany returns search results"""
        response = requests.get(f"{BASE_URL}/api/country/search/germany", timeout=15)
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data, "Response should have 'results' field"
        assert len(data["results"]) > 0, "Should find at least one result for 'germany'"
        
        # Verify Germany is in results
        germany = data["results"][0]
        assert germany["name"] == "Germany"
        assert germany["iso_code"] == "DE"
        assert germany["region"] == "Europe"
        assert germany["flag_url"] is not None
        print(f"✓ Search for 'germany' returned {len(data['results'])} result(s)")

    def test_search_partial_name(self):
        """Test search with partial country name"""
        response = requests.get(f"{BASE_URL}/api/country/search/braz", timeout=15)
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        # Should find Brazil with partial match
        print(f"✓ Partial search 'braz' returned {len(data['results'])} result(s)")

    def test_search_empty_results(self):
        """Test search with non-existent country returns empty results"""
        response = requests.get(f"{BASE_URL}/api/country/search/xyzcountry123", timeout=15)
        assert response.status_code == 200
        
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 0, "Should return empty results for non-existent country"
        print("✓ Search for non-existent country returns empty results")


class TestCountriesListAPI:
    """Tests for countries list endpoint"""

    def test_get_countries_list(self):
        """Test /api/countries/list returns list of all countries"""
        response = requests.get(f"{BASE_URL}/api/countries/list", timeout=20)
        assert response.status_code == 200
        
        data = response.json()
        assert "countries" in data, "Response should have 'countries' field"
        assert "total" in data, "Response should have 'total' field"
        assert data["total"] > 200, f"Should have > 200 countries, got {data['total']}"
        
        # Verify structure of country entry
        if len(data["countries"]) > 0:
            country = data["countries"][0]
            assert "name" in country
            assert "iso_code" in country
            assert "region" in country
            assert "flag_url" in country
        
        print(f"✓ Countries list returned {data['total']} countries")

    def test_countries_list_structure(self):
        """Test countries list entry structure"""
        response = requests.get(f"{BASE_URL}/api/countries/list", timeout=20)
        assert response.status_code == 200
        
        data = response.json()
        required_fields = ["name", "iso_code", "iso_code_3", "region", "subregion", "flag_url", "population", "area"]
        
        for country in data["countries"][:5]:
            for field in required_fields:
                assert field in country, f"Missing field '{field}' in country entry"
        
        print("✓ Countries list entries have all required fields")

    def test_countries_list_sorted(self):
        """Test countries list is sorted alphabetically"""
        response = requests.get(f"{BASE_URL}/api/countries/list", timeout=20)
        assert response.status_code == 200
        
        data = response.json()
        names = [c["name"] for c in data["countries"] if c["name"]]
        
        # Check if sorted (case-insensitive)
        sorted_names = sorted(names, key=lambda x: x.lower())
        assert names == sorted_names, "Countries list should be sorted alphabetically"
        print("✓ Countries list is sorted alphabetically")


class TestCountryNotFound:
    """Tests for error handling"""

    def test_invalid_country_code(self):
        """Test that invalid country code returns 404"""
        response = requests.get(f"{BASE_URL}/api/country/XX", timeout=30)
        assert response.status_code == 404, f"Expected 404 for invalid code, got {response.status_code}"
        print("✓ Invalid country code returns 404")

    def test_nonexistent_country(self):
        """Test that non-existent country returns 404"""
        response = requests.get(f"{BASE_URL}/api/country/ZZ", timeout=30)
        assert response.status_code == 404
        print("✓ Non-existent country returns 404")


class TestCountryBasicInfoFields:
    """Specific tests for basic info fields"""

    def test_flag_url_valid(self):
        """Test that flag URL is valid for countries"""
        response = requests.get(f"{BASE_URL}/api/country/CA", timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        flag_url = data["basic"]["flag_url"]
        assert flag_url is not None, "Flag URL should not be None"
        assert flag_url.startswith("http"), f"Flag URL should be a valid URL: {flag_url}"
        print(f"✓ Canada flag URL: {flag_url}")

    def test_currency_info(self):
        """Test currency information is present"""
        response = requests.get(f"{BASE_URL}/api/country/AU", timeout=30)
        assert response.status_code == 200
        
        data = response.json()
        assert data["economic"]["currency_code"] == "AUD", "Australia currency should be AUD"
        assert data["economic"]["currency"] is not None
        print(f"✓ Australia currency: {data['economic']['currency']} ({data['economic']['currency_code']})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
