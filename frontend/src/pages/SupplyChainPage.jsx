import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import ReactFlow, { 
  Background, 
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Handle,
  Position
} from 'reactflow';
import 'reactflow/dist/style.css';
import { 
  GitBranch, 
  Search, 
  Building, 
  Factory, 
  Users, 
  AlertTriangle,
  Globe,
  ArrowLeft,
  ExternalLink
} from 'lucide-react';

// Custom node component
const CustomNode = ({ data }) => {
  const getRiskColor = (risk) => {
    switch (risk) {
      case 'critical': return 'border-red-500 bg-red-500/10';
      case 'high': return 'border-orange-500 bg-orange-500/10';
      case 'medium': return 'border-yellow-500 bg-yellow-500/10';
      default: return 'border-emerald-500 bg-emerald-500/10';
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case 'company': return Building;
      case 'supplier': return Factory;
      case 'customer': return Users;
      default: return Building;
    }
  };

  const Icon = getIcon(data.nodeType);

  return (
    <div 
      className={`px-3 py-2 rounded-sm border-2 ${getRiskColor(data.risk)} bg-zinc-900 min-w-[180px] cursor-pointer hover:border-opacity-100 transition-all`}
      data-testid={`node-${data.id}`}
    >
      {/* Left handle for incoming connections */}
      <Handle
        type="target"
        position={Position.Left}
        style={{ background: '#3f3f46', border: '2px solid #52525b' }}
      />
      
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4 text-zinc-400" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white truncate">{data.label}</p>
          {data.symbol && (
            <p className="font-mono text-[10px] text-orange-500">{data.symbol}</p>
          )}
        </div>
      </div>
      <div className="flex items-center justify-between mt-2 pt-2 border-t border-zinc-800">
        <div className="flex items-center gap-1">
          <Globe className="w-3 h-3 text-zinc-500" />
          <span className="text-[10px] text-zinc-500">{data.country}</span>
        </div>
        <Badge className={`badge-${data.risk} rounded-none text-[9px] px-1 py-0`}>
          {data.risk}
        </Badge>
      </div>
      {data.dependency && (
        <div className="mt-1">
          <div className="w-full h-1 bg-zinc-800 rounded-full overflow-hidden">
            <div 
              className="h-full bg-orange-500 rounded-full"
              style={{ width: `${data.dependency}%` }}
            ></div>
          </div>
          <p className="text-[9px] text-zinc-500 mt-0.5">{data.dependency}% dependency</p>
        </div>
      )}
      
      {/* Right handle for outgoing connections */}
      <Handle
        type="source"
        position={Position.Right}
        style={{ background: '#3f3f46', border: '2px solid #52525b' }}
      />
    </div>
  );
};

const nodeTypes = {
  custom: CustomNode,
};

const SupplyChainPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { getSupplyChain, searchAssets, getQuote, conflicts } = useApp();
  
  const [symbol, setSymbol] = useState(searchParams.get('symbol') || 'AAPL');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [supplyChain, setSupplyChain] = useState([]);
  const [companyInfo, setCompanyInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Fetch supply chain data
  const fetchData = useCallback(async () => {
    setLoading(true);
    const [chainData, quoteData] = await Promise.all([
      getSupplyChain(symbol),
      getQuote(symbol)
    ]);
    setSupplyChain(chainData);
    setCompanyInfo(quoteData);
    setLoading(false);
  }, [symbol, getSupplyChain, getQuote]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Handle search
  useEffect(() => {
    const search = async () => {
      if (searchQuery.length > 0) {
        const results = await searchAssets(searchQuery);
        setSearchResults(results.filter(r => r.type === 'stock'));
      } else {
        setSearchResults([]);
      }
    };
    const debounce = setTimeout(search, 300);
    return () => clearTimeout(debounce);
  }, [searchQuery, searchAssets]);

  // Build graph nodes and edges
  useEffect(() => {
    if (!companyInfo || supplyChain.length === 0) {
      setNodes([]);
      setEdges([]);
      return;
    }

    const newNodes = [];
    const newEdges = [];

    // Center node (main company)
    newNodes.push({
      id: 'center',
      type: 'custom',
      position: { x: 400, y: 300 },
      data: {
        id: 'center',
        label: companyInfo.name || symbol,
        symbol: symbol,
        nodeType: 'company',
        country: 'USA',
        risk: 'low',
      }
    });

    // Suppliers (left side)
    const suppliers = supplyChain.filter(n => n.relationship === 'supplier');
    suppliers.forEach((supplier, i) => {
      const nodeId = `supplier-${supplier.id}`;
      const yOffset = (i - suppliers.length / 2) * 120;
      
      // Check if affected by any conflict
      const isAffected = conflicts.some(c => 
        c.affected_assets?.includes(supplier.symbol) ||
        supplier.country === c.country
      );
      
      newNodes.push({
        id: nodeId,
        type: 'custom',
        position: { x: 50, y: 300 + yOffset },
        data: {
          id: supplier.id,
          label: supplier.name,
          symbol: supplier.symbol,
          nodeType: 'supplier',
          country: supplier.country,
          risk: isAffected ? 'high' : supplier.risk_level,
          dependency: supplier.dependency_percent,
        }
      });

      newEdges.push({
        id: `e-${nodeId}-center`,
        source: nodeId,
        target: 'center',
        animated: supplier.risk_level === 'critical' || supplier.risk_level === 'high',
        style: { 
          stroke: supplier.risk_level === 'critical' ? '#ef4444' : 
                  supplier.risk_level === 'high' ? '#f97316' : '#3f3f46',
          strokeWidth: 2
        },
        label: supplier.dependency_percent ? `${supplier.dependency_percent}%` : '',
        labelStyle: { fill: '#71717a', fontSize: 10 },
        labelBgStyle: { fill: '#18181b' }
      });
    });

    // Customers (right side)
    const customers = supplyChain.filter(n => n.relationship === 'customer');
    customers.forEach((customer, i) => {
      const nodeId = `customer-${customer.id}`;
      const yOffset = (i - customers.length / 2) * 120;
      
      newNodes.push({
        id: nodeId,
        type: 'custom',
        position: { x: 750, y: 300 + yOffset },
        data: {
          id: customer.id,
          label: customer.name,
          symbol: customer.symbol,
          nodeType: 'customer',
          country: customer.country,
          risk: customer.risk_level,
          dependency: customer.dependency_percent,
        }
      });

      newEdges.push({
        id: `e-center-${nodeId}`,
        source: 'center',
        target: nodeId,
        style: { stroke: '#3f3f46', strokeWidth: 2 },
        label: customer.dependency_percent ? `${customer.dependency_percent}%` : '',
        labelStyle: { fill: '#71717a', fontSize: 10 },
        labelBgStyle: { fill: '#18181b' }
      });
    });

    setNodes(newNodes);
    setEdges(newEdges);
  }, [supplyChain, companyInfo, symbol, conflicts, setNodes, setEdges]);

  // Handle node click
  const onNodeClick = useCallback((event, node) => {
    if (node.data.symbol && node.id !== 'center') {
      setSelectedNode(node.data);
    }
  }, []);

  // Select asset from search
  const handleSelectAsset = (asset) => {
    setSymbol(asset.symbol);
    setSearchQuery('');
    setSearchResults([]);
    navigate(`/supplychain?symbol=${asset.symbol}`);
  };

  // Risk summary
  const riskSummary = useMemo(() => {
    const suppliers = supplyChain.filter(n => n.relationship === 'supplier');
    return {
      critical: suppliers.filter(s => s.risk_level === 'critical').length,
      high: suppliers.filter(s => s.risk_level === 'high').length,
      medium: suppliers.filter(s => s.risk_level === 'medium').length,
      low: suppliers.filter(s => s.risk_level === 'low').length,
    };
  }, [supplyChain]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[80vh]">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-zinc-500 text-sm mt-4">Loading supply chain data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="supplychain-page">
      {/* Header */}
      <Card className="nexus-card">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-orange-500/20 rounded-sm flex items-center justify-center">
                <GitBranch className="w-5 h-5 text-orange-500" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-white">Supply Chain Graph</h1>
                <p className="text-sm text-zinc-500">Company relationships, dependencies & risk analysis</p>
              </div>
            </div>

            {/* Search */}
            <div className="relative w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
              <Input
                type="text"
                placeholder="Search company..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 bg-zinc-900 border-zinc-800"
                data-testid="supplychain-search"
              />
              {searchResults.length > 0 && (
                <div className="absolute top-full left-0 mt-1 w-full bg-zinc-900 border border-zinc-800 rounded-sm z-50 shadow-lg">
                  {searchResults.map((result, i) => (
                    <div
                      key={i}
                      className="px-4 py-2 hover:bg-zinc-800 cursor-pointer"
                      onClick={() => handleSelectAsset(result)}
                    >
                      <span className="font-mono text-white">{result.symbol}</span>
                      <span className="text-zinc-500 text-sm ml-2">{result.name}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Company Info Bar */}
      {companyInfo && (
        <Card className="nexus-card">
          <CardContent className="p-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-white">{companyInfo.name}</h2>
                  <p className="font-mono text-sm text-orange-500">{symbol}</p>
                </div>
                <div className="h-8 w-px bg-zinc-800"></div>
                <div>
                  <p className="text-[10px] text-zinc-500 uppercase">Suppliers</p>
                  <p className="font-mono text-lg text-white">{supplyChain.filter(n => n.relationship === 'supplier').length}</p>
                </div>
                <div>
                  <p className="text-[10px] text-zinc-500 uppercase">Customers</p>
                  <p className="font-mono text-lg text-white">{supplyChain.filter(n => n.relationship === 'customer').length}</p>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-zinc-500">Risk Distribution:</span>
                  {riskSummary.critical > 0 && (
                    <Badge className="badge-critical rounded-none text-xs">{riskSummary.critical} Critical</Badge>
                  )}
                  {riskSummary.high > 0 && (
                    <Badge className="badge-high rounded-none text-xs">{riskSummary.high} High</Badge>
                  )}
                  {riskSummary.medium > 0 && (
                    <Badge className="badge-medium rounded-none text-xs">{riskSummary.medium} Medium</Badge>
                  )}
                  {riskSummary.low > 0 && (
                    <Badge className="badge-low rounded-none text-xs">{riskSummary.low} Low</Badge>
                  )}
                </div>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => navigate(`/quote?symbol=${symbol}`)}
                >
                  <ExternalLink className="w-4 h-4 mr-2" />
                  View Quote
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-12 gap-4">
        {/* Graph */}
        <div className="col-span-9">
          <Card className="nexus-card overflow-hidden">
            <CardContent className="p-0">
              <div style={{ height: '600px' }}>
                {nodes.length > 0 ? (
                  <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onNodeClick={onNodeClick}
                    nodeTypes={nodeTypes}
                    fitView
                    minZoom={0.5}
                    maxZoom={2}
                    defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
                  >
                    <Background color="#27272a" gap={20} size={1} />
                    <Controls 
                      style={{ 
                        backgroundColor: '#18181b', 
                        borderColor: '#27272a',
                        borderRadius: '2px'
                      }}
                    />
                    <MiniMap 
                      style={{ backgroundColor: '#09090b' }}
                      nodeColor={(node) => {
                        if (node.data?.risk === 'critical') return '#ef4444';
                        if (node.data?.risk === 'high') return '#f97316';
                        if (node.data?.risk === 'medium') return '#eab308';
                        return '#22c55e';
                      }}
                    />
                  </ReactFlow>
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <p className="text-zinc-500">No supply chain data available for {symbol}</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="col-span-3 space-y-4">
          {/* Selected Node Detail */}
          {selectedNode ? (
            <Card className="nexus-card border-orange-500/50">
              <CardHeader className="card-header-terminal">
                <CardTitle className="card-header-title">Node Details</CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0"
                  onClick={() => setSelectedNode(null)}
                >
                  <ArrowLeft className="w-4 h-4" />
                </Button>
              </CardHeader>
              <CardContent className="p-4">
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-medium text-white">{selectedNode.label}</h3>
                    {selectedNode.symbol && (
                      <p className="font-mono text-sm text-orange-500">{selectedNode.symbol}</p>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div className="p-2 bg-zinc-900 rounded-sm">
                      <p className="text-[10px] text-zinc-500 uppercase">Country</p>
                      <p className="text-sm text-white">{selectedNode.country}</p>
                    </div>
                    <div className="p-2 bg-zinc-900 rounded-sm">
                      <p className="text-[10px] text-zinc-500 uppercase">Risk Level</p>
                      <Badge className={`badge-${selectedNode.risk} rounded-none text-xs mt-1`}>
                        {selectedNode.risk}
                      </Badge>
                    </div>
                  </div>

                  {selectedNode.dependency && (
                    <div>
                      <p className="text-[10px] text-zinc-500 uppercase mb-1">Dependency</p>
                      <div className="w-full h-2 bg-zinc-800 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-orange-500 rounded-full"
                          style={{ width: `${selectedNode.dependency}%` }}
                        ></div>
                      </div>
                      <p className="text-xs text-zinc-400 mt-1">{selectedNode.dependency}%</p>
                    </div>
                  )}

                  {selectedNode.symbol && (
                    <Button 
                      className="w-full"
                      onClick={() => navigate(`/quote?symbol=${selectedNode.symbol}`)}
                    >
                      View {selectedNode.symbol} Quote
                    </Button>
                  )}

                  <Button 
                    variant="outline"
                    className="w-full"
                    onClick={() => {
                      if (selectedNode.symbol) {
                        setSymbol(selectedNode.symbol);
                        setSelectedNode(null);
                        navigate(`/supplychain?symbol=${selectedNode.symbol}`);
                      }
                    }}
                    disabled={!selectedNode.symbol}
                  >
                    <GitBranch className="w-4 h-4 mr-2" />
                    View Supply Chain
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="nexus-card">
              <CardHeader className="card-header-terminal">
                <CardTitle className="card-header-title flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-orange-500" />
                  Risk Overview
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-zinc-400">Critical Risk</span>
                    <span className="font-mono text-lg text-red-500">{riskSummary.critical}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-zinc-400">High Risk</span>
                    <span className="font-mono text-lg text-orange-500">{riskSummary.high}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-zinc-400">Medium Risk</span>
                    <span className="font-mono text-lg text-yellow-500">{riskSummary.medium}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-zinc-400">Low Risk</span>
                    <span className="font-mono text-lg text-emerald-500">{riskSummary.low}</span>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-zinc-800">
                  <p className="text-xs text-zinc-500 mb-2">Click on a node to see details</p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Legend */}
          <Card className="nexus-card">
            <CardHeader className="card-header-terminal py-2">
              <CardTitle className="card-header-title">Legend</CardTitle>
            </CardHeader>
            <CardContent className="p-3">
              <div className="space-y-2 text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-sm bg-zinc-900 border-2 border-emerald-500"></div>
                  <span className="text-zinc-400">Low Risk</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-sm bg-zinc-900 border-2 border-yellow-500"></div>
                  <span className="text-zinc-400">Medium Risk</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-sm bg-zinc-900 border-2 border-orange-500"></div>
                  <span className="text-zinc-400">High Risk</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-sm bg-zinc-900 border-2 border-red-500"></div>
                  <span className="text-zinc-400">Critical Risk</span>
                </div>
                <div className="flex items-center gap-2 mt-3 pt-2 border-t border-zinc-800">
                  <Factory className="w-4 h-4 text-zinc-500" />
                  <span className="text-zinc-400">Supplier</span>
                </div>
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-zinc-500" />
                  <span className="text-zinc-400">Customer</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default SupplyChainPage;
