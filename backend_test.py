#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class BloombergTerminalAPITester:
    def __init__(self, base_url="https://market-terminal-8.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []

    def run_test(self, name, method, endpoint, expected_status=200, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, list) and len(response_data) > 0:
                        print(f"   Response contains {len(response_data)} items")
                    elif isinstance(response_data, dict):
                        print(f"   Response keys: {list(response_data.keys())}")
                except:
                    print(f"   Response length: {len(response.text)}")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                self.failed_tests.append({
                    'name': name, 
                    'endpoint': endpoint, 
                    'expected': expected_status, 
                    'actual': response.status_code,
                    'error': response.text[:200]
                })

            return success, response.json() if success and response.text else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                'name': name, 
                'endpoint': endpoint, 
                'expected': expected_status, 
                'actual': 'Exception',
                'error': str(e)
            })
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, response = self.run_test("Root API", "GET", "")
        return success

    def test_market_quotes(self):
        """Test market quote endpoints"""
        # Test single quote
        success1, response1 = self.run_test("Get AAPL Quote", "GET", "market/quote/AAPL")
        
        # Test multiple quotes
        success2, response2 = self.run_test("Get Multiple Quotes", "GET", "market/quotes", params={'symbols': 'AAPL,MSFT,GOOGL'})
        
        # Test invalid quote
        success3, response3 = self.run_test("Get Invalid Quote", "GET", "market/quote/INVALID", expected_status=404)
        
        return success1 and success2 and success3

    def test_historical_data(self):
        """Test historical data endpoint"""
        success1, response1 = self.run_test("Get AAPL History (1mo)", "GET", "market/history/AAPL", params={'period': '1mo', 'interval': '1d'})
        
        success2, response2 = self.run_test("Get AAPL History (5d)", "GET", "market/history/AAPL", params={'period': '5d', 'interval': '30m'})
        
        return success1 and success2

    def test_market_search(self):
        """Test market asset search"""
        success1, response1 = self.run_test("Search Assets (Apple)", "GET", "market/search", params={'q': 'Apple'})
        
        success2, response2 = self.run_test("Search Assets (AAPL)", "GET", "market/search", params={'q': 'AAPL'})
        
        return success1 and success2

    def test_market_movers(self):
        """Test market movers endpoint"""
        success, response = self.run_test("Get Market Movers", "GET", "market/movers")
        
        if success and response:
            if 'gainers' in response and 'losers' in response:
                print(f"   Gainers: {len(response.get('gainers', []))}")
                print(f"   Losers: {len(response.get('losers', []))}")
            else:
                print("   Warning: Response missing gainers/losers structure")
                
        return success

    def test_news_endpoints(self):
        """Test news endpoints"""
        success1, response1 = self.run_test("Get News", "GET", "news")
        
        success2, response2 = self.run_test("Get Breaking News", "GET", "news/breaking")
        
        success3, response3 = self.run_test("Get News with Query", "GET", "news", params={'q': 'Apple', 'page_size': 5})
        
        return success1 and success2 and success3

    def test_conflicts_endpoints(self):
        """Test geopolitical conflicts endpoints"""
        success1, response1 = self.run_test("Get Conflicts", "GET", "conflicts")
        
        if success1 and response1:
            if len(response1) > 0:
                # Try to get detail for first conflict
                first_conflict_id = response1[0].get('id')
                if first_conflict_id:
                    success2, response2 = self.run_test("Get Conflict Detail", "GET", f"conflicts/{first_conflict_id}")
                    return success1 and success2
                else:
                    print("   Warning: Conflict missing ID field")
                    
        return success1

    def test_supply_chain_endpoints(self):
        """Test supply chain endpoints"""
        success1, response1 = self.run_test("Get AAPL Supply Chain", "GET", "supplychain/AAPL")
        
        success2, response2 = self.run_test("Get TSLA Supply Chain", "GET", "supplychain/TSLA")
        
        success3, response3 = self.run_test("Get NVDA Supply Chain", "GET", "supplychain/NVDA")
        
        # Test empty supply chain
        success4, response4 = self.run_test("Get Unknown Supply Chain", "GET", "supplychain/UNKNOWN")
        
        return success1 and success2 and success3

    def test_watchlist_endpoints(self):
        """Test watchlist CRUD operations"""
        # Get current watchlist
        success1, response1 = self.run_test("Get Watchlist", "GET", "watchlist")
        
        # Add to watchlist
        watchlist_item = {
            "symbol": "AAPL", 
            "name": "Apple Inc.", 
            "asset_type": "stock"
        }
        success2, response2 = self.run_test("Add to Watchlist", "POST", "watchlist", expected_status=200, data=watchlist_item)
        
        # Remove from watchlist
        success3, response3 = self.run_test("Remove from Watchlist", "DELETE", "watchlist/AAPL", expected_status=200)
        
        return success1 and success2 and success3

    def test_screener_endpoints(self):
        """Test asset screener"""
        success1, response1 = self.run_test("Screen Stocks", "GET", "screener", params={'asset_type': 'stock'})
        
        success2, response2 = self.run_test("Screen Commodities", "GET", "screener", params={'asset_type': 'commodity'})
        
        success3, response3 = self.run_test("Screen Forex", "GET", "screener", params={'asset_type': 'forex'})
        
        success4, response4 = self.run_test("Screen with Filters", "GET", "screener", params={'asset_type': 'stock', 'min_change': '-5', 'max_change': '5'})
        
        return success1 and success2 and success3 and success4

    def print_summary(self):
        """Print test results summary"""
        print(f"\n{'='*60}")
        print(f"📊 BLOOMBERG TERMINAL API TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed / self.tests_run * 100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in self.failed_tests:
                print(f"   - {test['name']}: Expected {test['expected']}, got {test['actual']}")
                print(f"     Endpoint: {test['endpoint']}")
                print(f"     Error: {test['error']}")
        
        return self.tests_passed == self.tests_run

def main():
    print("🚀 Starting Bloomberg Terminal API Tests")
    print("=" * 60)
    
    tester = BloombergTerminalAPITester()
    
    # Run all test suites
    test_suites = [
        ("Root Endpoint", tester.test_root_endpoint),
        ("Market Quotes", tester.test_market_quotes),
        ("Historical Data", tester.test_historical_data),
        ("Market Search", tester.test_market_search),
        ("Market Movers", tester.test_market_movers),
        ("News Endpoints", tester.test_news_endpoints),
        ("Conflicts Endpoints", tester.test_conflicts_endpoints),
        ("Supply Chain Endpoints", tester.test_supply_chain_endpoints),
        ("Watchlist Endpoints", tester.test_watchlist_endpoints),
        ("Screener Endpoints", tester.test_screener_endpoints),
    ]
    
    suite_results = []
    
    for suite_name, test_func in test_suites:
        print(f"\n📋 Running {suite_name} Tests...")
        print("-" * 40)
        
        try:
            result = test_func()
            suite_results.append((suite_name, result))
            if result:
                print(f"✅ {suite_name} - All tests passed")
            else:
                print(f"❌ {suite_name} - Some tests failed")
        except Exception as e:
            print(f"💥 {suite_name} - Test suite crashed: {e}")
            suite_results.append((suite_name, False))
    
    # Print final summary
    all_passed = tester.print_summary()
    
    print(f"\n📋 TEST SUITE RESULTS:")
    for suite_name, result in suite_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} - {suite_name}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())