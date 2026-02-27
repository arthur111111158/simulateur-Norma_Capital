import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { ScrollArea } from '../components/ui/scroll-area';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Calendar, TrendingUp, TrendingDown, Clock, Building2, Globe2 } from 'lucide-react';

const EarningsPage = () => {
  const navigate = useNavigate();
  const { fetchEarnings, earnings } = useApp();
  const [loading, setLoading] = useState(true);
  const [region, setRegion] = useState('all');
  const [days, setDays] = useState('30');

  useEffect(() => {
    const loadEarnings = async () => {
      setLoading(true);
      await fetchEarnings(parseInt(days), region === 'all' ? null : region);
      setLoading(false);
    };
    loadEarnings();
  }, [fetchEarnings, region, days]);

  const formatCurrency = (num) => {
    if (num === null || num === undefined) return '—';
    if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
    return `$${num.toFixed(2)}`;
  };

  const formatEPS = (num) => {
    if (num === null || num === undefined) return '—';
    return `$${num.toFixed(2)}`;
  };

  const getDaysUntil = (date) => {
    const now = new Date();
    const earningsDate = new Date(date);
    const diffTime = earningsDate - now;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const groupEventsByDate = (events) => {
    const grouped = {};
    events.forEach(event => {
      const date = new Date(event.earnings_date).toISOString().split('T')[0];
      if (!grouped[date]) {
        grouped[date] = [];
      }
      grouped[date].push(event);
    });
    return grouped;
  };

  const groupedEarnings = groupEventsByDate(earnings);
  const sortedDates = Object.keys(groupedEarnings).sort();

  return (
    <div className="space-y-4" data-testid="earnings-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white flex items-center gap-3">
            <Calendar className="w-6 h-6 text-orange-500" />
            Earnings Calendar
          </h1>
          <p className="text-zinc-500 text-sm mt-1">
            Upcoming company earnings announcements
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Select value={days} onValueChange={setDays}>
            <SelectTrigger className="w-[120px] h-8 text-xs bg-zinc-900 border-zinc-800" data-testid="days-select">
              <SelectValue placeholder="Period" />
            </SelectTrigger>
            <SelectContent className="bg-zinc-900 border-zinc-800">
              <SelectItem value="7" className="text-xs">7 days</SelectItem>
              <SelectItem value="14" className="text-xs">14 days</SelectItem>
              <SelectItem value="30" className="text-xs">30 days</SelectItem>
              <SelectItem value="60" className="text-xs">60 days</SelectItem>
            </SelectContent>
          </Select>

          <Select value={region} onValueChange={setRegion}>
            <SelectTrigger className="w-[120px] h-8 text-xs bg-zinc-900 border-zinc-800" data-testid="region-select">
              <SelectValue placeholder="Region" />
            </SelectTrigger>
            <SelectContent className="bg-zinc-900 border-zinc-800">
              <SelectItem value="all" className="text-xs">All Regions</SelectItem>
              <SelectItem value="US" className="text-xs">United States</SelectItem>
              <SelectItem value="Europe" className="text-xs">Europe</SelectItem>
              <SelectItem value="Asia" className="text-xs">Asia</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="nexus-card">
          <CardContent className="p-4">
            <p className="text-[10px] text-zinc-500 uppercase">Total Events</p>
            <p className="font-mono text-2xl text-white">{earnings.length}</p>
          </CardContent>
        </Card>
        <Card className="nexus-card">
          <CardContent className="p-4">
            <p className="text-[10px] text-zinc-500 uppercase">This Week</p>
            <p className="font-mono text-2xl text-orange-500">
              {earnings.filter(e => getDaysUntil(e.earnings_date) <= 7 && getDaysUntil(e.earnings_date) >= 0).length}
            </p>
          </CardContent>
        </Card>
        <Card className="nexus-card">
          <CardContent className="p-4">
            <p className="text-[10px] text-zinc-500 uppercase">Tomorrow</p>
            <p className="font-mono text-2xl text-emerald-500">
              {earnings.filter(e => getDaysUntil(e.earnings_date) === 1).length}
            </p>
          </CardContent>
        </Card>
        <Card className="nexus-card">
          <CardContent className="p-4">
            <p className="text-[10px] text-zinc-500 uppercase">Today</p>
            <p className="font-mono text-2xl text-yellow-500">
              {earnings.filter(e => getDaysUntil(e.earnings_date) === 0).length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Earnings List */}
      <Card className="nexus-card">
        <CardHeader className="card-header-terminal">
          <CardTitle className="card-header-title">
            Upcoming Earnings
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="w-6 h-6 border-2 border-orange-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : earnings.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-zinc-500">
              <Calendar className="w-12 h-12 mb-4 opacity-50" />
              <p>No earnings events found for this period</p>
            </div>
          ) : (
            <ScrollArea className="h-[600px]">
              {sortedDates.map(date => {
                const dateEvents = groupedEarnings[date];
                const displayDate = new Date(date);
                const daysUntil = getDaysUntil(date);
                
                return (
                  <div key={date} className="border-b border-zinc-800 last:border-b-0">
                    {/* Date Header */}
                    <div className="sticky top-0 bg-zinc-900/95 backdrop-blur px-4 py-2 border-b border-zinc-800/50">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-white">
                          {displayDate.toLocaleDateString('en-US', { 
                            weekday: 'long', 
                            month: 'long', 
                            day: 'numeric',
                            year: 'numeric'
                          })}
                        </span>
                        <Badge className={`rounded-none text-[10px] ${
                          daysUntil === 0 ? 'bg-yellow-500/20 text-yellow-500' :
                          daysUntil === 1 ? 'bg-emerald-500/20 text-emerald-500' :
                          daysUntil <= 7 ? 'bg-orange-500/20 text-orange-500' :
                          'bg-zinc-500/20 text-zinc-400'
                        }`}>
                          {daysUntil === 0 ? 'Today' :
                           daysUntil === 1 ? 'Tomorrow' :
                           `In ${daysUntil} days`}
                        </Badge>
                      </div>
                    </div>

                    {/* Events for this date */}
                    <Table>
                      <TableHeader>
                        <TableRow className="hover:bg-transparent border-zinc-800/50">
                          <TableHead className="text-[10px] text-zinc-500 font-medium w-[100px]">Symbol</TableHead>
                          <TableHead className="text-[10px] text-zinc-500 font-medium">Company</TableHead>
                          <TableHead className="text-[10px] text-zinc-500 font-medium w-[80px]">Sector</TableHead>
                          <TableHead className="text-[10px] text-zinc-500 font-medium w-[80px]">Region</TableHead>
                          <TableHead className="text-[10px] text-zinc-500 font-medium text-right w-[100px]">EPS Est.</TableHead>
                          <TableHead className="text-[10px] text-zinc-500 font-medium text-right w-[120px]">Rev. Est.</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {dateEvents.map((event, i) => (
                          <TableRow 
                            key={i} 
                            className="hover:bg-zinc-800/50 cursor-pointer border-zinc-800/30"
                            onClick={() => navigate(`/quote?symbol=${event.symbol}`)}
                            data-testid={`earnings-row-${event.symbol}`}
                          >
                            <TableCell className="font-mono text-sm py-3">
                              <span className="text-orange-400 hover:underline">{event.symbol}</span>
                            </TableCell>
                            <TableCell className="py-3">
                              <div>
                                <span className="text-sm text-white">{event.company_name}</span>
                              </div>
                            </TableCell>
                            <TableCell className="py-3">
                              <Badge variant="outline" className="text-[9px] text-zinc-400 rounded-none">
                                {event.sector || '—'}
                              </Badge>
                            </TableCell>
                            <TableCell className="py-3">
                              <span className="flex items-center gap-1 text-xs text-zinc-400">
                                <Globe2 className="w-3 h-3" />
                                {event.region || '—'}
                              </span>
                            </TableCell>
                            <TableCell className="text-right py-3">
                              <span className="font-mono text-sm text-white">
                                {formatEPS(event.eps_estimate)}
                              </span>
                            </TableCell>
                            <TableCell className="text-right py-3">
                              <span className="font-mono text-sm text-zinc-400">
                                {formatCurrency(event.revenue_estimate)}
                              </span>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                );
              })}
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default EarningsPage;
