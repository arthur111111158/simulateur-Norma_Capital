import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Tabs, TabsList, TabsTrigger } from '../components/ui/tabs';
import { ScrollArea } from '../components/ui/scroll-area';
import { 
  Gem, 
  Fuel, 
  Wheat, 
  Factory,
  TrendingUp, 
  TrendingDown,
  RefreshCw,
  Loader2
} from 'lucide-react';

const CommoditiesPage = () => {
  const navigate = useNavigate();
  const { getCommodities, getHistory } = useApp();
  const [commodities, setCommodities] = useState([]);
  const [categories, setCategories] = useState({});
  const [activeCategory, setActiveCategory] = useState('all');
  const [loading, setLoading] = useState(true);
  const [selectedCommodity, setSelectedCommodity] = useState(null);

  // Load commodities
  useEffect(() => {
    const loadCommodities = async () => {
      setLoading(true);
      const data = await getCommodities();
      setCommodities(data.commodities || []);
      setCategories(data.by_category || {});
      setLoading(false);
    };
    loadCommodities();
  }, [getCommodities]);

  // Refresh data
  const refreshData = async () => {
    setLoading(true);
    const data = await getCommodities();
    setCommodities(data.commodities || []);
    setCategories(data.by_category || {});
    setLoading(false);
  };

  // Get category icon
  const getCategoryIcon = (category) => {
    switch (category) {
      case 'Precious Metals': return Gem;
      case 'Energy': return Fuel;
      case 'Agriculture': return Wheat;
      case 'Industrial Metals': return Factory;
      default: return Gem;
    }
  };

  // Get category color
  const getCategoryColor = (category) => {
    switch (category) {
      case 'Precious Metals': return 'text-yellow-500';
      case 'Energy': return 'text-orange-500';
      case 'Agriculture': return 'text-green-500';
      case 'Industrial Metals': return 'text-blue-500';
      default: return 'text-zinc-400';
    }
  };

  // Format price
  const formatPrice = (price, currency = 'USD') => {
    if (price === null || price === undefined) return '—';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(price);
  };

  // Filter commodities by category
  const filteredCommodities = activeCategory === 'all' 
    ? commodities 
    : commodities.filter(c => c.category === activeCategory);

  // Calculate category stats
  const getCategoryStats = (category) => {
    const items = categories[category] || [];
    const gainers = items.filter(i => i.change_percent > 0).length;
    const losers = items.filter(i => i.change_percent < 0).length;
    return { total: items.length, gainers, losers };
  };

  return (
    <div className="space-y-4" data-testid="commodities-page">
      {/* Header */}
      <Card className="nexus-card">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-yellow-500/20 rounded-sm flex items-center justify-center">
                <Gem className="w-5 h-5 text-yellow-500" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-white">Commodities</h1>
                <p className="text-sm text-zinc-500">Real-time commodity prices and trends</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={refreshData}
                disabled={loading}
                className="h-8"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <div className="px-3 py-1.5 bg-zinc-800 rounded-sm">
                <span className="text-zinc-400 font-mono text-sm">
                  {commodities.length} COMMODITIES
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Category Tabs */}
      <Tabs value={activeCategory} onValueChange={setActiveCategory}>
        <TabsList className="bg-zinc-900 h-10 p-1">
          <TabsTrigger 
            value="all" 
            className="text-xs px-4 data-[state=active]:bg-zinc-800"
            data-testid="category-all"
          >
            All ({commodities.length})
          </TabsTrigger>
          {Object.keys(categories).map(category => {
            const Icon = getCategoryIcon(category);
            const stats = getCategoryStats(category);
            return (
              <TabsTrigger 
                key={category}
                value={category}
                className="text-xs px-4 data-[state=active]:bg-zinc-800"
                data-testid={`category-${category.replace(/\s+/g, '-').toLowerCase()}`}
              >
                <Icon className={`w-3 h-3 mr-1.5 ${getCategoryColor(category)}`} />
                {category} ({stats.total})
              </TabsTrigger>
            );
          })}
        </TabsList>
      </Tabs>

      {/* Main Content */}
      <div className="grid grid-cols-12 gap-4">
        {/* Commodities List */}
        <div className="col-span-8">
          <Card className="nexus-card">
            <CardHeader className="card-header-terminal">
              <CardTitle className="card-header-title">
                {activeCategory === 'all' ? 'All Commodities' : activeCategory}
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {loading ? (
                <div className="flex items-center justify-center h-64">
                  <Loader2 className="w-6 h-6 animate-spin text-yellow-500" />
                </div>
              ) : (
                <ScrollArea className="h-[600px]">
                  <div className="divide-y divide-zinc-800/50">
                    {filteredCommodities.map((commodity, i) => {
                      const Icon = getCategoryIcon(commodity.category);
                      const isPositive = commodity.change_percent >= 0;
                      const isSelected = selectedCommodity?.symbol === commodity.symbol;
                      
                      return (
                        <div 
                          key={commodity.symbol}
                          className={`p-4 hover:bg-zinc-800/30 cursor-pointer transition-colors ${isSelected ? 'bg-zinc-800/50' : ''}`}
                          onClick={() => setSelectedCommodity(commodity)}
                          data-testid={`commodity-${commodity.symbol}`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <div className={`w-10 h-10 rounded-sm flex items-center justify-center bg-zinc-800`}>
                                <Icon className={`w-5 h-5 ${getCategoryColor(commodity.category)}`} />
                              </div>
                              <div>
                                <h3 className="font-medium text-white">{commodity.name}</h3>
                                <div className="flex items-center gap-2 mt-0.5">
                                  <span className="text-xs text-zinc-500">{commodity.symbol}</span>
                                  <Badge className={`rounded-none text-[9px] ${getCategoryColor(commodity.category)} bg-opacity-20`}>
                                    {commodity.category}
                                  </Badge>
                                </div>
                              </div>
                            </div>
                            
                            <div className="text-right">
                              <p className="font-mono text-lg text-white">
                                {formatPrice(commodity.price, commodity.currency)}
                              </p>
                              <div className="flex items-center justify-end gap-2 mt-0.5">
                                <span className={`font-mono text-sm ${isPositive ? 'text-emerald-500' : 'text-red-500'}`}>
                                  {isPositive ? '+' : ''}{commodity.change?.toFixed(2)}
                                </span>
                                <Badge className={`rounded-none text-xs ${isPositive ? 'bg-emerald-500/20 text-emerald-500' : 'bg-red-500/20 text-red-500'}`}>
                                  {isPositive ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                                  {isPositive ? '+' : ''}{commodity.change_percent?.toFixed(2)}%
                                </Badge>
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar - Selected Commodity Details */}
        <div className="col-span-4 space-y-4">
          {selectedCommodity ? (
            <Card className="nexus-card border-yellow-500/30">
              <CardHeader className="card-header-terminal">
                <CardTitle className="card-header-title flex items-center gap-2">
                  {React.createElement(getCategoryIcon(selectedCommodity.category), {
                    className: `w-4 h-4 ${getCategoryColor(selectedCommodity.category)}`
                  })}
                  {selectedCommodity.name}
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4">
                <div className="space-y-4">
                  {/* Price */}
                  <div className="text-center py-4 bg-zinc-900 rounded-sm">
                    <p className="font-mono text-3xl text-white">
                      {formatPrice(selectedCommodity.price, selectedCommodity.currency)}
                    </p>
                    <div className="flex items-center justify-center gap-2 mt-2">
                      <span className={`font-mono text-lg ${selectedCommodity.change_percent >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                        {selectedCommodity.change_percent >= 0 ? '+' : ''}{selectedCommodity.change?.toFixed(2)}
                      </span>
                      <Badge className={`rounded-none ${selectedCommodity.change_percent >= 0 ? 'bg-emerald-500/20 text-emerald-500' : 'bg-red-500/20 text-red-500'}`}>
                        {selectedCommodity.change_percent >= 0 ? '+' : ''}{selectedCommodity.change_percent?.toFixed(2)}%
                      </Badge>
                    </div>
                  </div>

                  {/* Details */}
                  <div className="space-y-2">
                    <div className="flex justify-between items-center py-2 border-b border-zinc-800/50">
                      <span className="text-sm text-zinc-400">Open</span>
                      <span className="font-mono text-sm text-white">{formatPrice(selectedCommodity.open)}</span>
                    </div>
                    <div className="flex justify-between items-center py-2 border-b border-zinc-800/50">
                      <span className="text-sm text-zinc-400">High</span>
                      <span className="font-mono text-sm text-emerald-500">{formatPrice(selectedCommodity.high)}</span>
                    </div>
                    <div className="flex justify-between items-center py-2 border-b border-zinc-800/50">
                      <span className="text-sm text-zinc-400">Low</span>
                      <span className="font-mono text-sm text-red-500">{formatPrice(selectedCommodity.low)}</span>
                    </div>
                    <div className="flex justify-between items-center py-2 border-b border-zinc-800/50">
                      <span className="text-sm text-zinc-400">Prev. Close</span>
                      <span className="font-mono text-sm text-white">{formatPrice(selectedCommodity.previous_close)}</span>
                    </div>
                    <div className="flex justify-between items-center py-2 border-b border-zinc-800/50">
                      <span className="text-sm text-zinc-400">Currency</span>
                      <span className="font-mono text-sm text-white">{selectedCommodity.currency}</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <Button 
                    className="w-full bg-yellow-500/20 text-yellow-500 hover:bg-yellow-500/30"
                    onClick={() => navigate(`/quote?symbol=${selectedCommodity.symbol}`)}
                  >
                    View Full Chart
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="nexus-card">
              <CardContent className="p-8">
                <div className="text-center text-zinc-500">
                  <Gem className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Select a commodity to view details</p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Category Overview */}
          <Card className="nexus-card">
            <CardHeader className="card-header-terminal">
              <CardTitle className="card-header-title">Category Overview</CardTitle>
            </CardHeader>
            <CardContent className="p-3">
              <div className="space-y-3">
                {Object.keys(categories).map(category => {
                  const stats = getCategoryStats(category);
                  const Icon = getCategoryIcon(category);
                  return (
                    <div 
                      key={category}
                      className="flex items-center justify-between p-2 bg-zinc-900 rounded-sm"
                    >
                      <div className="flex items-center gap-2">
                        <Icon className={`w-4 h-4 ${getCategoryColor(category)}`} />
                        <span className="text-sm text-white">{category}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className="bg-emerald-500/20 text-emerald-500 rounded-none text-[10px]">
                          {stats.gainers} up
                        </Badge>
                        <Badge className="bg-red-500/20 text-red-500 rounded-none text-[10px]">
                          {stats.losers} down
                        </Badge>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default CommoditiesPage;
