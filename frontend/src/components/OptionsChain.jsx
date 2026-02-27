import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { ScrollArea } from '../components/ui/scroll-area';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { TrendingUp, TrendingDown, BarChart2 } from 'lucide-react';

const OptionsChain = ({ symbol }) => {
  const { getOptionsExpirations, getOptionsChain } = useApp();
  const [expirations, setExpirations] = useState([]);
  const [selectedExpiration, setSelectedExpiration] = useState('');
  const [optionsData, setOptionsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('calls');

  // Fetch expirations
  useEffect(() => {
    const fetchExpirations = async () => {
      if (!symbol) return;
      setLoading(true);
      const data = await getOptionsExpirations(symbol);
      if (data?.expirations) {
        setExpirations(data.expirations);
        if (data.expirations.length > 0) {
          setSelectedExpiration(data.expirations[0]);
        }
      }
      setLoading(false);
    };
    fetchExpirations();
  }, [symbol, getOptionsExpirations]);

  // Fetch options chain when expiration changes
  useEffect(() => {
    const fetchChain = async () => {
      if (!symbol || !selectedExpiration) return;
      setLoading(true);
      const data = await getOptionsChain(symbol, selectedExpiration);
      setOptionsData(data);
      setLoading(false);
    };
    fetchChain();
  }, [symbol, selectedExpiration, getOptionsChain]);

  const formatNumber = (num, decimals = 2) => {
    if (num === null || num === undefined) return '—';
    return num.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
  };

  const formatPercent = (num) => {
    if (num === null || num === undefined) return '—';
    return `${(num * 100).toFixed(1)}%`;
  };

  if (loading && !optionsData) {
    return (
      <Card className="nexus-card">
        <CardHeader className="card-header-terminal">
          <CardTitle className="card-header-title flex items-center gap-2">
            <BarChart2 className="w-4 h-4 text-orange-500" />
            Options Chain - {symbol}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          <div className="flex items-center justify-center h-32">
            <div className="w-6 h-6 border-2 border-orange-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!optionsData) {
    return (
      <Card className="nexus-card">
        <CardHeader className="card-header-terminal">
          <CardTitle className="card-header-title flex items-center gap-2">
            <BarChart2 className="w-4 h-4 text-orange-500" />
            Options Chain - {symbol}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-4">
          <p className="text-zinc-500 text-center">No options data available for {symbol}</p>
        </CardContent>
      </Card>
    );
  }

  const renderOptionsTable = (options, type) => (
    <ScrollArea className="h-[400px]">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent border-zinc-800">
            <TableHead className="text-[10px] text-zinc-500 font-medium">Strike</TableHead>
            <TableHead className="text-[10px] text-zinc-500 font-medium">Last</TableHead>
            <TableHead className="text-[10px] text-zinc-500 font-medium">Bid</TableHead>
            <TableHead className="text-[10px] text-zinc-500 font-medium">Ask</TableHead>
            <TableHead className="text-[10px] text-zinc-500 font-medium">Vol</TableHead>
            <TableHead className="text-[10px] text-zinc-500 font-medium">OI</TableHead>
            <TableHead className="text-[10px] text-zinc-500 font-medium">IV</TableHead>
            <TableHead className="text-[10px] text-zinc-500 font-medium">ITM</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {options.map((opt, i) => {
            const isITM = opt.in_the_money;
            return (
              <TableRow 
                key={i} 
                className={`hover:bg-zinc-800/50 border-zinc-800/50 ${isITM ? 'bg-zinc-800/30' : ''}`}
              >
                <TableCell className="font-mono text-xs py-2">
                  <span className={isITM ? 'text-orange-400' : 'text-white'}>
                    {formatNumber(opt.strike)}
                  </span>
                </TableCell>
                <TableCell className="font-mono text-xs py-2 text-white">
                  {formatNumber(opt.last_price)}
                </TableCell>
                <TableCell className="font-mono text-xs py-2 text-emerald-500">
                  {formatNumber(opt.bid)}
                </TableCell>
                <TableCell className="font-mono text-xs py-2 text-red-500">
                  {formatNumber(opt.ask)}
                </TableCell>
                <TableCell className="font-mono text-xs py-2 text-zinc-400">
                  {opt.volume?.toLocaleString() || '—'}
                </TableCell>
                <TableCell className="font-mono text-xs py-2 text-zinc-400">
                  {opt.open_interest?.toLocaleString() || '—'}
                </TableCell>
                <TableCell className="font-mono text-xs py-2 text-blue-400">
                  {formatPercent(opt.implied_volatility)}
                </TableCell>
                <TableCell className="py-2">
                  {isITM ? (
                    <Badge className="bg-emerald-500/20 text-emerald-500 text-[9px] rounded-none">ITM</Badge>
                  ) : (
                    <Badge className="bg-zinc-500/20 text-zinc-500 text-[9px] rounded-none">OTM</Badge>
                  )}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </ScrollArea>
  );

  return (
    <Card className="nexus-card" data-testid="options-chain-card">
      <CardHeader className="card-header-terminal">
        <CardTitle className="card-header-title flex items-center gap-2">
          <BarChart2 className="w-4 h-4 text-orange-500" />
          Options Chain - {symbol}
        </CardTitle>
        <div className="flex items-center gap-3">
          {optionsData.underlying_price && (
            <span className="text-xs text-zinc-400">
              Spot: <span className="font-mono text-white">${formatNumber(optionsData.underlying_price)}</span>
            </span>
          )}
          <Select value={selectedExpiration} onValueChange={setSelectedExpiration}>
            <SelectTrigger className="w-[140px] h-7 text-xs bg-zinc-900 border-zinc-800" data-testid="expiration-select">
              <SelectValue placeholder="Expiration" />
            </SelectTrigger>
            <SelectContent className="bg-zinc-900 border-zinc-800">
              {expirations.map((exp) => (
                <SelectItem key={exp} value={exp} className="text-xs">
                  {new Date(exp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' })}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-zinc-900 rounded-none h-8">
            <TabsTrigger 
              value="calls" 
              className="text-xs rounded-none data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-500"
              data-testid="calls-tab"
            >
              <TrendingUp className="w-3 h-3 mr-1" />
              Calls ({optionsData.calls?.length || 0})
            </TabsTrigger>
            <TabsTrigger 
              value="puts" 
              className="text-xs rounded-none data-[state=active]:bg-red-500/20 data-[state=active]:text-red-500"
              data-testid="puts-tab"
            >
              <TrendingDown className="w-3 h-3 mr-1" />
              Puts ({optionsData.puts?.length || 0})
            </TabsTrigger>
          </TabsList>
          <TabsContent value="calls" className="mt-0">
            {renderOptionsTable(optionsData.calls || [], 'call')}
          </TabsContent>
          <TabsContent value="puts" className="mt-0">
            {renderOptionsTable(optionsData.puts || [], 'put')}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};

export default OptionsChain;
