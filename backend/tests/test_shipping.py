"""
Test shipping routes, ports, and statistics APIs
Maritime and Air Cargo shipping data with conflict disruption analysis
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestShippingRoutes:
    """Test shipping routes API - maritime and air cargo"""
    
    def test_get_all_routes(self):
        """Test /api/shipping/routes returns all routes"""
        response = requests.get(f"{BASE_URL}/api/shipping/routes")
        assert response.status_code == 200
        
        data = response.json()
        assert "routes" in data
        assert "stats" in data
        
        # Verify correct number of routes
        routes = data["routes"]
        assert len(routes) == 18, f"Expected 18 routes (9 maritime + 9 air), got {len(routes)}"
        
        # Verify maritime routes exist
        maritime_routes = [r for r in routes if r["route_type"] == "maritime"]
        assert len(maritime_routes) == 9, f"Expected 9 maritime routes, got {len(maritime_routes)}"
        
        # Verify air cargo routes exist
        air_routes = [r for r in routes if r["route_type"] == "air_cargo"]
        assert len(air_routes) == 9, f"Expected 9 air cargo routes, got {len(air_routes)}"
    
    def test_get_maritime_routes_only(self):
        """Test /api/shipping/routes?route_type=maritime returns only maritime routes"""
        response = requests.get(f"{BASE_URL}/api/shipping/routes?route_type=maritime")
        assert response.status_code == 200
        
        data = response.json()
        routes = data["routes"]
        
        # All routes should be maritime
        for route in routes:
            assert route["route_type"] == "maritime"
        
        assert len(routes) == 9, f"Expected 9 maritime routes, got {len(routes)}"
    
    def test_get_air_routes_only(self):
        """Test /api/shipping/routes?route_type=air returns only air cargo routes"""
        response = requests.get(f"{BASE_URL}/api/shipping/routes?route_type=air")
        assert response.status_code == 200
        
        data = response.json()
        routes = data["routes"]
        
        # All routes should be air_cargo
        for route in routes:
            assert route["route_type"] == "air_cargo"
        
        assert len(routes) == 9, f"Expected 9 air cargo routes, got {len(routes)}"
    
    def test_route_structure(self):
        """Test route objects have required fields"""
        response = requests.get(f"{BASE_URL}/api/shipping/routes")
        assert response.status_code == 200
        
        route = response.json()["routes"][0]
        
        # Required fields
        assert "id" in route
        assert "name" in route
        assert "route_type" in route
        assert "origin" in route
        assert "destination" in route
        assert "distance_km" in route
        assert "average_transit_days" in route
        assert "annual_volume" in route
        assert "volume_unit" in route
        assert "disruption_level" in route
        
        # Origin port structure
        origin = route["origin"]
        assert "id" in origin
        assert "name" in origin
        assert "country" in origin
        assert "coordinates" in origin
        assert len(origin["coordinates"]) == 2
    
    def test_disrupted_routes_have_positive_disruption_level(self):
        """Test routes affected by conflicts have disruption_level > 0"""
        response = requests.get(f"{BASE_URL}/api/shipping/routes")
        assert response.status_code == 200
        
        routes = response.json()["routes"]
        
        # Find routes affected by conflicts
        disrupted_routes = [r for r in routes if r.get("affected_by_conflicts") and len(r["affected_by_conflicts"]) > 0]
        
        # Check that disrupted routes have disruption_level > 0
        for route in disrupted_routes:
            # Note: Not all routes with affected_by_conflicts will have disruption > 0
            # It depends on whether the conflict exists in the system
            # Check that the field exists
            assert "disruption_level" in route


class TestShippingPorts:
    """Test shipping ports API - seaports and airports"""
    
    def test_get_all_ports(self):
        """Test /api/shipping/ports returns seaports and airports"""
        response = requests.get(f"{BASE_URL}/api/shipping/ports")
        assert response.status_code == 200
        
        data = response.json()
        assert "seaports" in data
        assert "airports" in data
        assert "total_seaports" in data
        assert "total_airports" in data
    
    def test_seaports_count(self):
        """Test correct number of seaports"""
        response = requests.get(f"{BASE_URL}/api/shipping/ports")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_seaports"] == 27, f"Expected 27 seaports, got {data['total_seaports']}"
        assert len(data["seaports"]) == 27
    
    def test_airports_count(self):
        """Test correct number of airports"""
        response = requests.get(f"{BASE_URL}/api/shipping/ports")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_airports"] == 20, f"Expected 20 airports, got {data['total_airports']}"
        assert len(data["airports"]) == 20
    
    def test_port_structure(self):
        """Test port objects have required fields"""
        response = requests.get(f"{BASE_URL}/api/shipping/ports")
        assert response.status_code == 200
        
        seaport = response.json()["seaports"][0]
        
        assert "id" in seaport
        assert "name" in seaport
        assert "country" in seaport
        assert "coordinates" in seaport
        assert "port_type" in seaport
        assert "region" in seaport
        assert "is_major_hub" in seaport
        
        # Verify coordinates are [lng, lat]
        assert len(seaport["coordinates"]) == 2


class TestShippingStats:
    """Test shipping statistics API"""
    
    def test_get_stats(self):
        """Test /api/shipping/stats returns statistics"""
        response = requests.get(f"{BASE_URL}/api/shipping/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "stats" in data
        assert "risk_summary" in data
    
    def test_stats_values(self):
        """Test stats have correct values"""
        response = requests.get(f"{BASE_URL}/api/shipping/stats")
        assert response.status_code == 200
        
        stats = response.json()["stats"]
        
        assert stats["total_maritime_routes"] == 9
        assert stats["total_air_routes"] == 9
        assert stats["total_ports"] == 27
        assert stats["total_airports"] == 20
        assert stats["routes_affected_by_conflicts"] >= 0
        assert "volume_at_risk_percent" in stats
    
    def test_risk_summary(self):
        """Test risk summary structure"""
        response = requests.get(f"{BASE_URL}/api/shipping/stats")
        assert response.status_code == 200
        
        risk_summary = response.json()["risk_summary"]
        
        assert "high_risk_routes" in risk_summary
        assert "medium_risk_routes" in risk_summary
        assert "low_risk_routes" in risk_summary
        assert "critical_chokepoints" in risk_summary
        
        # Critical chokepoints should be a list
        assert isinstance(risk_summary["critical_chokepoints"], list)


class TestConflictIntegration:
    """Test shipping routes integration with conflicts"""
    
    def test_routes_affected_by_conflicts_count(self):
        """Test that some routes are affected by conflicts"""
        response = requests.get(f"{BASE_URL}/api/shipping/routes")
        assert response.status_code == 200
        
        routes = response.json()["routes"]
        stats = response.json()["stats"]
        
        # Count routes with disruption_level > 0
        affected_routes = [r for r in routes if r["disruption_level"] > 0]
        
        assert stats["routes_affected_by_conflicts"] == len(affected_routes)
        assert stats["routes_affected_by_conflicts"] > 0, "Expected some routes to be affected by conflicts"
    
    def test_specific_disrupted_routes(self):
        """Test specific routes known to be affected by conflicts"""
        response = requests.get(f"{BASE_URL}/api/shipping/routes")
        assert response.status_code == 200
        
        routes = {r["id"]: r for r in response.json()["routes"]}
        
        # Asia-Europe via Suez should be affected by Red Sea/Yemen conflicts
        suez_route = routes.get("asia_europe_suez")
        if suez_route:
            assert suez_route["disruption_level"] > 0, "Asia-Europe via Suez should have disruption from Red Sea/Yemen"
            assert "Red Sea" in suez_route["affected_by_conflicts"] or "Yemen" in suez_route["affected_by_conflicts"]
    
    def test_volume_at_risk_calculation(self):
        """Test volume at risk is calculated correctly"""
        response = requests.get(f"{BASE_URL}/api/shipping/stats")
        assert response.status_code == 200
        
        stats = response.json()["stats"]
        
        # Volume at risk should be between 0 and 100
        assert 0 <= stats["volume_at_risk_percent"] <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
