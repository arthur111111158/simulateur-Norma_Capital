import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/tabs';
import { ScrollArea } from '../components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Checkbox } from '../components/ui/checkbox';
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown,
  RefreshCw,
  Loader2,
  ArrowRightLeft,
  Calculator,
  Globe
} from 'lucide-react';

const ForexPage = () => {
  const navigate = useNavigate();
  const { getForexPairs, getCurrencies, convertCurrency } = useApp();
  const [pairs, setPairs] = useState([]);
  const [pairsByBase, setPairsByBase] = useState({});
  const [currencies, setCurrencies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('pairs');
  const [selectedPair, setSelectedPair] = useState(null);
  
  // Converter state
  const [amount, setAmount] = useState('1000');
  const [fromCurrency, setFromCurrency] = useState('EUR');
  const [selectedTargets, setSelectedTargets] = useState(['USD', 'GBP', 'JPY', 'CHF', 'CNY']);
  const [conversions, setConversions] = useState(null);
  const [converting, setConverting] = useState(false);

  // Load forex data
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      const [pairsData, currenciesData] = await Promise.all([
        getForexPairs(),
        getCurrencies()
      ]);
      setPairs(pairsData.pairs || []);
      setPairsByBase(pairsData.by_base_currency || {});
      setCurrencies(currenciesData.currencies || []);
      setLoading(false);
    };
    loadData();
  }, [getForexPairs, getCurrencies]);

  // Refresh data
  const refreshData = async () => {
    setLoading(true);
    const data = await getForexPairs();
    setPairs(data.pairs || []);
    setPairsByBase(data.by_base_currency || {});
    setLoading(false);
  };

  // Handle conversion
  const handleConvert = async () => {
    if (!amount || selectedTargets.length === 0) return;
    
    setConverting(true);
    const result = await convertCurrency(
      parseFloat(amount),
      fromCurrency,
      selectedTargets
    );
    setConversions(result);
    setConverting(false);
  };

  // Toggle target currency
  const toggleTarget = (currency) => {
    if (currency === fromCurrency) return;
    setSelectedTargets(prev => 
      prev.includes(currency) 
        ? prev.filter(c => c !== currency)
        : [...prev, currency]
    );
  };

  // Format rate
  const formatRate = (rate) => {
    if (rate === null || rate === undefined) return '—';
    if (rate >= 100) return rate.toFixed(2);
    if (rate >= 1) return rate.toFixed(4);
    return rate.toFixed(6);
  };

  // Format amount
  const formatAmount = (amount, currency) => {
    if (amount === null || amount === undefined) return '—';
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };

  // Major currencies for quick selection
  const majorCurrencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'CNY'];

  return (
    <div className="space-y-4" data-testid="forex-page">
      {/* Header */}
      <Card className="nexus-card">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-emerald-500/20 rounded-sm flex items-center justify-center">
                <DollarSign className="w-5 h-5 text-emerald-500" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-white">Forex</h1>
                <p className="text-sm text-zinc-500">Currency exchange rates and converter</p>
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
                  {pairs.length} PAIRS
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-zinc-900 h-10 p-1">
          <TabsTrigger 
            value="pairs" 
            className="text-xs px-6 data-[state=active]:bg-zinc-800"
            data-testid="tab-pairs"
          >
            <Globe className="w-3 h-3 mr-2" />
            Currency Pairs
          </TabsTrigger>
          <TabsTrigger 
            value="converter" 
            className="text-xs px-6 data-[state=active]:bg-zinc-800"
            data-testid="tab-converter"
          >
            <Calculator className="w-3 h-3 mr-2" />
            Currency Converter
          </TabsTrigger>
        </TabsList>

        {/* Pairs Tab */}
        <TabsContent value="pairs" className="mt-4">
          <div className="grid grid-cols-12 gap-4">
            {/* Pairs List */}
            <div className="col-span-8">
              <Card className="nexus-card">
                <CardHeader className="card-header-terminal">
                  <CardTitle className="card-header-title">Exchange Rates</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  {loading ? (
                    <div className="flex items-center justify-center h-64">
                      <Loader2 className="w-6 h-6 animate-spin text-emerald-500" />
                    </div>
                  ) : (
                    <ScrollArea className="h-[600px]">
                      <div className="divide-y divide-zinc-800/50">
                        {pairs.map((pair, i) => {
                          const isPositive = pair.change_percent >= 0;
                          const isSelected = selectedPair?.symbol === pair.symbol;
                          
                          return (
                            <div 
                              key={pair.symbol}
                              className={`p-4 hover:bg-zinc-800/30 cursor-pointer transition-colors ${isSelected ? 'bg-zinc-800/50' : ''}`}
                              onClick={() => setSelectedPair(pair)}
                              data-testid={`pair-${pair.symbol}`}
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                  <div className="w-10 h-10 rounded-sm flex items-center justify-center bg-zinc-800">
                                    <ArrowRightLeft className="w-5 h-5 text-emerald-500" />
                                  </div>
                                  <div>
                                    <h3 className="font-medium text-white">{pair.name}</h3>
                                    <span className="text-xs text-zinc-500">{pair.base} / {pair.quote}</span>
                                  </div>
                                </div>
                                
                                <div className="text-right">
                                  <p className="font-mono text-lg text-white">
                                    {formatRate(pair.rate)}
                                  </p>
                                  <div className="flex items-center justify-end gap-2 mt-0.5">
                                    <Badge className={`rounded-none text-xs ${isPositive ? 'bg-emerald-500/20 text-emerald-500' : 'bg-red-500/20 text-red-500'}`}>
                                      {isPositive ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                                      {isPositive ? '+' : ''}{pair.change_percent?.toFixed(2)}%
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

            {/* Selected Pair Details */}
            <div className="col-span-4">
              {selectedPair ? (
                <Card className="nexus-card border-emerald-500/30">
                  <CardHeader className="card-header-terminal">
                    <CardTitle className="card-header-title">{selectedPair.name}</CardTitle>
                  </CardHeader>
                  <CardContent className="p-4">
                    <div className="space-y-4">
                      {/* Rate */}
                      <div className="text-center py-4 bg-zinc-900 rounded-sm">
                        <p className="font-mono text-3xl text-white">
                          {formatRate(selectedPair.rate)}
                        </p>
                        <p className="text-xs text-zinc-500 mt-1">
                          1 {selectedPair.base} = {formatRate(selectedPair.rate)} {selectedPair.quote}
                        </p>
                        <Badge className={`mt-2 rounded-none ${selectedPair.change_percent >= 0 ? 'bg-emerald-500/20 text-emerald-500' : 'bg-red-500/20 text-red-500'}`}>
                          {selectedPair.change_percent >= 0 ? '+' : ''}{selectedPair.change_percent?.toFixed(2)}%
                        </Badge>
                      </div>

                      {/* Details */}
                      <div className="space-y-2">
                        <div className="flex justify-between items-center py-2 border-b border-zinc-800/50">
                          <span className="text-sm text-zinc-400">Bid</span>
                          <span className="font-mono text-sm text-emerald-500">{formatRate(selectedPair.bid)}</span>
                        </div>
                        <div className="flex justify-between items-center py-2 border-b border-zinc-800/50">
                          <span className="text-sm text-zinc-400">Ask</span>
                          <span className="font-mono text-sm text-red-500">{formatRate(selectedPair.ask)}</span>
                        </div>
                        <div className="flex justify-between items-center py-2 border-b border-zinc-800/50">
                          <span className="text-sm text-zinc-400">Spread</span>
                          <span className="font-mono text-sm text-white">
                            {selectedPair.bid && selectedPair.ask 
                              ? ((selectedPair.ask - selectedPair.bid) * 10000).toFixed(1) + ' pips'
                              : '—'}
                          </span>
                        </div>
                        <div className="flex justify-between items-center py-2 border-b border-zinc-800/50">
                          <span className="text-sm text-zinc-400">High</span>
                          <span className="font-mono text-sm text-emerald-500">{formatRate(selectedPair.high)}</span>
                        </div>
                        <div className="flex justify-between items-center py-2 border-b border-zinc-800/50">
                          <span className="text-sm text-zinc-400">Low</span>
                          <span className="font-mono text-sm text-red-500">{formatRate(selectedPair.low)}</span>
                        </div>
                      </div>

                      {/* Actions */}
                      <Button 
                        className="w-full bg-emerald-500/20 text-emerald-500 hover:bg-emerald-500/30"
                        onClick={() => navigate(`/quote?symbol=${selectedPair.symbol}`)}
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
                      <ArrowRightLeft className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>Select a pair to view details</p>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>

        {/* Converter Tab */}
        <TabsContent value="converter" className="mt-4">
          <div className="grid grid-cols-12 gap-4">
            {/* Converter Form */}
            <div className="col-span-5">
              <Card className="nexus-card">
                <CardHeader className="card-header-terminal">
                  <CardTitle className="card-header-title flex items-center gap-2">
                    <Calculator className="w-4 h-4 text-emerald-500" />
                    Currency Converter
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-4">
                  <div className="space-y-4">
                    {/* Amount Input */}
                    <div>
                      <label className="text-xs text-zinc-500 uppercase mb-2 block">Amount</label>
                      <Input
                        type="number"
                        value={amount}
                        onChange={(e) => setAmount(e.target.value)}
                        className="bg-zinc-900 border-zinc-800 font-mono text-lg h-12"
                        placeholder="Enter amount"
                        data-testid="amount-input"
                      />
                    </div>

                    {/* From Currency */}
                    <div>
                      <label className="text-xs text-zinc-500 uppercase mb-2 block">From Currency</label>
                      <Select value={fromCurrency} onValueChange={setFromCurrency}>
                        <SelectTrigger className="bg-zinc-900 border-zinc-800 h-12" data-testid="from-currency-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent className="bg-zinc-900 border-zinc-800 max-h-64">
                          {currencies.map(currency => (
                            <SelectItem key={currency.code} value={currency.code}>
                              <span className="mr-2">{currency.flag}</span>
                              {currency.code} - {currency.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Quick Select Major Currencies */}
                    <div>
                      <label className="text-xs text-zinc-500 uppercase mb-2 block">Quick Select</label>
                      <div className="flex flex-wrap gap-2">
                        {majorCurrencies.map(curr => (
                          <Button
                            key={curr}
                            variant={fromCurrency === curr ? "default" : "outline"}
                            size="sm"
                            className="h-8"
                            onClick={() => setFromCurrency(curr)}
                          >
                            {curr}
                          </Button>
                        ))}
                      </div>
                    </div>

                    {/* Convert Button */}
                    <Button 
                      className="w-full h-12 bg-emerald-500 hover:bg-emerald-600 text-black font-medium"
                      onClick={handleConvert}
                      disabled={converting || !amount || selectedTargets.length === 0}
                      data-testid="convert-button"
                    >
                      {converting ? (
                        <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      ) : (
                        <ArrowRightLeft className="w-4 h-4 mr-2" />
                      )}
                      Convert to {selectedTargets.length} Currencies
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Target Currencies Selection */}
              <Card className="nexus-card mt-4">
                <CardHeader className="card-header-terminal">
                  <CardTitle className="card-header-title">Target Currencies</CardTitle>
                </CardHeader>
                <CardContent className="p-3">
                  <ScrollArea className="h-[250px]">
                    <div className="space-y-1">
                      {currencies.map(currency => {
                        const isSelected = selectedTargets.includes(currency.code);
                        const isSource = currency.code === fromCurrency;
                        
                        return (
                          <div 
                            key={currency.code}
                            className={`flex items-center justify-between p-2 rounded-sm cursor-pointer transition-colors
                              ${isSource ? 'opacity-50 cursor-not-allowed' : 'hover:bg-zinc-800'}
                              ${isSelected && !isSource ? 'bg-emerald-500/10' : ''}
                            `}
                            onClick={() => !isSource && toggleTarget(currency.code)}
                          >
                            <div className="flex items-center gap-2">
                              <Checkbox 
                                checked={isSelected} 
                                disabled={isSource}
                                className="data-[state=checked]:bg-emerald-500"
                              />
                              <span className="text-lg">{currency.flag}</span>
                              <span className="text-sm text-white">{currency.code}</span>
                              <span className="text-xs text-zinc-500">{currency.name}</span>
                            </div>
                            {isSource && (
                              <Badge className="bg-zinc-700 text-zinc-300 rounded-none text-[9px]">SOURCE</Badge>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </div>

            {/* Conversion Results */}
            <div className="col-span-7">
              <Card className="nexus-card h-full">
                <CardHeader className="card-header-terminal">
                  <CardTitle className="card-header-title">Conversion Results</CardTitle>
                </CardHeader>
                <CardContent className="p-4">
                  {conversions ? (
                    <div className="space-y-4">
                      {/* Source Amount */}
                      <div className="p-4 bg-zinc-900 rounded-sm text-center">
                        <p className="text-xs text-zinc-500 uppercase">Converting</p>
                        <p className="font-mono text-3xl text-white mt-1">
                          {conversions.source.currency_info?.symbol || ''} {formatAmount(conversions.source.amount)}
                        </p>
                        <p className="text-sm text-zinc-400 mt-1">
                          {conversions.source.currency_info?.flag} {conversions.source.currency} - {conversions.source.currency_info?.name}
                        </p>
                      </div>

                      {/* Results */}
                      <ScrollArea className="h-[400px]">
                        <div className="space-y-2">
                          {conversions.conversions.map((conv, i) => (
                            <div 
                              key={conv.to}
                              className="p-4 bg-zinc-900 rounded-sm"
                              data-testid={`conversion-result-${conv.to}`}
                            >
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                  <span className="text-2xl">{conv.currency_info?.flag}</span>
                                  <div>
                                    <p className="font-medium text-white">{conv.to}</p>
                                    <p className="text-xs text-zinc-500">{conv.currency_info?.name}</p>
                                  </div>
                                </div>
                                <div className="text-right">
                                  {conv.error ? (
                                    <p className="text-red-500 text-sm">Error</p>
                                  ) : (
                                    <>
                                      <p className="font-mono text-xl text-emerald-500">
                                        {conv.currency_info?.symbol || ''} {formatAmount(conv.converted)}
                                      </p>
                                      <p className="text-xs text-zinc-500">
                                        Rate: {formatRate(conv.rate)}
                                      </p>
                                    </>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </ScrollArea>

                      {/* Timestamp */}
                      <p className="text-[10px] text-zinc-500 text-center">
                        Last updated: {new Date(conversions.timestamp).toLocaleString()}
                      </p>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-[500px] text-zinc-500">
                      <Calculator className="w-16 h-16 mb-4 opacity-50" />
                      <p className="text-lg">Enter an amount and click Convert</p>
                      <p className="text-sm mt-2">Select target currencies from the list</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ForexPage;
