import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useApp } from '../context/AppContext';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { ScrollArea } from '../components/ui/scroll-area';
import { Tabs, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  ComposableMap, 
  Geographies, 
  Geography, 
  Marker,
  Line,
  ZoomableGroup 
} from 'react-simple-maps';
import { 
  Globe, 
  AlertTriangle, 
  TrendingDown,
  TrendingUp,
  Flame,
  Shield,
  Ship,
  Plane,
  Anchor,
  X,
  ChevronRight,
  MapPin,
  Route,
  Users,
  DollarSign,
  Building2,
  Flag,
  Loader2,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Newspaper,
  TrendingUp as Trending
} from 'lucide-react';

const geoUrl = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

// Country ISO code mapping from geo properties
const GEO_NAME_TO_ISO = {
  "United States of America": "US", "United States": "US",
  "United Kingdom": "GB", "France": "FR", "Germany": "DE",
  "Italy": "IT", "Spain": "ES", "Portugal": "PT", "Netherlands": "NL",
  "Belgium": "BE", "Switzerland": "CH", "Austria": "AT", "Poland": "PL",
  "Sweden": "SE", "Norway": "NO", "Denmark": "DK", "Finland": "FI",
  "Ireland": "IE", "Greece": "GR", "Czech Republic": "CZ", "Czechia": "CZ",
  "Romania": "RO", "Hungary": "HU", "Ukraine": "UA", "Russia": "RU",
  "China": "CN", "Japan": "JP", "South Korea": "KR", "North Korea": "KP",
  "India": "IN", "Pakistan": "PK", "Bangladesh": "BD", "Indonesia": "ID",
  "Malaysia": "MY", "Thailand": "TH", "Vietnam": "VN", "Philippines": "PH",
  "Singapore": "SG", "Australia": "AU", "New Zealand": "NZ",
  "Brazil": "BR", "Argentina": "AR", "Mexico": "MX", "Canada": "CA",
  "Colombia": "CO", "Chile": "CL", "Peru": "PE", "Venezuela": "VE",
  "Egypt": "EG", "South Africa": "ZA", "Nigeria": "NG", "Kenya": "KE",
  "Morocco": "MA", "Algeria": "DZ", "Tunisia": "TN", "Ethiopia": "ET",
  "Saudi Arabia": "SA", "United Arab Emirates": "AE", "Israel": "IL",
  "Turkey": "TR", "Iran": "IR", "Iraq": "IQ", "Syria": "SY",
  "Taiwan": "TW", "Hong Kong": "HK",
};

// Country coordinates for conflict markers
const countryCoordinates = {
  'Ukraine': [31.1656, 48.3794],
  'Yemen': [42.5, 13.5],
  'Taiwan': [121.0, 24.0],
  'Iran': [53.6880, 32.4279],
  'Philippines': [114.0, 12.0],
  'Russia': [105.3188, 61.5240],
  'China': [104.1954, 35.8617],
  'Syria': [38.9968, 34.8021],
  'Israel': [35.2137, 31.7683],
  'North Korea': [127.5101, 40.3399],
};

const WorldMapPage = () => {
  const { conflicts, news, getShippingRoutes, getShippingPorts, getShippingStats, getCountryData } = useApp();
  const navigate = useNavigate();
  const [selectedConflict, setSelectedConflict] = useState(null);
  const [hoveredConflict, setHoveredConflict] = useState(null);
  const [zoom, setZoom] = useState(1);
  const [center, setCenter] = useState([20, 20]);
  
  // Shipping state
  const [shippingRoutes, setShippingRoutes] = useState([]);
  const [shippingPorts, setShippingPorts] = useState({ seaports: [], airports: [] });
  const [shippingStats, setShippingStats] = useState(null);
  const [activeLayer, setActiveLayer] = useState('all');
  const [showPorts, setShowPorts] = useState(true);
  const [hoveredRoute, setHoveredRoute] = useState(null);
  const [selectedRoute, setSelectedRoute] = useState(null);
  
  // Country state
  const [selectedCountry, setSelectedCountry] = useState(null);
  const [countryData, setCountryData] = useState(null);
  const [loadingCountry, setLoadingCountry] = useState(false);
  const [hoveredCountry, setHoveredCountry] = useState(null);

  // News hotspots - countries most mentioned in news
  const newsHotspots = useMemo(() => {
    const countryMentions = {};
    const countryToCoords = {
      'US': [-95, 38], 'USA': [-95, 38], 'United States': [-95, 38], 'America': [-95, 38],
      'China': [104, 35], 'Chinese': [104, 35],
      'Russia': [100, 60], 'Russian': [100, 60], 'Ukraine': [31, 49], 'Ukrainian': [31, 49],
      'France': [2, 46], 'French': [2, 46], 'Paris': [2, 48],
      'Germany': [10, 51], 'German': [10, 51], 'Berlin': [13, 52],
      'UK': [-2, 54], 'Britain': [-2, 54], 'British': [-2, 54], 'London': [-0.1, 51.5],
      'Japan': [138, 36], 'Japanese': [138, 36], 'Tokyo': [139.7, 35.7],
      'India': [78, 22], 'Indian': [78, 22],
      'Brazil': [-51, -10], 'Brazilian': [-51, -10],
      'Israel': [35, 31], 'Israeli': [35, 31], 'Gaza': [34.4, 31.5], 'Palestine': [35, 32],
      'Iran': [53, 32], 'Iranian': [53, 32], 'Tehran': [51, 35.7],
      'Saudi': [45, 24], 'Arabia': [45, 24], 'Riyadh': [46.7, 24.7],
      'Taiwan': [121, 24], 'Taiwanese': [121, 24],
      'Europe': [10, 50], 'European': [10, 50], 'EU': [10, 50],
      'Middle East': [45, 29], 'Asia': [100, 35], 'Africa': [20, 0],
      'Mexico': [-102, 23], 'Canada': [-106, 56],
      'Australia': [134, -25], 'Australian': [134, -25],
      'Korea': [127, 36], 'Korean': [127, 36], 'Seoul': [127, 37.5],
      'Italy': [12, 42], 'Italian': [12, 42], 'Rome': [12.5, 41.9],
      'Spain': [-3, 40], 'Spanish': [-3, 40], 'Madrid': [-3.7, 40.4],
      'Turkey': [35, 39], 'Turkish': [35, 39], 'Ankara': [32.9, 39.9],
      'Egypt': [30, 27], 'Egyptian': [30, 27], 'Cairo': [31.2, 30],
      'Syria': [38, 35], 'Syrian': [38, 35], 'Damascus': [36.3, 33.5],
      'Yemen': [48, 15], 'Yemeni': [48, 15],
      'Lebanon': [35.8, 33.9], 'Beirut': [35.5, 33.9],
      'Iraq': [44, 33], 'Iraqi': [44, 33], 'Baghdad': [44.4, 33.3],
      'Afghanistan': [67, 33], 'Afghan': [67, 33], 'Kabul': [69.2, 34.5],
      'Pakistan': [69, 30], 'Pakistani': [69, 30],
      'Switzerland': [8, 47], 'Swiss': [8, 47], 'Zurich': [8.5, 47.4],
      'Netherlands': [5, 52], 'Dutch': [5, 52], 'Amsterdam': [4.9, 52.4],
      'Belgium': [4, 50.8], 'Brussels': [4.4, 50.8],
      'Poland': [19, 52], 'Polish': [19, 52], 'Warsaw': [21, 52.2],
      'Sweden': [15, 62], 'Swedish': [15, 62], 'Stockholm': [18, 59.3],
      'Norway': [9, 62], 'Norwegian': [9, 62], 'Oslo': [10.7, 59.9],
      'Finland': [26, 64], 'Finnish': [26, 64], 'Helsinki': [25, 60.2],
      'Denmark': [10, 56], 'Danish': [10, 56], 'Copenhagen': [12.6, 55.7],
      'Greece': [22, 39], 'Greek': [22, 39], 'Athens': [23.7, 38],
      'Portugal': [-8, 39.5], 'Portuguese': [-8, 39.5], 'Lisbon': [-9.1, 38.7],
      'Austria': [14, 47.5], 'Austrian': [14, 47.5], 'Vienna': [16.4, 48.2],
      'Singapore': [104, 1.3], 'Hong Kong': [114, 22.3],
      'Indonesia': [118, -2], 'Jakarta': [106.8, -6.2],
      'Malaysia': [102, 4], 'Kuala Lumpur': [101.7, 3.1],
      'Thailand': [101, 15], 'Bangkok': [100.5, 13.8],
      'Vietnam': [106, 16], 'Hanoi': [105.8, 21],
      'Philippines': [122, 12], 'Manila': [121, 14.6],
      'South Africa': [25, -29], 'Johannesburg': [28, -26.2],
      'Nigeria': [8, 10], 'Lagos': [3.4, 6.5],
      'Argentina': [-64, -34], 'Buenos Aires': [-58.4, -34.6],
      'Chile': [-71, -33], 'Santiago': [-70.7, -33.4],
      'Colombia': [-74, 4], 'Bogota': [-74.1, 4.6],
      'Venezuela': [-66, 8], 'Caracas': [-66.9, 10.5],
      'Peru': [-76, -10], 'Lima': [-77, -12],
    };
    
    // Analyze news titles and descriptions
    news.forEach(article => {
      const text = `${article.title || ''} ${article.description || ''}`.toLowerCase();
      
      Object.entries(countryToCoords).forEach(([keyword, coords]) => {
        const keywordLower = keyword.toLowerCase();
        // Count occurrences
        const regex = new RegExp(`\\b${keywordLower}\\b`, 'gi');
        const matches = text.match(regex);
        if (matches) {
          const key = `${coords[0]},${coords[1]}`;
          if (!countryMentions[key]) {
            countryMentions[key] = { coords, count: 0, keywords: new Set() };
          }
          countryMentions[key].count += matches.length;
          countryMentions[key].keywords.add(keyword);
        }
      });
    });
    
    // Convert to array and sort by count
    return Object.values(countryMentions)
      .sort((a, b) => b.count - a.count)
      .slice(0, 15)
      .map(item => ({
        ...item,
        keywords: Array.from(item.keywords),
        intensity: Math.min(item.count / 5, 1) // Normalize intensity (0-1)
      }));
  }, [news]);

  // Load shipping data
  useEffect(() => {
    const loadShippingData = async () => {
      const [routesData, portsData, statsData] = await Promise.all([
        getShippingRoutes('all'),
        getShippingPorts(),
        getShippingStats()
      ]);
      setShippingRoutes(routesData.routes || []);
      setShippingPorts(portsData);
      setShippingStats(statsData);
    };
    loadShippingData();
  }, [getShippingRoutes, getShippingPorts, getShippingStats]);

  // Load country data when selected
  useEffect(() => {
    const loadCountryData = async () => {
      if (!selectedCountry) {
        setCountryData(null);
        return;
      }
      
      setLoadingCountry(true);
      const data = await getCountryData(selectedCountry.iso);
      setCountryData(data);
      setLoadingCountry(false);
    };
    loadCountryData();
  }, [selectedCountry, getCountryData]);

  // Handle country click
  const handleCountryClick = (geo) => {
    const countryName = geo.properties.name;
    const iso = GEO_NAME_TO_ISO[countryName] || countryName.substring(0, 2).toUpperCase();
    
    // Clear other selections
    setSelectedConflict(null);
    setSelectedRoute(null);
    
    setSelectedCountry({ name: countryName, iso });
  };

  // Get marker icon based on event type
  const getEventIcon = (eventType) => {
    switch (eventType) {
      case 'armed_conflict': return Flame;
      case 'shipping_chokepoint': return Ship;
      case 'sanctions': return Shield;
      case 'geopolitical_tension': return AlertTriangle;
      default: return AlertTriangle;
    }
  };

  // Get severity color
  const getSeverityColor = (severity) => {
    if (severity >= 8) return '#ef4444';
    if (severity >= 6) return '#f97316';
    if (severity >= 4) return '#eab308';
    return '#22c55e';
  };

  // Get disruption color for routes
  const getDisruptionColor = (level, routeType) => {
    if (level > 0.5) return '#ef4444';
    if (level > 0.2) return '#f97316';
    if (level > 0) return '#eab308';
    return routeType === 'maritime' ? '#3b82f6' : '#8b5cf6';
  };

  // Get severity badge class
  const getSeverityBadgeClass = (severity) => {
    if (severity >= 8) return 'badge-critical';
    if (severity >= 6) return 'badge-high';
    if (severity >= 4) return 'badge-medium';
    return 'badge-low';
  };

  // Process conflicts for markers
  const markers = useMemo(() => {
    return conflicts.map((conflict) => {
      const coords = conflict.location?.lng && conflict.location?.lat 
        ? [conflict.location.lng, conflict.location.lat]
        : countryCoordinates[conflict.country] || [0, 0];
      
      return {
        ...conflict,
        coordinates: coords
      };
    });
  }, [conflicts]);

  // Filter routes based on active layer
  const filteredRoutes = useMemo(() => {
    if (activeLayer === 'conflicts') return [];
    if (activeLayer === 'maritime') return shippingRoutes.filter(r => r.route_type === 'maritime');
    if (activeLayer === 'air') return shippingRoutes.filter(r => r.route_type === 'air_cargo');
    return shippingRoutes;
  }, [shippingRoutes, activeLayer]);

  // Filter ports based on active layer
  const filteredPorts = useMemo(() => {
    if (!showPorts || activeLayer === 'conflicts') return { seaports: [], airports: [] };
    if (activeLayer === 'maritime') return { seaports: shippingPorts.seaports, airports: [] };
    if (activeLayer === 'air') return { seaports: [], airports: shippingPorts.airports };
    return shippingPorts;
  }, [shippingPorts, activeLayer, showPorts]);

  // Format volume
  const formatVolume = (volume, unit) => {
    if (volume >= 1000000) return `${(volume / 1000000).toFixed(1)}M ${unit}`;
    if (volume >= 1000) return `${(volume / 1000).toFixed(0)}K ${unit}`;
    return `${volume} ${unit}`;
  };

  // Format large numbers
  const formatNumber = (num, decimals = 0) => {
    if (num === null || num === undefined) return '—';
    if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
    if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
    if (num >= 1e3) return `${(num / 1e3).toFixed(decimals)}K`;
    return num.toLocaleString(undefined, { maximumFractionDigits: decimals });
  };

  // Format percentage
  const formatPercent = (num) => {
    if (num === null || num === undefined) return '—';
    return `${num.toFixed(1)}%`;
  };

  // Format population
  const formatPopulation = (num) => {
    if (num === null || num === undefined) return '—';
    if (num >= 1e9) return `${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `${(num / 1e6).toFixed(1)}M`;
    if (num >= 1e3) return `${(num / 1e3).toFixed(0)}K`;
    return num.toLocaleString();
  };

  // Clear all selections
  const clearSelection = () => {
    setSelectedCountry(null);
    setCountryData(null);
    setSelectedConflict(null);
    setSelectedRoute(null);
  };

  // Zoom controls
  const handleZoomIn = useCallback(() => {
    setZoom(z => Math.min(z * 1.5, 8));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoom(z => Math.max(z / 1.5, 1));
  }, []);

  const handleReset = useCallback(() => {
    setZoom(1);
    setCenter([20, 20]);
  }, []);

  const handleMoveEnd = useCallback(({ coordinates, zoom: newZoom }) => {
    setCenter(coordinates);
    setZoom(newZoom);
  }, []);

  // Zoom to a specific location
  const zoomToLocation = useCallback((coords, zoomLevel = 4) => {
    setCenter(coords);
    setZoom(zoomLevel);
  }, []);

  return (
    <div className="space-y-4" data-testid="worldmap-page">
      {/* Header */}
      <Card className="nexus-card">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-orange-500/20 rounded-sm flex items-center justify-center">
                <Globe className="w-5 h-5 text-orange-500" />
              </div>
              <div>
                <h1 className="text-xl font-semibold text-white">Global Trade & Risk Map</h1>
                <p className="text-sm text-zinc-500">Click on any country to view economic & demographic data</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              {/* Layer Tabs */}
              <Tabs value={activeLayer} onValueChange={setActiveLayer}>
                <TabsList className="bg-zinc-900 h-8">
                  <TabsTrigger value="all" className="text-xs h-6 px-3" data-testid="layer-all">All</TabsTrigger>
                  <TabsTrigger value="news" className="text-xs h-6 px-3" data-testid="layer-news">
                    <Newspaper className="w-3 h-3 mr-1" />News
                  </TabsTrigger>
                  <TabsTrigger value="maritime" className="text-xs h-6 px-3" data-testid="layer-maritime">
                    <Ship className="w-3 h-3 mr-1" />Maritime
                  </TabsTrigger>
                  <TabsTrigger value="air" className="text-xs h-6 px-3" data-testid="layer-air">
                    <Plane className="w-3 h-3 mr-1" />Air Cargo
                  </TabsTrigger>
                  <TabsTrigger value="countries" className="text-xs h-6 px-3" data-testid="layer-countries">
                    <Flag className="w-3 h-3 mr-1" />Countries
                  </TabsTrigger>
                  <TabsTrigger value="conflicts" className="text-xs h-6 px-3" data-testid="layer-conflicts">
                    <AlertTriangle className="w-3 h-3 mr-1" />Conflicts
                  </TabsTrigger>
                </TabsList>
              </Tabs>

              {/* Toggle Ports */}
              <Button 
                variant={showPorts ? "default" : "outline"} 
                size="sm" 
                className="h-8 text-xs"
                onClick={() => setShowPorts(!showPorts)}
              >
                <Anchor className="w-3 h-3 mr-1" />
                Ports
              </Button>

              {/* Active Events Count */}
              <div className="px-3 py-1.5 bg-red-500/10 border border-red-500/30 rounded-sm">
                <span className="text-red-500 font-mono text-sm">
                  {conflicts.filter(c => c.status === 'ongoing').length} EVENTS
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats Row */}
      {shippingStats && (
        <div className="grid grid-cols-6 gap-3">
          <Card className="nexus-card">
            <CardContent className="p-3">
              <div className="flex items-center gap-2">
                <Ship className="w-4 h-4 text-blue-500" />
                <div>
                  <p className="text-[10px] text-zinc-500">Maritime Routes</p>
                  <p className="font-mono text-lg text-white">{shippingStats.stats?.total_maritime_routes || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="nexus-card">
            <CardContent className="p-3">
              <div className="flex items-center gap-2">
                <Plane className="w-4 h-4 text-purple-500" />
                <div>
                  <p className="text-[10px] text-zinc-500">Air Routes</p>
                  <p className="font-mono text-lg text-white">{shippingStats.stats?.total_air_routes || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="nexus-card">
            <CardContent className="p-3">
              <div className="flex items-center gap-2">
                <Anchor className="w-4 h-4 text-cyan-500" />
                <div>
                  <p className="text-[10px] text-zinc-500">Major Ports</p>
                  <p className="font-mono text-lg text-white">{shippingStats.stats?.total_ports || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="nexus-card">
            <CardContent className="p-3">
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-violet-500" />
                <div>
                  <p className="text-[10px] text-zinc-500">Cargo Airports</p>
                  <p className="font-mono text-lg text-white">{shippingStats.stats?.total_airports || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="nexus-card">
            <CardContent className="p-3">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-orange-500" />
                <div>
                  <p className="text-[10px] text-zinc-500">Routes at Risk</p>
                  <p className="font-mono text-lg text-orange-500">{shippingStats.stats?.routes_affected_by_conflicts || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="nexus-card">
            <CardContent className="p-3">
              <div className="flex items-center gap-2">
                <TrendingDown className="w-4 h-4 text-red-500" />
                <div>
                  <p className="text-[10px] text-zinc-500">Volume at Risk</p>
                  <p className="font-mono text-lg text-red-500">{(shippingStats.stats?.volume_at_risk_percent || 0).toFixed(1)}%</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-12 gap-4">
        {/* Map */}
        <div className="col-span-8">
          <Card className="nexus-card overflow-hidden">
            <CardContent className="p-0">
              <div className="bg-zinc-950 relative" style={{ height: '600px' }}>
                <ComposableMap
                  projection="geoMercator"
                  projectionConfig={{
                    scale: 150,
                    center: [0, 20]
                  }}
                  style={{ width: '100%', height: '100%' }}
                >
                  <ZoomableGroup 
                    zoom={zoom} 
                    center={center}
                    onMoveEnd={handleMoveEnd}
                    minZoom={1}
                    maxZoom={8}
                  >
                    <Geographies geography={geoUrl}>
                      {({ geographies }) =>
                        geographies.map((geo) => {
                          const countryName = geo.properties.name;
                          const isSelected = selectedCountry?.name === countryName;
                          const isHovered = hoveredCountry === countryName;
                          
                          return (
                            <Geography
                              key={geo.rsmKey}
                              geography={geo}
                              fill={isSelected ? "#f97316" : isHovered ? "#3f3f46" : "#27272a"}
                              stroke={isSelected ? "#fb923c" : "#3f3f46"}
                              strokeWidth={isSelected ? 1.5 : 0.5}
                              style={{
                                default: { outline: 'none', cursor: 'pointer' },
                                hover: { fill: '#3f3f46', outline: 'none', cursor: 'pointer' },
                                pressed: { outline: 'none' }
                              }}
                              onClick={() => handleCountryClick(geo)}
                              onMouseEnter={() => setHoveredCountry(countryName)}
                              onMouseLeave={() => setHoveredCountry(null)}
                              data-testid={`country-${countryName?.replace(/\s+/g, '-')}`}
                            />
                          );
                        })
                      }
                    </Geographies>

                    {/* Shipping Routes */}
                    {filteredRoutes.map((route, i) => {
                      const isHovered = hoveredRoute?.id === route.id;
                      const isSelected = selectedRoute?.id === route.id;
                      const color = getDisruptionColor(route.disruption_level, route.route_type);
                      const strokeWidth = isHovered || isSelected ? 3 : route.is_strategic ? 2 : 1;
                      const opacity = isHovered || isSelected ? 1 : 0.6;
                      
                      return (
                        <Line
                          key={route.id}
                          from={route.origin.coordinates}
                          to={route.destination.coordinates}
                          stroke={color}
                          strokeWidth={strokeWidth}
                          strokeLinecap="round"
                          strokeDasharray={route.route_type === 'air_cargo' ? "4,4" : "0"}
                          style={{
                            cursor: 'pointer',
                            opacity: opacity
                          }}
                          onMouseEnter={() => setHoveredRoute(route)}
                          onMouseLeave={() => setHoveredRoute(null)}
                          onClick={() => {
                            clearSelection();
                            setSelectedRoute(route);
                          }}
                        />
                      );
                    })}

                    {/* Seaport Markers */}
                    {filteredPorts.seaports?.map((port, i) => (
                      <Marker key={`port-${port.id}`} coordinates={port.coordinates}>
                        <g transform="translate(-6, -6)">
                          <circle
                            cx="6"
                            cy="6"
                            r={port.is_major_hub ? 5 : 3}
                            fill="#3b82f6"
                            stroke="#09090b"
                            strokeWidth={1}
                            opacity={0.8}
                          />
                        </g>
                      </Marker>
                    ))}

                    {/* Airport Markers */}
                    {filteredPorts.airports?.map((airport, i) => (
                      <Marker key={`airport-${airport.id}`} coordinates={airport.coordinates}>
                        <g transform="translate(-6, -6)">
                          <rect
                            x="2"
                            y="2"
                            width={airport.is_major_hub ? 8 : 5}
                            height={airport.is_major_hub ? 8 : 5}
                            fill="#8b5cf6"
                            stroke="#09090b"
                            strokeWidth={1}
                            opacity={0.8}
                            transform={`rotate(45, 6, 6)`}
                          />
                        </g>
                      </Marker>
                    ))}

                    {/* Conflict Markers */}
                    {(activeLayer === 'all' || activeLayer === 'conflicts') && markers.map((conflict, i) => {
                      const Icon = getEventIcon(conflict.event_type);
                      const color = getSeverityColor(conflict.severity);
                      const isSelected = selectedConflict?.id === conflict.id;
                      const isHovered = hoveredConflict?.id === conflict.id;
                      
                      return (
                        <Marker
                          key={conflict.id || i}
                          coordinates={conflict.coordinates}
                          onClick={() => {
                            clearSelection();
                            setSelectedConflict(conflict);
                          }}
                          onMouseEnter={() => setHoveredConflict(conflict)}
                          onMouseLeave={() => setHoveredConflict(null)}
                        >
                          <g 
                            transform="translate(-12, -12)"
                            style={{ cursor: 'pointer' }}
                          >
                            {conflict.severity >= 7 && (
                              <circle
                                cx="12"
                                cy="12"
                                r={isSelected || isHovered ? 20 : 16}
                                fill={color}
                                opacity={0.3}
                                className="animate-pulse"
                              />
                            )}
                            <circle
                              cx="12"
                              cy="12"
                              r={isSelected || isHovered ? 14 : 10}
                              fill={color}
                              stroke="#09090b"
                              strokeWidth={2}
                            />
                            <text
                              x="12"
                              y="16"
                              textAnchor="middle"
                              fill="#fff"
                              fontSize="10"
                              fontWeight="bold"
                            >
                              !
                            </text>
                          </g>
                        </Marker>
                      );
                    })}

                    {/* News Hotspots - Heatmap circles showing most mentioned regions */}
                    {(activeLayer === 'all' || activeLayer === 'news') && newsHotspots.map((hotspot, i) => (
                      <Marker key={`hotspot-${i}`} coordinates={hotspot.coords}>
                        <g 
                          transform="translate(-20, -20)"
                          style={{ cursor: 'pointer' }}
                          onClick={() => zoomToLocation(hotspot.coords, 3)}
                        >
                          {/* Outer glow */}
                          <circle
                            cx="20"
                            cy="20"
                            r={15 + hotspot.intensity * 20}
                            fill="#f59e0b"
                            opacity={0.1 + hotspot.intensity * 0.15}
                          />
                          {/* Inner circle */}
                          <circle
                            cx="20"
                            cy="20"
                            r={8 + hotspot.intensity * 10}
                            fill="#f59e0b"
                            opacity={0.3 + hotspot.intensity * 0.3}
                            stroke="#fbbf24"
                            strokeWidth={1}
                          />
                          {/* Count badge */}
                          <circle
                            cx="20"
                            cy="20"
                            r={8}
                            fill="#18181b"
                            stroke="#f59e0b"
                            strokeWidth={2}
                          />
                          <text
                            x="20"
                            y="24"
                            textAnchor="middle"
                            fill="#f59e0b"
                            fontSize="10"
                            fontWeight="bold"
                          >
                            {hotspot.count}
                          </text>
                        </g>
                      </Marker>
                    ))}
                  </ZoomableGroup>
                </ComposableMap>

                {/* Country Hover Tooltip */}
                {hoveredCountry && !selectedCountry && !hoveredRoute && !hoveredConflict && (
                  <div className="absolute top-4 left-4 bg-zinc-900/95 border border-zinc-700 rounded-sm p-3 z-10">
                    <p className="text-sm text-white font-medium">{hoveredCountry}</p>
                    <p className="text-[10px] text-zinc-400 mt-1">Click for details</p>
                  </div>
                )}

                {/* Route Hover Tooltip */}
                {hoveredRoute && !selectedRoute && (
                  <div className="absolute top-4 left-4 bg-zinc-900/95 border border-zinc-700 rounded-sm p-3 max-w-xs z-10">
                    <div className="flex items-center gap-2 mb-2">
                      {hoveredRoute.route_type === 'maritime' ? (
                        <Ship className="w-4 h-4 text-blue-500" />
                      ) : (
                        <Plane className="w-4 h-4 text-purple-500" />
                      )}
                      <h4 className="text-sm font-medium text-white">{hoveredRoute.name}</h4>
                    </div>
                    <p className="text-xs text-zinc-400">
                      {hoveredRoute.origin.name} → {hoveredRoute.destination.name}
                    </p>
                    <div className="flex items-center gap-3 mt-2 text-xs">
                      <span className="text-zinc-400">{hoveredRoute.distance_km.toLocaleString()} km</span>
                      <span className="text-zinc-400">{hoveredRoute.average_transit_days.toFixed(0)} days</span>
                      <span className="text-emerald-500">{formatVolume(hoveredRoute.annual_volume, hoveredRoute.volume_unit)}/yr</span>
                    </div>
                    {hoveredRoute.disruption_level > 0 && (
                      <Badge className="mt-2 bg-red-500/20 text-red-500 rounded-none text-[10px]">
                        {(hoveredRoute.disruption_level * 100).toFixed(0)}% Disruption Risk
                      </Badge>
                    )}
                  </div>
                )}

                {/* Conflict Hover Tooltip */}
                {hoveredConflict && !selectedConflict && !hoveredRoute && (
                  <div className="absolute top-4 left-4 bg-zinc-900 border border-zinc-700 rounded-sm p-3 max-w-xs z-10">
                    <h4 className="text-sm font-medium text-white">{hoveredConflict.title}</h4>
                    <p className="text-xs text-zinc-500 mt-1">{hoveredConflict.country}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge className={`${getSeverityBadgeClass(hoveredConflict.severity)} rounded-none text-[10px]`}>
                        Severity: {hoveredConflict.severity}/10
                      </Badge>
                    </div>
                  </div>
                )}

                {/* Legend */}
                <div className="absolute bottom-4 left-4 bg-zinc-900/90 border border-zinc-800 rounded-sm p-2 text-[10px]">
                  <p className="text-zinc-400 mb-2 font-medium">Legend</p>
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-0.5 bg-blue-500"></div>
                      <span className="text-zinc-400">Maritime Route</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-0.5 bg-purple-500 border-dashed" style={{borderTop: '2px dashed #8b5cf6'}}></div>
                      <span className="text-zinc-400">Air Cargo Route</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-0.5 bg-red-500"></div>
                      <span className="text-zinc-400">Disrupted Route</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span className="text-zinc-400">Seaport</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-purple-500 rotate-45"></div>
                      <span className="text-zinc-400">Airport</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                      <span className="text-zinc-400">Conflict Zone</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-amber-500/50 rounded-full border border-amber-500"></div>
                      <span className="text-zinc-400">News Hotspot</span>
                    </div>
                  </div>
                </div>

                {/* Zoom Controls */}
                <div className="absolute bottom-4 right-4 flex flex-col gap-1">
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 w-8 p-0 bg-zinc-900 hover:bg-zinc-800"
                    onClick={handleZoomIn}
                    title="Zoom in"
                  >
                    <ZoomIn className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 w-8 p-0 bg-zinc-900 hover:bg-zinc-800"
                    onClick={handleZoomOut}
                    title="Zoom out"
                  >
                    <ZoomOut className="w-4 h-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 w-8 p-0 bg-zinc-900 hover:bg-zinc-800"
                    onClick={handleReset}
                    title="Reset view"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </Button>
                </div>

                {/* Zoom Level Indicator */}
                <div className="absolute top-4 right-4 bg-zinc-900/90 border border-zinc-800 rounded-sm px-2 py-1">
                  <span className="text-[10px] text-zinc-400">Zoom: </span>
                  <span className="text-[10px] font-mono text-white">{zoom.toFixed(1)}x</span>
                </div>

                {/* Instructions */}
                <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-zinc-900/80 border border-zinc-800 rounded-sm px-3 py-1.5">
                  <p className="text-[10px] text-zinc-400">
                    🖱️ Scroll to zoom • Drag to pan • Click for details
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="col-span-4 space-y-4">
          {/* Country Data Panel */}
          {selectedCountry && (
            <Card className="nexus-card border-emerald-500/50" data-testid="country-data-panel">
              <CardHeader className="card-header-terminal">
                <CardTitle className="card-header-title flex items-center gap-2">
                  <Flag className="w-4 h-4 text-emerald-500" />
                  {selectedCountry.name}
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0"
                  onClick={clearSelection}
                >
                  <X className="w-4 h-4" />
                </Button>
              </CardHeader>
              <CardContent className="p-4">
                {loadingCountry ? (
                  <div className="flex items-center justify-center h-48">
                    <Loader2 className="w-6 h-6 animate-spin text-emerald-500" />
                  </div>
                ) : countryData ? (
                  <ScrollArea className="h-[500px] pr-2">
                    <div className="space-y-4">
                      {/* Basic Info */}
                      <div className="flex items-start gap-3">
                        {countryData.basic.flag_url && (
                          <img 
                            src={countryData.basic.flag_url} 
                            alt={`${countryData.basic.name} flag`}
                            className="w-16 h-10 object-cover border border-zinc-700"
                          />
                        )}
                        <div>
                          <h3 className="text-lg font-medium text-white">{countryData.basic.name}</h3>
                          <p className="text-xs text-zinc-400">{countryData.basic.official_name}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <Badge className="bg-zinc-700 text-zinc-300 rounded-none text-[10px]">
                              {countryData.basic.region}
                            </Badge>
                            {countryData.basic.subregion && (
                              <Badge className="bg-zinc-800 text-zinc-400 rounded-none text-[10px]">
                                {countryData.basic.subregion}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Quick Stats */}
                      <div className="grid grid-cols-2 gap-2">
                        <div className="p-2 bg-zinc-900 rounded-sm">
                          <p className="text-[10px] text-zinc-500">Capital</p>
                          <p className="text-sm text-white">{countryData.basic.capital || '—'}</p>
                        </div>
                        <div className="p-2 bg-zinc-900 rounded-sm">
                          <p className="text-[10px] text-zinc-500">Currency</p>
                          <p className="text-sm text-white">{countryData.economic.currency_code || '—'}</p>
                        </div>
                      </div>

                      {/* Economic Data */}
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <DollarSign className="w-4 h-4 text-emerald-500" />
                          <p className="text-xs text-zinc-500 uppercase font-medium">Economic Indicators</p>
                        </div>
                        <div className="space-y-2">
                          <div className="flex justify-between items-center py-1.5 border-b border-zinc-800/50">
                            <span className="text-sm text-zinc-400">GDP</span>
                            <span className="font-mono text-sm text-white">{formatNumber(countryData.economic.gdp)}</span>
                          </div>
                          <div className="flex justify-between items-center py-1.5 border-b border-zinc-800/50">
                            <span className="text-sm text-zinc-400">GDP per Capita</span>
                            <span className="font-mono text-sm text-white">{formatNumber(countryData.economic.gdp_per_capita)}</span>
                          </div>
                          <div className="flex justify-between items-center py-1.5 border-b border-zinc-800/50">
                            <span className="text-sm text-zinc-400">GDP Growth</span>
                            <span className={`font-mono text-sm ${countryData.economic.gdp_growth > 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                              {formatPercent(countryData.economic.gdp_growth)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center py-1.5 border-b border-zinc-800/50">
                            <span className="text-sm text-zinc-400">Inflation</span>
                            <span className={`font-mono text-sm ${countryData.economic.inflation > 5 ? 'text-red-500' : 'text-white'}`}>
                              {formatPercent(countryData.economic.inflation)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center py-1.5 border-b border-zinc-800/50">
                            <span className="text-sm text-zinc-400">Unemployment</span>
                            <span className={`font-mono text-sm ${countryData.economic.unemployment > 10 ? 'text-red-500' : 'text-white'}`}>
                              {formatPercent(countryData.economic.unemployment)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center py-1.5 border-b border-zinc-800/50">
                            <span className="text-sm text-zinc-400">Exports</span>
                            <span className="font-mono text-sm text-emerald-500">{formatNumber(countryData.economic.exports)}</span>
                          </div>
                          <div className="flex justify-between items-center py-1.5 border-b border-zinc-800/50">
                            <span className="text-sm text-zinc-400">Imports</span>
                            <span className="font-mono text-sm text-orange-500">{formatNumber(countryData.economic.imports)}</span>
                          </div>
                          {countryData.economic.trade_balance !== null && (
                            <div className="flex justify-between items-center py-1.5 border-b border-zinc-800/50">
                              <span className="text-sm text-zinc-400">Trade Balance</span>
                              <span className={`font-mono text-sm ${countryData.economic.trade_balance > 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                                {formatNumber(countryData.economic.trade_balance)}
                              </span>
                            </div>
                          )}
                          <div className="flex justify-between items-center py-1.5 border-b border-zinc-800/50">
                            <span className="text-sm text-zinc-400">FDI Inflow</span>
                            <span className="font-mono text-sm text-blue-400">{formatNumber(countryData.economic.fdi_inflow)}</span>
                          </div>
                        </div>
                      </div>

                      {/* Demographic Data */}
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <Users className="w-4 h-4 text-blue-500" />
                          <p className="text-xs text-zinc-500 uppercase font-medium">Demographics</p>
                        </div>
                        <div className="space-y-2">
                          <div className="flex justify-between items-center py-1.5 border-b border-zinc-800/50">
                            <span className="text-sm text-zinc-400">Population</span>
                            <span className="font-mono text-sm text-white">{formatPopulation(countryData.demographic.population)}</span>
                          </div>
                          <div className="flex justify-between items-center py-1.5 border-b border-zinc-800/50">
                            <span className="text-sm text-zinc-400">Pop. Growth</span>
                            <span className={`font-mono text-sm ${countryData.demographic.population_growth > 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                              {formatPercent(countryData.demographic.population_growth)}
                            </span>
                          </div>
                          <div className="flex justify-between items-center py-1.5 border-b border-zinc-800/50">
                            <span className="text-sm text-zinc-400">Density</span>
                            <span className="font-mono text-sm text-white">
                              {countryData.demographic.population_density ? `${countryData.demographic.population_density.toFixed(1)}/km²` : '—'}
                            </span>
                          </div>
                          <div className="flex justify-between items-center py-1.5 border-b border-zinc-800/50">
                            <span className="text-sm text-zinc-400">Life Expectancy</span>
                            <span className="font-mono text-sm text-white">
                              {countryData.demographic.life_expectancy ? `${countryData.demographic.life_expectancy.toFixed(1)} yrs` : '—'}
                            </span>
                          </div>
                          <div className="flex justify-between items-center py-1.5 border-b border-zinc-800/50">
                            <span className="text-sm text-zinc-400">Urban Population</span>
                            <span className="font-mono text-sm text-white">{formatPercent(countryData.demographic.urban_population_percent)}</span>
                          </div>
                          <div className="flex justify-between items-center py-1.5 border-b border-zinc-800/50">
                            <span className="text-sm text-zinc-400">Fertility Rate</span>
                            <span className="font-mono text-sm text-white">
                              {countryData.demographic.fertility_rate ? `${countryData.demographic.fertility_rate.toFixed(2)}` : '—'}
                            </span>
                          </div>
                          {countryData.demographic.hdi && (
                            <div className="flex justify-between items-center py-1.5 border-b border-zinc-800/50">
                              <span className="text-sm text-zinc-400">HDI</span>
                              <span className={`font-mono text-sm ${countryData.demographic.hdi > 0.8 ? 'text-emerald-500' : countryData.demographic.hdi > 0.6 ? 'text-yellow-500' : 'text-red-500'}`}>
                                {countryData.demographic.hdi.toFixed(3)}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Additional Info */}
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <Building2 className="w-4 h-4 text-violet-500" />
                          <p className="text-xs text-zinc-500 uppercase font-medium">Additional Info</p>
                        </div>
                        <div className="space-y-2">
                          <div className="py-1.5 border-b border-zinc-800/50">
                            <span className="text-sm text-zinc-400">Languages</span>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {countryData.basic.languages
                                ?.filter(lang => {
                                  const langLower = lang.toLowerCase();
                                  return langLower.includes('english') || 
                                         langLower.includes('french') || 
                                         langLower.includes('français') ||
                                         langLower === 'english' ||
                                         langLower === 'french';
                                })
                                .map((lang, i) => (
                                  <Badge key={i} variant="outline" className="text-[10px] rounded-none">
                                    {lang}
                                  </Badge>
                                ))}
                              {countryData.basic.languages?.filter(lang => {
                                const langLower = lang.toLowerCase();
                                return langLower.includes('english') || 
                                       langLower.includes('french') || 
                                       langLower.includes('français');
                              }).length === 0 && (
                                <span className="text-xs text-zinc-500">Other languages</span>
                              )}
                            </div>
                          </div>
                          <div className="py-1.5 border-b border-zinc-800/50">
                            <span className="text-sm text-zinc-400">Area</span>
                            <p className="font-mono text-sm text-white mt-1">
                              {countryData.basic.area ? `${countryData.basic.area.toLocaleString()} km²` : '—'}
                            </p>
                          </div>
                          {countryData.basic.borders?.length > 0 && (
                            <div className="py-1.5 border-b border-zinc-800/50">
                              <span className="text-sm text-zinc-400">Borders</span>
                              <div className="flex flex-wrap gap-1 mt-1">
                                {countryData.basic.borders.map((border, i) => (
                                  <Badge key={i} variant="outline" className="text-[10px] rounded-none text-zinc-400">
                                    {border}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Risk Factors */}
                      {countryData.risk_factors?.length > 0 && (
                        <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-sm">
                          <div className="flex items-center gap-2 mb-2">
                            <AlertTriangle className="w-4 h-4 text-red-500" />
                            <p className="text-xs text-red-400 uppercase font-medium">Risk Factors</p>
                          </div>
                          <div className="space-y-1">
                            {countryData.risk_factors.map((risk, i) => (
                              <p key={i} className="text-xs text-red-300">{risk}</p>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                ) : (
                  <div className="flex flex-col items-center justify-center h-48 text-zinc-500">
                    <Globe className="w-12 h-12 mb-4 opacity-50" />
                    <p>No data available</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Selected Route Detail */}
          {selectedRoute && !selectedCountry && (
            <Card className="nexus-card border-blue-500/50">
              <CardHeader className="card-header-terminal">
                <CardTitle className="card-header-title flex items-center gap-2">
                  {selectedRoute.route_type === 'maritime' ? (
                    <Ship className="w-4 h-4 text-blue-500" />
                  ) : (
                    <Plane className="w-4 h-4 text-purple-500" />
                  )}
                  Route Details
                </CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0"
                  onClick={clearSelection}
                >
                  <X className="w-4 h-4" />
                </Button>
              </CardHeader>
              <CardContent className="p-4">
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-medium text-white">{selectedRoute.name}</h3>
                    <Badge className={`mt-1 rounded-none ${selectedRoute.route_type === 'maritime' ? 'bg-blue-500/20 text-blue-500' : 'bg-purple-500/20 text-purple-500'}`}>
                      {selectedRoute.route_type === 'maritime' ? 'Maritime' : 'Air Cargo'}
                    </Badge>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-zinc-900 rounded-sm">
                      <p className="text-[10px] text-zinc-500 uppercase">Origin</p>
                      <p className="font-medium text-white text-sm">{selectedRoute.origin.name}</p>
                      <p className="text-xs text-zinc-400">{selectedRoute.origin.country}</p>
                    </div>
                    <div className="p-3 bg-zinc-900 rounded-sm">
                      <p className="text-[10px] text-zinc-500 uppercase">Destination</p>
                      <p className="font-medium text-white text-sm">{selectedRoute.destination.name}</p>
                      <p className="text-xs text-zinc-400">{selectedRoute.destination.country}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2">
                    <div className="p-2 bg-zinc-900 rounded-sm text-center">
                      <p className="text-[10px] text-zinc-500">Distance</p>
                      <p className="font-mono text-sm text-white">{(selectedRoute.distance_km / 1000).toFixed(1)}K km</p>
                    </div>
                    <div className="p-2 bg-zinc-900 rounded-sm text-center">
                      <p className="text-[10px] text-zinc-500">Transit</p>
                      <p className="font-mono text-sm text-white">{selectedRoute.average_transit_days.toFixed(0)} days</p>
                    </div>
                    <div className="p-2 bg-zinc-900 rounded-sm text-center">
                      <p className="text-[10px] text-zinc-500">Volume/Yr</p>
                      <p className="font-mono text-sm text-emerald-500">{formatVolume(selectedRoute.annual_volume, selectedRoute.volume_unit)}</p>
                    </div>
                  </div>

                  {selectedRoute.chokepoints?.length > 0 && (
                    <div>
                      <p className="text-xs text-zinc-500 uppercase mb-2">Strategic Chokepoints</p>
                      <div className="flex flex-wrap gap-1">
                        {selectedRoute.chokepoints.map((cp, i) => (
                          <Badge key={i} variant="outline" className="rounded-none text-xs text-cyan-400 border-cyan-500/30">
                            {cp}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {selectedRoute.disruption_level > 0 && (
                    <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-sm">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs text-red-400 uppercase font-medium">Disruption Risk</span>
                        <span className="font-mono text-lg text-red-500">{(selectedRoute.disruption_level * 100).toFixed(0)}%</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {selectedRoute.affected_by_conflicts?.map((conflict, i) => (
                          <Badge key={i} className="bg-red-500/20 text-red-400 rounded-none text-[10px]">
                            {conflict}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Selected Conflict Detail */}
          {selectedConflict && !selectedCountry && !selectedRoute && (
            <Card className="nexus-card border-orange-500/50">
              <CardHeader className="card-header-terminal">
                <CardTitle className="card-header-title">Event Details</CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0"
                  onClick={clearSelection}
                >
                  <X className="w-4 h-4" />
                </Button>
              </CardHeader>
              <CardContent className="p-4">
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-medium text-white">{selectedConflict.title}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge className={`${getSeverityBadgeClass(selectedConflict.severity)} rounded-none`}>
                        {selectedConflict.status}
                      </Badge>
                      <span className="text-sm text-zinc-500">{selectedConflict.country}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="flex-1 p-3 bg-zinc-900 rounded-sm">
                      <p className="text-[10px] text-zinc-500 uppercase">Severity</p>
                      <p className="font-mono text-2xl text-white">{selectedConflict.severity}<span className="text-sm text-zinc-500">/10</span></p>
                    </div>
                    <div className="flex-1 p-3 bg-zinc-900 rounded-sm">
                      <p className="text-[10px] text-zinc-500 uppercase">Impact Score</p>
                      <p className="font-mono text-2xl text-orange-500">{selectedConflict.impact_score?.toFixed(0)}</p>
                    </div>
                  </div>

                  <div>
                    <p className="text-xs text-zinc-500 uppercase mb-2">Description</p>
                    <p className="text-sm text-zinc-300">{selectedConflict.description}</p>
                  </div>

                  <div>
                    <p className="text-xs text-zinc-500 uppercase mb-2">Affected Assets</p>
                    <div className="flex flex-wrap gap-1">
                      {selectedConflict.affected_assets?.map((asset, i) => (
                        <Badge 
                          key={i} 
                          variant="outline" 
                          className="rounded-none text-xs text-orange-500 border-orange-500/30 cursor-pointer hover:bg-orange-500/10"
                          onClick={() => navigate(`/quote?symbol=${asset}`)}
                        >
                          {asset}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Default: Routes List or Risk Summary */}
          {!selectedCountry && !selectedRoute && !selectedConflict && (
            <>
              {/* News Hotspots Panel - shown when News layer is active */}
              {activeLayer === 'news' && newsHotspots.length > 0 && (
                <Card className="nexus-card border-amber-500/30">
                  <CardHeader className="card-header-terminal">
                    <CardTitle className="card-header-title flex items-center gap-2">
                      <Newspaper className="w-4 h-4 text-amber-500" />
                      News Hotspots
                    </CardTitle>
                    <Badge className="bg-amber-500/20 text-amber-400 rounded-none text-[10px]">
                      {newsHotspots.length} regions
                    </Badge>
                  </CardHeader>
                  <CardContent className="p-0">
                    <ScrollArea className="h-[320px]">
                      {newsHotspots.map((hotspot, i) => (
                        <div
                          key={i}
                          className="p-3 border-b border-zinc-800/50 hover:bg-zinc-800/30 cursor-pointer"
                          onClick={() => zoomToLocation(hotspot.coords, 3)}
                        >
                          <div className="flex items-start gap-3">
                            <div className="w-10 h-10 rounded-sm flex items-center justify-center flex-shrink-0 bg-amber-500/20 border border-amber-500/30">
                              <span className="font-mono text-lg text-amber-400">{hotspot.count}</span>
                            </div>
                            <div className="flex-1 min-w-0">
                              <h4 className="text-sm text-white font-medium">
                                {hotspot.keywords.slice(0, 2).join(', ')}
                              </h4>
                              <p className="text-[10px] text-zinc-500 mt-0.5">
                                {hotspot.keywords.length > 2 && `+${hotspot.keywords.length - 2} more terms`}
                              </p>
                              <div className="mt-1.5">
                                <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                                  <div 
                                    className="h-full bg-gradient-to-r from-amber-500 to-orange-500 rounded-full"
                                    style={{ width: `${hotspot.intensity * 100}%` }}
                                  />
                                </div>
                              </div>
                            </div>
                            <ChevronRight className="w-4 h-4 text-zinc-600 flex-shrink-0" />
                          </div>
                        </div>
                      ))}
                    </ScrollArea>
                  </CardContent>
                </Card>
              )}

              {/* Routes/Conflicts List - shown for other layers */}
              {activeLayer !== 'news' && (
              <Card className="nexus-card">
                <CardHeader className="card-header-terminal">
                  <CardTitle className="card-header-title flex items-center gap-2">
                    <Route className="w-4 h-4 text-blue-500" />
                    {activeLayer === 'conflicts' ? 'Active Events' : 'Shipping Routes'}
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <ScrollArea className="h-[320px]">
                    {activeLayer === 'conflicts' ? (
                      conflicts.map((conflict, i) => {
                        const Icon = getEventIcon(conflict.event_type);
                        return (
                          <div
                            key={conflict.id || i}
                            className="p-3 border-b border-zinc-800/50 hover:bg-zinc-800/30 cursor-pointer"
                            onClick={() => setSelectedConflict(conflict)}
                          >
                            <div className="flex items-start gap-3">
                              <div 
                                className="w-8 h-8 rounded-sm flex items-center justify-center flex-shrink-0"
                                style={{ backgroundColor: `${getSeverityColor(conflict.severity)}20` }}
                              >
                                <Icon className="w-4 h-4" style={{ color: getSeverityColor(conflict.severity) }} />
                              </div>
                              <div className="flex-1 min-w-0">
                                <h4 className="text-sm text-white">{conflict.title}</h4>
                                <div className="flex items-center gap-2 mt-1">
                                  <span className="text-[10px] text-zinc-500">{conflict.country}</span>
                                  <Badge className={`${getSeverityBadgeClass(conflict.severity)} rounded-none text-[9px]`}>
                                    {conflict.severity}/10
                                  </Badge>
                                </div>
                              </div>
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      filteredRoutes.slice(0, 8).map((route, i) => (
                        <div
                          key={route.id}
                          className="p-3 border-b border-zinc-800/50 hover:bg-zinc-800/30 cursor-pointer"
                          onClick={() => setSelectedRoute(route)}
                          data-testid={`route-item-${route.id}`}
                        >
                          <div className="flex items-start gap-3">
                            <div className={`w-8 h-8 rounded-sm flex items-center justify-center flex-shrink-0 ${route.route_type === 'maritime' ? 'bg-blue-500/20' : 'bg-purple-500/20'}`}>
                              {route.route_type === 'maritime' ? (
                                <Ship className="w-4 h-4 text-blue-500" />
                              ) : (
                                <Plane className="w-4 h-4 text-purple-500" />
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              <h4 className="text-sm text-white">{route.name}</h4>
                              <p className="text-[10px] text-zinc-500">{route.origin.name} → {route.destination.name}</p>
                              <div className="flex items-center gap-2 mt-1">
                                <span className="text-[10px] text-zinc-400">{formatVolume(route.annual_volume, route.volume_unit)}/yr</span>
                                {route.disruption_level > 0 && (
                                  <Badge className="bg-red-500/20 text-red-400 rounded-none text-[9px]">
                                    {(route.disruption_level * 100).toFixed(0)}% Risk
                                  </Badge>
                                )}
                              </div>
                            </div>
                            <ChevronRight className="w-4 h-4 text-zinc-600 flex-shrink-0" />
                          </div>
                        </div>
                      ))
                    )}
                  </ScrollArea>
                </CardContent>
              </Card>
              )}

              {/* Risk Summary */}
              {shippingStats?.risk_summary && (
                <Card className="nexus-card">
                  <CardHeader className="card-header-terminal">
                    <CardTitle className="card-header-title flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-orange-500" />
                      Risk Summary
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-3">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between py-1.5">
                        <span className="text-sm text-zinc-400">High Risk Routes</span>
                        <Badge className="bg-red-500/20 text-red-500 rounded-none">
                          {shippingStats.risk_summary.high_risk_routes}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between py-1.5">
                        <span className="text-sm text-zinc-400">Medium Risk Routes</span>
                        <Badge className="bg-orange-500/20 text-orange-500 rounded-none">
                          {shippingStats.risk_summary.medium_risk_routes}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between py-1.5">
                        <span className="text-sm text-zinc-400">Low Risk Routes</span>
                        <Badge className="bg-yellow-500/20 text-yellow-500 rounded-none">
                          {shippingStats.risk_summary.low_risk_routes}
                        </Badge>
                      </div>
                      {shippingStats.risk_summary.critical_chokepoints?.length > 0 && (
                        <div className="pt-2 border-t border-zinc-800">
                          <p className="text-xs text-zinc-500 uppercase mb-2">Critical Chokepoints</p>
                          <div className="flex flex-wrap gap-1">
                            {shippingStats.risk_summary.critical_chokepoints.map((cp, i) => (
                              <Badge key={i} className="bg-red-500/20 text-red-400 rounded-none text-[10px]">
                                {cp}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default WorldMapPage;
