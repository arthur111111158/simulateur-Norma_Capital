import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { ScrollArea } from '../components/ui/scroll-area';
import { 
  Search, 
  Star, 
  StarOff, 
  TrendingUp, 
  TrendingDown, 
  ArrowRight,
  Clock,
  BarChart3,
  GitBranch,
  Newspaper,
  Activity,
  AlertTriangle,
  Target,
  BarChart2,
  Users,
  Building2,
  Landmark,
  UserCircle
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, 
  AreaChart, Area, CartesianGrid, Bar, BarChart,
  PieChart, Pie, Cell
} from 'recharts';
import OptionsChain from '../components/OptionsChain';

const QuotePage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { getQuote, getHistory, getSupplyChain, searchAssets, addToWatchlist, watchlist, removeFromWatchlist, news, getTechnicalIndicators, getImpactScore } = useApp();
  
  const [symbol, setSymbol] = useState(searchParams.get('symbol') || 'AAPL');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [quote, setQuote] = useState(null);
  const [history, setHistory] = useState(null);
  const [supplyChain, setSupplyChain] = useState([]);
  const [technicals, setTechnicals] = useState(null);
  const [impactScore, setImpactScore] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('1mo');
  const [interval, setIntervalState] = useState('1d');

  // Check if in watchlist
  const isInWatchlist = watchlist.some(item => item.symbol === symbol);

  // Fetch data
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      const [quoteData, historyData, supplyChainData, techData, impactData] = await Promise.all([
        getQuote(symbol),
        getHistory(symbol, period, interval),
        getSupplyChain(symbol),
        getTechnicalIndicators(symbol),
        getImpactScore(symbol)
      ]);
      
      setQuote(quoteData);
      setHistory(historyData);
      setSupplyChain(supplyChainData);
      setTechnicals(techData);
      setImpactScore(impactData);
      setLoading(false);
    };
    
    if (symbol) {
      fetchData();
    }
  }, [symbol, period, interval, getQuote, getHistory, getSupplyChain, getTechnicalIndicators, getImpactScore]);

  // Handle search
  useEffect(() => {
    const search = async () => {
      if (searchQuery.length > 0) {
        const results = await searchAssets(searchQuery);
        setSearchResults(results);
      } else {
        setSearchResults([]);
      }
    };
    const debounce = setTimeout(search, 300);
    return () => clearTimeout(debounce);
  }, [searchQuery, searchAssets]);

  // Select asset
  const handleSelectAsset = (asset) => {
    setSymbol(asset.symbol);
    setSearchQuery('');
    setSearchResults([]);
    navigate(`/quote?symbol=${asset.symbol}`);
  };

  // Toggle watchlist
  const handleWatchlistToggle = () => {
    if (isInWatchlist) {
      removeFromWatchlist(symbol);
    } else {
      addToWatchlist(symbol, quote?.name || symbol, quote?.asset_type || 'stock');
    }
  };

  // Period buttons
  const periods = [
    { value: '1d', label: '1D', interval: '5m' },
    { value: '5d', label: '5D', interval: '30m' },
    { value: '1mo', label: '1M', interval: '1d' },
    { value: '3mo', label: '3M', interval: '1d' },
    { value: '1y', label: '1Y', interval: '1wk' },
    { value: '5y', label: '5Y', interval: '1mo' },
  ];

  const isPositive = quote?.change >= 0;

  // Related news
  const relatedNews = news.filter(article => 
    article.tags?.some(tag => tag.toUpperCase() === symbol.toUpperCase()) || 
    article.title?.toLowerCase().includes(symbol.toLowerCase())
  ).slice(0, 5);

  if (loading && !quote) {
    return (
      <div className="flex items-center justify-center h-[80vh]">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-zinc-500 text-sm mt-4">Loading quote data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="quote-page">
      {/* Search Bar */}
      <div className="relative">
        <div className="flex items-center gap-2">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
            <Input
              type="text"
              placeholder="Search assets..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 bg-zinc-900 border-zinc-800"
              data-testid="quote-search-input"
            />
          </div>
        </div>
        
        {/* Search Results Dropdown */}
        {searchResults.length > 0 && (
          <div className="absolute top-full left-0 mt-1 w-full max-w-md bg-zinc-900 border border-zinc-800 rounded-sm z-50 shadow-lg">
            {searchResults.map((result, i) => (
              <div
                key={i}
                className="px-4 py-2 hover:bg-zinc-800 cursor-pointer flex items-center justify-between"
                onClick={() => handleSelectAsset(result)}
                data-testid={`search-result-${result.symbol}`}
              >
                <div>
                  <span className="font-mono text-white">{result.symbol}</span>
                  <span className="text-zinc-500 text-sm ml-2">{result.name}</span>
                </div>
                <Badge variant="outline" className="text-[10px] text-zinc-500">
                  {result.type}
                </Badge>
              </div>
            ))}
          </div>
        )}
      </div>

      {quote && (
        <>
          {/* Header */}
          <Card className="nexus-card">
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-3">
                    <h1 className="text-2xl font-semibold text-white">{quote.symbol}</h1>
                    <Badge variant="outline" className="text-xs uppercase text-zinc-400">
                      {quote.asset_type}
                    </Badge>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleWatchlistToggle}
                      data-testid="watchlist-toggle-btn"
                    >
                      {isInWatchlist ? (
                        <Star className="w-5 h-5 text-yellow-500 fill-yellow-500" />
                      ) : (
                        <StarOff className="w-5 h-5 text-zinc-500" />
                      )}
                    </Button>
                  </div>
                  <p className="text-zinc-400 text-sm mt-1">{quote.name}</p>
                </div>
                
                <div className="text-right">
                  <div className="flex items-baseline gap-3">
                    <span className="font-mono text-3xl text-white">{quote.price?.toFixed(2)}</span>
                    <span className="text-zinc-500 text-sm">{quote.currency}</span>
                  </div>
                  <div className={`flex items-center gap-2 justify-end mt-1 ${isPositive ? 'text-emerald-500' : 'text-red-500'}`}>
                    {isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                    <span className="font-mono">
                      {isPositive ? '+' : ''}{quote.change?.toFixed(2)} ({isPositive ? '+' : ''}{quote.change_percent?.toFixed(2)}%)
                    </span>
                  </div>
                </div>
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-6 gap-4 mt-6 pt-4 border-t border-zinc-800">
                <div>
                  <p className="text-[10px] text-zinc-500 uppercase">Open</p>
                  <p className="font-mono text-sm text-white">{quote.open?.toFixed(2) || '—'}</p>
                </div>
                <div>
                  <p className="text-[10px] text-zinc-500 uppercase">High</p>
                  <p className="font-mono text-sm text-emerald-500">{quote.high?.toFixed(2) || '—'}</p>
                </div>
                <div>
                  <p className="text-[10px] text-zinc-500 uppercase">Low</p>
                  <p className="font-mono text-sm text-red-500">{quote.low?.toFixed(2) || '—'}</p>
                </div>
                <div>
                  <p className="text-[10px] text-zinc-500 uppercase">Prev Close</p>
                  <p className="font-mono text-sm text-white">{quote.previous_close?.toFixed(2) || '—'}</p>
                </div>
                <div>
                  <p className="text-[10px] text-zinc-500 uppercase">Volume</p>
                  <p className="font-mono text-sm text-white">{quote.volume?.toLocaleString() || '—'}</p>
                </div>
                <div>
                  <p className="text-[10px] text-zinc-500 uppercase">Mkt Cap</p>
                  <p className="font-mono text-sm text-white">
                    {quote.market_cap ? `${(quote.market_cap / 1e9).toFixed(2)}B` : '—'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Main Content Grid */}
          <div className="grid grid-cols-12 gap-4">
            {/* Chart */}
            <div className="col-span-8">
              <Card className="nexus-card">
                <CardHeader className="card-header-terminal">
                  <CardTitle className="card-header-title flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-orange-500" />
                    Price Chart
                  </CardTitle>
                  <div className="flex gap-1">
                    {periods.map((p) => (
                      <Button
                        key={p.value}
                        variant={period === p.value ? 'default' : 'ghost'}
                        size="sm"
                        className={`text-xs px-2 h-6 ${period === p.value ? 'bg-orange-500' : ''}`}
                        onClick={() => { setPeriod(p.value); setIntervalState(p.interval); }}
                        data-testid={`period-btn-${p.value}`}
                      >
                        {p.label}
                      </Button>
                    ))}
                  </div>
                </CardHeader>
                <CardContent className="p-4">
                  {history?.data && (
                    <ResponsiveContainer width="100%" height={400}>
                      <AreaChart data={history.data}>
                        <defs>
                          <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={isPositive ? "#22c55e" : "#ef4444"} stopOpacity={0.3}/>
                            <stop offset="95%" stopColor={isPositive ? "#22c55e" : "#ef4444"} stopOpacity={0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid stroke="#27272a" strokeDasharray="3 3" />
                        <XAxis 
                          dataKey="date" 
                          stroke="#52525b" 
                          tick={{ fill: '#52525b', fontSize: 10 }}
                          tickFormatter={(value) => {
                            const date = new Date(value);
                            if (period === '1d') return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                            return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
                          }}
                        />
                        <YAxis 
                          stroke="#52525b" 
                          tick={{ fill: '#52525b', fontSize: 10 }}
                          domain={['dataMin', 'dataMax']}
                          tickFormatter={(value) => value.toFixed(2)}
                        />
                        <Tooltip
                          contentStyle={{ 
                            backgroundColor: '#18181b', 
                            border: '1px solid #27272a',
                            borderRadius: '2px',
                            fontSize: '12px'
                          }}
                          labelStyle={{ color: '#a1a1aa' }}
                          itemStyle={{ color: '#fafafa' }}
                          formatter={(value) => [`$${value.toFixed(2)}`, 'Price']}
                          labelFormatter={(label) => new Date(label).toLocaleString()}
                        />
                        <Area 
                          type="monotone" 
                          dataKey="close" 
                          stroke={isPositive ? "#22c55e" : "#ef4444"}
                          strokeWidth={2}
                          fill="url(#colorPrice)"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  )}
                </CardContent>
              </Card>

              {/* Volume Chart */}
              <Card className="nexus-card mt-4">
                <CardHeader className="card-header-terminal py-2">
                  <CardTitle className="card-header-title">Volume</CardTitle>
                </CardHeader>
                <CardContent className="p-2">
                  {history?.data && (
                    <ResponsiveContainer width="100%" height={100}>
                      <BarChart data={history.data}>
                        <Bar dataKey="volume" fill="#3b82f6" opacity={0.6} />
                        <XAxis dataKey="date" hide />
                        <YAxis hide />
                        <Tooltip
                          contentStyle={{ 
                            backgroundColor: '#18181b', 
                            border: '1px solid #27272a',
                            borderRadius: '2px',
                            fontSize: '12px'
                          }}
                          formatter={(value) => [value.toLocaleString(), 'Volume']}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Right Column */}
            <div className="col-span-4 space-y-4">
              {/* Technical Indicators */}
              {technicals && (
                <Card className="nexus-card">
                  <CardHeader className="card-header-terminal">
                    <CardTitle className="card-header-title flex items-center gap-2">
                      <Activity className="w-4 h-4 text-orange-500" />
                      Technical Analysis
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-3">
                    {/* Signal */}
                    <div className="flex items-center justify-between mb-3 pb-3 border-b border-zinc-800">
                      <div>
                        <p className="text-[10px] text-zinc-500 uppercase">Signal</p>
                        <Badge className={`mt-1 rounded-none ${
                          technicals.signal === 'buy' ? 'bg-emerald-500/20 text-emerald-500' :
                          technicals.signal === 'sell' ? 'bg-red-500/20 text-red-500' :
                          'bg-zinc-500/20 text-zinc-400'
                        }`}>
                          {technicals.signal?.toUpperCase()}
                        </Badge>
                      </div>
                      <div className="text-right">
                        <p className="text-[10px] text-zinc-500 uppercase">Trend</p>
                        <span className={`text-sm font-medium ${
                          technicals.trend === 'bullish' ? 'text-emerald-500' :
                          technicals.trend === 'bearish' ? 'text-red-500' :
                          'text-zinc-400'
                        }`}>
                          {technicals.trend?.charAt(0).toUpperCase() + technicals.trend?.slice(1)}
                        </span>
                      </div>
                    </div>
                    
                    {/* Key Indicators */}
                    <div className="grid grid-cols-2 gap-2">
                      <div className="p-2 bg-zinc-900/50 rounded-sm">
                        <p className="text-[9px] text-zinc-500">RSI (14)</p>
                        <p className={`font-mono text-sm ${
                          technicals.rsi_14 > 70 ? 'text-red-500' :
                          technicals.rsi_14 < 30 ? 'text-emerald-500' :
                          'text-white'
                        }`}>
                          {technicals.rsi_14?.toFixed(1) || '—'}
                        </p>
                      </div>
                      <div className="p-2 bg-zinc-900/50 rounded-sm">
                        <p className="text-[9px] text-zinc-500">MACD</p>
                        <p className={`font-mono text-sm ${
                          technicals.macd > 0 ? 'text-emerald-500' : 'text-red-500'
                        }`}>
                          {technicals.macd?.toFixed(2) || '—'}
                        </p>
                      </div>
                      <div className="p-2 bg-zinc-900/50 rounded-sm">
                        <p className="text-[9px] text-zinc-500">SMA 20</p>
                        <p className="font-mono text-sm text-white">{technicals.sma_20?.toFixed(2) || '—'}</p>
                      </div>
                      <div className="p-2 bg-zinc-900/50 rounded-sm">
                        <p className="text-[9px] text-zinc-500">SMA 50</p>
                        <p className="font-mono text-sm text-white">{technicals.sma_50?.toFixed(2) || '—'}</p>
                      </div>
                    </div>
                    
                    {/* Bollinger Bands */}
                    <div className="mt-2 p-2 bg-zinc-900/50 rounded-sm">
                      <p className="text-[9px] text-zinc-500 mb-1">Bollinger Bands</p>
                      <div className="flex justify-between text-xs">
                        <span className="text-red-400">{technicals.bollinger_lower?.toFixed(2)}</span>
                        <span className="text-zinc-400">{technicals.bollinger_middle?.toFixed(2)}</span>
                        <span className="text-emerald-400">{technicals.bollinger_upper?.toFixed(2)}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Impact Score */}
              {impactScore && (
                <Card className="nexus-card">
                  <CardHeader className="card-header-terminal">
                    <CardTitle className="card-header-title flex items-center gap-2">
                      <Target className="w-4 h-4 text-orange-500" />
                      Impact Score
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-3">
                    <div className="flex items-center justify-between mb-3">
                      <div className="text-center">
                        <span className={`font-mono text-3xl ${
                          impactScore.risk_level === 'critical' ? 'text-red-500' :
                          impactScore.risk_level === 'high' ? 'text-orange-500' :
                          impactScore.risk_level === 'medium' ? 'text-yellow-500' :
                          'text-emerald-500'
                        }`}>
                          {impactScore.score?.toFixed(0)}
                        </span>
                        <p className="text-[10px] text-zinc-500 uppercase">/ 100</p>
                      </div>
                      <Badge className={`rounded-none ${
                        impactScore.risk_level === 'critical' ? 'badge-critical' :
                        impactScore.risk_level === 'high' ? 'badge-high' :
                        impactScore.risk_level === 'medium' ? 'badge-medium' :
                        'badge-low'
                      }`}>
                        {impactScore.risk_level?.toUpperCase()}
                      </Badge>
                    </div>
                    
                    {impactScore.factors?.length > 0 && (
                      <div className="space-y-2">
                        <p className="text-[10px] text-zinc-500 uppercase">Risk Factors</p>
                        {impactScore.factors.map((factor, i) => (
                          <div key={i} className="flex items-center gap-2 text-xs">
                            <AlertTriangle className={`w-3 h-3 ${
                              factor.impact > 0 ? 'text-red-500' : 'text-emerald-500'
                            }`} />
                            <span className="text-zinc-400 flex-1">{factor.description}</span>
                            <span className={`font-mono ${
                              factor.impact > 0 ? 'text-red-500' : 'text-emerald-500'
                            }`}>
                              {factor.impact > 0 ? '+' : ''}{factor.impact}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Supply Chain Preview */}
              {supplyChain.length > 0 && (
                <Card className="nexus-card">
                  <CardHeader className="card-header-terminal">
                    <CardTitle className="card-header-title flex items-center gap-2">
                      <GitBranch className="w-4 h-4 text-orange-500" />
                      Supply Chain
                    </CardTitle>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      className="text-xs text-zinc-400"
                      onClick={() => navigate(`/supplychain?symbol=${symbol}`)}
                    >
                      View Graph <ArrowRight className="w-3 h-3 ml-1" />
                    </Button>
                  </CardHeader>
                  <CardContent className="p-2">
                    <Tabs defaultValue="suppliers" className="w-full">
                      <TabsList className="grid w-full grid-cols-2 bg-zinc-900 h-7">
                        <TabsTrigger value="suppliers" className="text-xs">Suppliers</TabsTrigger>
                        <TabsTrigger value="customers" className="text-xs">Customers</TabsTrigger>
                      </TabsList>
                      <TabsContent value="suppliers" className="mt-2">
                        <ScrollArea className="h-[150px]">
                          {supplyChain.filter(n => n.relationship === 'supplier').slice(0, 5).map((node, i) => (
                            <div key={i} className="flex items-center justify-between py-2 px-1 hover:bg-zinc-800/30 rounded-sm">
                              <div>
                                <span className="text-sm text-white">{node.name}</span>
                                <p className="text-[10px] text-zinc-500">{node.country}</p>
                              </div>
                              <Badge className={`badge-${node.risk_level} rounded-none text-[9px]`}>
                                {node.risk_level}
                              </Badge>
                            </div>
                          ))}
                        </ScrollArea>
                      </TabsContent>
                      <TabsContent value="customers" className="mt-2">
                        <ScrollArea className="h-[150px]">
                          {supplyChain.filter(n => n.relationship === 'customer').slice(0, 5).map((node, i) => (
                            <div key={i} className="flex items-center justify-between py-2 px-1 hover:bg-zinc-800/30 rounded-sm">
                              <div>
                                <span className="text-sm text-white">{node.name}</span>
                                <p className="text-[10px] text-zinc-500">{node.country}</p>
                              </div>
                              <Badge className={`badge-${node.risk_level} rounded-none text-[9px]`}>
                                {node.risk_level}
                              </Badge>
                            </div>
                          ))}
                        </ScrollArea>
                      </TabsContent>
                    </Tabs>
                  </CardContent>
                </Card>
              )}

              {/* Related News */}
              <Card className="nexus-card">
                <CardHeader className="card-header-terminal">
                  <CardTitle className="card-header-title flex items-center gap-2">
                    <Newspaper className="w-4 h-4 text-orange-500" />
                    Related News
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <ScrollArea className="h-[250px]">
                    {relatedNews.length > 0 ? relatedNews.map((article, i) => (
                      <div 
                        key={i}
                        className="p-3 border-b border-zinc-800/50 hover:bg-zinc-800/30 cursor-pointer"
                        onClick={() => window.open(article.url, '_blank')}
                      >
                        <h4 className="text-sm text-white line-clamp-2">{article.title}</h4>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-[10px] text-zinc-500">{article.source}</span>
                          <span className="text-[10px] text-zinc-500 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {new Date(article.published_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                      </div>
                    )) : (
                      <div className="p-4 text-center text-zinc-500 text-sm">
                        No related news found
                      </div>
                    )}
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Options Chain Section - Full Width */}
          {quote?.asset_type === 'stock' && (
            <div className="mt-4">
              <OptionsChain symbol={symbol} />
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default QuotePage;
