import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { ScrollArea } from '../components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  TrendingUp, 
  TrendingDown, 
  Star, 
  StarOff, 
  Clock, 
  Globe,
  AlertTriangle,
  Activity,
  BarChart3,
  Zap
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, AreaChart, Area } from 'recharts';
import { useNavigate } from 'react-router-dom';

// Price display component
const PriceDisplay = ({ price, change, changePercent }) => {
  const isPositive = change >= 0;
  return (
    <div className="flex items-baseline gap-2">
      <span className="font-mono text-lg text-white">{price?.toFixed(2) || '—'}</span>
      <span className={`font-mono text-sm ${isPositive ? 'text-emerald-500' : 'text-red-500'}`}>
        {isPositive ? '+' : ''}{change?.toFixed(2) || '0.00'}
      </span>
      <span className={`font-mono text-xs ${isPositive ? 'text-emerald-500' : 'text-red-500'}`}>
        ({isPositive ? '+' : ''}{changePercent?.toFixed(2) || '0.00'}%)
      </span>
    </div>
  );
};

// Mini chart component
const MiniChart = ({ data, positive }) => {
  if (!data || data.length === 0) return null;
  
  return (
    <ResponsiveContainer width="100%" height={40}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id={positive ? "colorPositive" : "colorNegative"} x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={positive ? "#22c55e" : "#ef4444"} stopOpacity={0.3}/>
            <stop offset="95%" stopColor={positive ? "#22c55e" : "#ef4444"} stopOpacity={0}/>
          </linearGradient>
        </defs>
        <Area 
          type="monotone" 
          dataKey="close" 
          stroke={positive ? "#22c55e" : "#ef4444"}
          strokeWidth={1.5}
          fill={`url(#${positive ? "colorPositive" : "colorNegative"})`}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};

// Watchlist widget
const WatchlistWidget = () => {
  const { watchlist, removeFromWatchlist, getQuote, getHistory } = useApp();
  const [quotes, setQuotes] = useState({});
  const [charts, setCharts] = useState({});
  const navigate = useNavigate();

  useEffect(() => {
    const fetchQuotes = async () => {
      for (const item of watchlist) {
        const quote = await getQuote(item.symbol);
        if (quote) {
          setQuotes(prev => ({ ...prev, [item.symbol]: quote }));
        }
        const history = await getHistory(item.symbol, '5d', '1h');
        if (history) {
          setCharts(prev => ({ ...prev, [item.symbol]: history.data }));
        }
      }
    };
    if (watchlist.length > 0) {
      fetchQuotes();
    }
  }, [watchlist, getQuote, getHistory]);

  if (watchlist.length === 0) {
    return (
      <Card className="nexus-card h-full">
        <CardHeader className="card-header-terminal">
          <CardTitle className="card-header-title flex items-center gap-2">
            <Star className="w-4 h-4 text-orange-500" />
            Watchlist
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          <p className="text-sm text-zinc-500 text-center py-8">
            No items in watchlist. Search for assets to add.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="nexus-card h-full">
      <CardHeader className="card-header-terminal">
        <CardTitle className="card-header-title flex items-center gap-2">
          <Star className="w-4 h-4 text-orange-500" />
          Watchlist
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[300px]">
          <table className="data-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Price</th>
                <th>Change</th>
                <th>Chart</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {watchlist.map((item) => {
                const quote = quotes[item.symbol];
                const chartData = charts[item.symbol];
                const isPositive = quote?.change >= 0;
                
                return (
                  <tr 
                    key={item.symbol} 
                    className="cursor-pointer"
                    onClick={() => navigate(`/quote?symbol=${item.symbol}`)}
                    data-testid={`watchlist-item-${item.symbol}`}
                  >
                    <td>
                      <div>
                        <span className="text-white font-medium">{item.symbol}</span>
                        <p className="text-[10px] text-zinc-500 truncate max-w-[100px]">{item.name}</p>
                      </div>
                    </td>
                    <td className="font-mono text-white">
                      {quote?.price?.toFixed(2) || '—'}
                    </td>
                    <td className={`font-mono ${isPositive ? 'text-emerald-500' : 'text-red-500'}`}>
                      {isPositive ? '+' : ''}{quote?.change_percent?.toFixed(2) || '0.00'}%
                    </td>
                    <td className="w-20">
                      <MiniChart data={chartData} positive={isPositive} />
                    </td>
                    <td>
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="h-6 w-6 p-0"
                        onClick={(e) => {
                          e.stopPropagation();
                          removeFromWatchlist(item.symbol);
                        }}
                      >
                        <StarOff className="w-3 h-3 text-zinc-500" />
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};

// Market movers widget
const MoversWidget = () => {
  const { movers } = useApp();
  const navigate = useNavigate();

  return (
    <Card className="nexus-card h-full">
      <CardHeader className="card-header-terminal">
        <CardTitle className="card-header-title flex items-center gap-2">
          <Activity className="w-4 h-4 text-orange-500" />
          Market Movers
        </CardTitle>
      </CardHeader>
      <CardContent className="p-2">
        <Tabs defaultValue="gainers" className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-zinc-900 h-7">
            <TabsTrigger value="gainers" className="text-xs data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-500">
              <TrendingUp className="w-3 h-3 mr-1" /> Gainers
            </TabsTrigger>
            <TabsTrigger value="losers" className="text-xs data-[state=active]:bg-red-500/20 data-[state=active]:text-red-500">
              <TrendingDown className="w-3 h-3 mr-1" /> Losers
            </TabsTrigger>
          </TabsList>
          <TabsContent value="gainers" className="mt-2">
            <ScrollArea className="h-[200px]">
              {movers.gainers?.map((stock, i) => (
                <div 
                  key={stock.symbol}
                  className="flex items-center justify-between py-2 px-1 hover:bg-zinc-800/30 cursor-pointer rounded-sm"
                  onClick={() => navigate(`/quote?symbol=${stock.symbol}`)}
                  data-testid={`gainer-${stock.symbol}`}
                >
                  <div>
                    <span className="font-mono text-sm text-white">{stock.symbol}</span>
                    <p className="text-[10px] text-zinc-500 truncate max-w-[120px]">{stock.name}</p>
                  </div>
                  <div className="text-right">
                    <span className="font-mono text-sm text-white">{stock.price?.toFixed(2)}</span>
                    <p className="font-mono text-xs text-emerald-500">+{stock.change_percent?.toFixed(2)}%</p>
                  </div>
                </div>
              ))}
              {(!movers.gainers || movers.gainers.length === 0) && (
                <p className="text-center text-zinc-500 text-xs py-4">No gainers data</p>
              )}
            </ScrollArea>
          </TabsContent>
          <TabsContent value="losers" className="mt-2">
            <ScrollArea className="h-[200px]">
              {movers.losers?.map((stock, i) => (
                <div 
                  key={stock.symbol}
                  className="flex items-center justify-between py-2 px-1 hover:bg-zinc-800/30 cursor-pointer rounded-sm"
                  onClick={() => navigate(`/quote?symbol=${stock.symbol}`)}
                  data-testid={`loser-${stock.symbol}`}
                >
                  <div>
                    <span className="font-mono text-sm text-white">{stock.symbol}</span>
                    <p className="text-[10px] text-zinc-500 truncate max-w-[120px]">{stock.name}</p>
                  </div>
                  <div className="text-right">
                    <span className="font-mono text-sm text-white">{stock.price?.toFixed(2)}</span>
                    <p className="font-mono text-xs text-red-500">{stock.change_percent?.toFixed(2)}%</p>
                  </div>
                </div>
              ))}
              {(!movers.losers || movers.losers.length === 0) && (
                <p className="text-center text-zinc-500 text-xs py-4">No losers data</p>
              )}
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

// News widget
const NewsWidget = () => {
  const { news } = useApp();
  const navigate = useNavigate();

  return (
    <Card className="nexus-card h-full">
      <CardHeader className="card-header-terminal">
        <CardTitle className="card-header-title flex items-center gap-2">
          <Zap className="w-4 h-4 text-orange-500" />
          Breaking News
        </CardTitle>
        <Button 
          variant="ghost" 
          size="sm" 
          className="text-xs text-zinc-400"
          onClick={() => navigate('/news')}
        >
          View All
        </Button>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[300px]">
          {news.slice(0, 10).map((article, i) => (
            <div 
              key={article.id || i}
              className="p-3 border-b border-zinc-800/50 hover:bg-zinc-800/30 cursor-pointer"
              onClick={() => window.open(article.url, '_blank')}
              data-testid={`news-item-${i}`}
            >
              <div className="flex items-start gap-2">
                <div className="flex-1">
                  <h4 className="text-sm text-white line-clamp-2 leading-tight">{article.title}</h4>
                  <div className="flex items-center gap-2 mt-1.5">
                    <span className="text-[10px] text-zinc-500">{article.source}</span>
                    <span className="text-[10px] text-zinc-600">•</span>
                    <span className="text-[10px] text-zinc-500 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(article.published_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  {article.tags?.length > 0 && (
                    <div className="flex gap-1 mt-1.5 flex-wrap">
                      {article.tags.slice(0, 3).map((tag, j) => (
                        <Badge key={j} variant="outline" className="rounded-none text-[9px] px-1 py-0 h-4 text-orange-500 border-orange-500/30">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </ScrollArea>
      </CardContent>
    </Card>
  );
};

// Conflicts widget
const ConflictsWidget = () => {
  const { conflicts } = useApp();
  const navigate = useNavigate();

  const getSeverityColor = (severity) => {
    if (severity >= 8) return 'badge-critical';
    if (severity >= 6) return 'badge-high';
    if (severity >= 4) return 'badge-medium';
    return 'badge-low';
  };

  return (
    <Card className="nexus-card h-full">
      <CardHeader className="card-header-terminal">
        <CardTitle className="card-header-title flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-orange-500" />
          Geopolitical Alerts
        </CardTitle>
        <Button 
          variant="ghost" 
          size="sm" 
          className="text-xs text-zinc-400"
          onClick={() => navigate('/worldmap')}
        >
          View Map
        </Button>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[250px]">
          {conflicts.slice(0, 5).map((conflict, i) => (
            <div 
              key={conflict.id || i}
              className="p-3 border-b border-zinc-800/50 hover:bg-zinc-800/30 cursor-pointer"
              onClick={() => navigate('/worldmap')}
              data-testid={`conflict-item-${i}`}
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h4 className="text-sm text-white">{conflict.title}</h4>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-[10px] text-zinc-500 flex items-center gap-1">
                      <Globe className="w-3 h-3" />
                      {conflict.country}
                    </span>
                    <Badge className={`${getSeverityColor(conflict.severity)} rounded-none text-[9px] px-1 py-0`}>
                      {conflict.status}
                    </Badge>
                  </div>
                </div>
                <div className="text-right">
                  <span className="font-mono text-lg text-orange-500">{conflict.impact_score?.toFixed(0)}</span>
                  <p className="text-[9px] text-zinc-500 uppercase">Impact</p>
                </div>
              </div>
              {conflict.affected_assets?.length > 0 && (
                <div className="flex gap-1 mt-2 flex-wrap">
                  {conflict.affected_assets.slice(0, 4).map((asset, j) => (
                    <Badge key={j} variant="outline" className="rounded-none text-[9px] px-1 py-0 h-4 text-zinc-400 border-zinc-700">
                      {asset}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          ))}
        </ScrollArea>
      </CardContent>
    </Card>
  );
};

// Quick stats widget - Global indices
const QuickStatsWidget = () => {
  const [indices, setIndices] = useState([]);
  const { getQuote } = useApp();

  useEffect(() => {
    const fetchIndices = async () => {
      // Global indices: US, Europe, Asia
      const symbols = [
        '^GSPC', '^DJI', '^IXIC',      // US
        '^FCHI', '^GDAXI', '^FTSE',     // Europe
        '^N225', '^HSI', '000001.SS',   // Asia
        'GC=F', 'CL=F', 'EURUSD=X'      // Commodities & Forex
      ];
      const names = [
        'S&P 500', 'Dow Jones', 'NASDAQ',
        'CAC 40', 'DAX', 'FTSE 100',
        'Nikkei', 'Hang Seng', 'Shanghai',
        'Gold', 'Oil', 'EUR/USD'
      ];
      const regions = [
        'US', 'US', 'US',
        'EU', 'EU', 'EU',
        'Asia', 'Asia', 'Asia',
        '', '', ''
      ];
      
      const data = [];
      for (let i = 0; i < symbols.length; i++) {
        const quote = await getQuote(symbols[i]);
        if (quote) {
          data.push({ ...quote, displayName: names[i], region: regions[i] });
        }
      }
      setIndices(data);
    };
    fetchIndices();
  }, [getQuote]);

  // Group by category
  const usIndices = indices.slice(0, 3);
  const euIndices = indices.slice(3, 6);
  const asiaIndices = indices.slice(6, 9);
  const commodities = indices.slice(9);

  const renderGroup = (items, title, flag) => (
    <div className="space-y-1">
      <p className="text-[10px] text-zinc-600 uppercase flex items-center gap-1">
        <span>{flag}</span> {title}
      </p>
      <div className="grid grid-cols-3 gap-1">
        {items.map((index, i) => {
          const isPositive = index.change >= 0;
          return (
            <div key={i} className="text-center p-1.5 bg-zinc-900/50 rounded-sm">
              <p className="text-[9px] text-zinc-500 uppercase truncate">{index.displayName}</p>
              <p className="font-mono text-xs text-white">{index.price?.toFixed(2)}</p>
              <p className={`font-mono text-[10px] ${isPositive ? 'text-emerald-500' : 'text-red-500'}`}>
                {isPositive ? '+' : ''}{index.change_percent?.toFixed(2)}%
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );

  return (
    <Card className="nexus-card">
      <CardHeader className="card-header-terminal py-1.5">
        <CardTitle className="card-header-title flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-orange-500" />
          Global Markets Overview
        </CardTitle>
      </CardHeader>
      <CardContent className="p-3">
        <div className="grid grid-cols-4 gap-3">
          {renderGroup(usIndices, 'United States', '🇺🇸')}
          {renderGroup(euIndices, 'Europe', '🇪🇺')}
          {renderGroup(asiaIndices, 'Asia', '🌏')}
          {renderGroup(commodities, 'Commodities & FX', '📊')}
        </div>
      </CardContent>
    </Card>
  );
};

// Main Dashboard
const Dashboard = () => {
  const { loading } = useApp();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[80vh]">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-zinc-500 text-sm mt-4">Loading market data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="dashboard">
      {/* Markets Overview */}
      <QuickStatsWidget />
      
      {/* Main Grid */}
      <div className="grid grid-cols-12 gap-4">
        {/* Left Column */}
        <div className="col-span-4 space-y-4">
          <WatchlistWidget />
          <MoversWidget />
        </div>

        {/* Middle Column */}
        <div className="col-span-5">
          <NewsWidget />
        </div>

        {/* Right Column */}
        <div className="col-span-3">
          <ConflictsWidget />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
