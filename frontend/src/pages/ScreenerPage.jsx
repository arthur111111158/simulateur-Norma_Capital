import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { ScrollArea } from '../components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Slider } from '../components/ui/slider';
import { 
  Filter, 
  Search, 
  TrendingUp, 
  TrendingDown,
  BarChart3,
  RefreshCw,
  Star
} from 'lucide-react';

const ScreenerPage = () => {
  const { screenAssets, addToWatchlist, watchlist } = useApp();
  const navigate = useNavigate();
  
  const [assetType, setAssetType] = useState('stock');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    minChange: -100,
    maxChange: 100,
    sector: 'all',
  });

  // Fetch screener results
  const fetchResults = async () => {
    setLoading(true);
    try {
      const data = await screenAssets(assetType, {
        min_change: filters.minChange !== -100 ? filters.minChange : undefined,
        max_change: filters.maxChange !== 100 ? filters.maxChange : undefined,
      });
      setResults(data || []);
    } catch (error) {
      console.error('Error fetching screener results:', error);
      setResults([]);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchResults();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assetType]);

  // Check if in watchlist
  const isInWatchlist = (symbol) => watchlist.some(item => item.symbol === symbol);

  // Sort results
  const sortedResults = [...results].sort((a, b) => b.change_percent - a.change_percent);

  // Filter results
  const filteredResults = sortedResults.filter(asset => {
    if (filters.minChange !== -100 && asset.change_percent < filters.minChange) return false;
    if (filters.maxChange !== 100 && asset.change_percent > filters.maxChange) return false;
    return true;
  });

  // Stats
  const stats = {
    total: filteredResults.length,
    gainers: filteredResults.filter(a => a.change_percent > 0).length,
    losers: filteredResults.filter(a => a.change_percent < 0).length,
    avgChange: filteredResults.length > 0 
      ? filteredResults.reduce((sum, a) => sum + a.change_percent, 0) / filteredResults.length 
      : 0
  };

  return (
    <div className="space-y-4" data-testid="screener-page">
      {/* Header */}
      <Card className="nexus-card">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-orange-500/20 rounded-sm flex items-center justify-center">
                <Filter className="w-5 h-5 text-orange-500" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-white">Asset Screener</h1>
                <p className="text-sm text-zinc-500">Filter and discover trading opportunities</p>
              </div>
            </div>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={fetchResults}
              disabled={loading}
              data-testid="refresh-screener-btn"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <Card className="nexus-card">
        <CardContent className="p-4">
          <div className="flex items-center gap-6">
            {/* Asset Type Tabs */}
            <div className="flex-shrink-0">
              <Tabs value={assetType} onValueChange={setAssetType} className="w-auto">
                <TabsList className="bg-zinc-900">
                  <TabsTrigger value="stock" className="text-xs" data-testid="tab-stock">
                    Stocks
                  </TabsTrigger>
                  <TabsTrigger value="commodity" className="text-xs" data-testid="tab-commodity">
                    Commodities
                  </TabsTrigger>
                  <TabsTrigger value="forex" className="text-xs" data-testid="tab-forex">
                    Forex
                  </TabsTrigger>
                </TabsList>
              </Tabs>
            </div>

            <div className="h-8 w-px bg-zinc-800"></div>

            {/* Change Filter */}
            <div className="flex-1 max-w-sm">
              <p className="text-[10px] text-zinc-500 uppercase mb-2">Change % Range</p>
              <div className="flex items-center gap-4">
                <Input
                  type="number"
                  value={filters.minChange}
                  onChange={(e) => setFilters(f => ({ ...f, minChange: parseFloat(e.target.value) || -100 }))}
                  className="w-20 bg-zinc-900 border-zinc-800 text-xs h-8"
                  placeholder="Min"
                />
                <span className="text-zinc-500">to</span>
                <Input
                  type="number"
                  value={filters.maxChange}
                  onChange={(e) => setFilters(f => ({ ...f, maxChange: parseFloat(e.target.value) || 100 }))}
                  className="w-20 bg-zinc-900 border-zinc-800 text-xs h-8"
                  placeholder="Max"
                />
              </div>
            </div>

            {/* Quick Filters */}
            <div className="flex items-center gap-2">
              <Button
                variant={filters.minChange === 0 ? 'default' : 'outline'}
                size="sm"
                className="text-xs"
                onClick={() => setFilters(f => ({ ...f, minChange: 0, maxChange: 100 }))}
              >
                <TrendingUp className="w-3 h-3 mr-1" /> Gainers Only
              </Button>
              <Button
                variant={filters.maxChange === 0 ? 'default' : 'outline'}
                size="sm"
                className="text-xs"
                onClick={() => setFilters(f => ({ ...f, minChange: -100, maxChange: 0 }))}
              >
                <TrendingDown className="w-3 h-3 mr-1" /> Losers Only
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="text-xs"
                onClick={() => setFilters({ minChange: -100, maxChange: 100, sector: 'all' })}
              >
                Reset
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats Bar */}
      <Card className="nexus-card">
        <CardContent className="p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-6">
              <div>
                <p className="text-[10px] text-zinc-500 uppercase">Total Results</p>
                <p className="font-mono text-lg text-white">{stats.total}</p>
              </div>
              <div>
                <p className="text-[10px] text-zinc-500 uppercase">Gainers</p>
                <p className="font-mono text-lg text-emerald-500">{stats.gainers}</p>
              </div>
              <div>
                <p className="text-[10px] text-zinc-500 uppercase">Losers</p>
                <p className="font-mono text-lg text-red-500">{stats.losers}</p>
              </div>
              <div>
                <p className="text-[10px] text-zinc-500 uppercase">Avg Change</p>
                <p className={`font-mono text-lg ${stats.avgChange >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                  {stats.avgChange >= 0 ? '+' : ''}{stats.avgChange.toFixed(2)}%
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results Table */}
      <Card className="nexus-card">
        <CardHeader className="card-header-terminal">
          <CardTitle className="card-header-title flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-orange-500" />
            Screener Results
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-[calc(100vh-450px)]">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="w-8"></th>
                  <th>Symbol</th>
                  <th>Name</th>
                  <th>Price</th>
                  <th>Change</th>
                  <th>Change %</th>
                  <th>Volume</th>
                  <th>Market Cap</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={8} className="text-center py-8">
                      <div className="w-6 h-6 border-2 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                      <p className="text-zinc-500 text-sm mt-2">Loading...</p>
                    </td>
                  </tr>
                ) : filteredResults.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="text-center py-8 text-zinc-500">
                      No results found with current filters
                    </td>
                  </tr>
                ) : (
                  filteredResults.map((asset, i) => {
                    const isPositive = asset.change_percent >= 0;
                    const inWatchlist = isInWatchlist(asset.symbol);
                    
                    return (
                      <tr 
                        key={asset.symbol || i}
                        className="cursor-pointer"
                        onClick={() => navigate(`/quote?symbol=${asset.symbol}`)}
                        data-testid={`screener-row-${asset.symbol}`}
                      >
                        <td>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 w-6 p-0"
                            onClick={(e) => {
                              e.stopPropagation();
                              if (!inWatchlist) {
                                addToWatchlist(asset.symbol, asset.name, asset.asset_type);
                              }
                            }}
                          >
                            <Star className={`w-3 h-3 ${inWatchlist ? 'text-yellow-500 fill-yellow-500' : 'text-zinc-600'}`} />
                          </Button>
                        </td>
                        <td>
                          <span className="font-mono text-white font-medium">{asset.symbol}</span>
                        </td>
                        <td>
                          <span className="text-zinc-400 text-xs truncate max-w-[150px] block">{asset.name}</span>
                        </td>
                        <td>
                          <span className="font-mono text-white">{asset.price?.toFixed(2)}</span>
                        </td>
                        <td>
                          <span className={`font-mono ${isPositive ? 'text-emerald-500' : 'text-red-500'}`}>
                            {isPositive ? '+' : ''}{asset.change?.toFixed(2)}
                          </span>
                        </td>
                        <td>
                          <Badge 
                            className={`rounded-none font-mono ${isPositive ? 'bg-emerald-500/20 text-emerald-500' : 'bg-red-500/20 text-red-500'}`}
                          >
                            {isPositive ? '+' : ''}{asset.change_percent?.toFixed(2)}%
                          </Badge>
                        </td>
                        <td>
                          <span className="font-mono text-zinc-400">
                            {asset.volume ? (asset.volume / 1e6).toFixed(2) + 'M' : '—'}
                          </span>
                        </td>
                        <td>
                          <span className="font-mono text-zinc-400">
                            {asset.market_cap ? '$' + (asset.market_cap / 1e9).toFixed(2) + 'B' : '—'}
                          </span>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
};

export default ScreenerPage;
