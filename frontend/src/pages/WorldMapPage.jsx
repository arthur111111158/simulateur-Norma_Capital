import React, { useState, useMemo } from 'react';
import { useApp } from '../context/AppContext';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { ScrollArea } from '../components/ui/scroll-area';
import { 
  ComposableMap, 
  Geographies, 
  Geography, 
  Marker,
  ZoomableGroup 
} from 'react-simple-maps';
import { 
  Globe, 
  AlertTriangle, 
  TrendingDown,
  Flame,
  Shield,
  Ship,
  Zap,
  X,
  ChevronRight
} from 'lucide-react';

const geoUrl = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

// Country coordinates for markers
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
  const { conflicts } = useApp();
  const navigate = useNavigate();
  const [selectedConflict, setSelectedConflict] = useState(null);
  const [hoveredConflict, setHoveredConflict] = useState(null);
  const [zoom, setZoom] = useState(1);

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
    if (severity >= 8) return '#ef4444'; // red
    if (severity >= 6) return '#f97316'; // orange
    if (severity >= 4) return '#eab308'; // yellow
    return '#22c55e'; // green
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
                <h1 className="text-xl font-semibold text-white">Geopolitical Risk Map</h1>
                <p className="text-sm text-zinc-500">Global conflicts, sanctions & supply chain disruptions</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              {/* Legend */}
              <div className="flex items-center gap-3 text-xs">
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-full bg-red-500"></div>
                  <span className="text-zinc-500">Critical</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                  <span className="text-zinc-500">High</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                  <span className="text-zinc-500">Medium</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
                  <span className="text-zinc-500">Low</span>
                </div>
              </div>
              {/* Active Events Count */}
              <div className="px-3 py-1.5 bg-red-500/10 border border-red-500/30 rounded-sm">
                <span className="text-red-500 font-mono text-sm">
                  {conflicts.filter(c => c.status === 'ongoing').length} ACTIVE EVENTS
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

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
                    center: [20, 20]
                  }}
                  style={{ width: '100%', height: '100%' }}
                >
                  <ZoomableGroup zoom={zoom} onMoveEnd={({ zoom: z }) => setZoom(z)}>
                    <Geographies geography={geoUrl}>
                      {({ geographies }) =>
                        geographies.map((geo) => (
                          <Geography
                            key={geo.rsmKey}
                            geography={geo}
                            fill="#27272a"
                            stroke="#3f3f46"
                            strokeWidth={0.5}
                            style={{
                              default: { outline: 'none' },
                              hover: { fill: '#3f3f46', outline: 'none' },
                              pressed: { outline: 'none' }
                            }}
                          />
                        ))
                      }
                    </Geographies>

                    {/* Conflict Markers */}
                    {markers.map((conflict, i) => {
                      const Icon = getEventIcon(conflict.event_type);
                      const color = getSeverityColor(conflict.severity);
                      const isSelected = selectedConflict?.id === conflict.id;
                      const isHovered = hoveredConflict?.id === conflict.id;
                      
                      return (
                        <Marker
                          key={conflict.id || i}
                          coordinates={conflict.coordinates}
                          onClick={() => setSelectedConflict(conflict)}
                          onMouseEnter={() => setHoveredConflict(conflict)}
                          onMouseLeave={() => setHoveredConflict(null)}
                        >
                          <g 
                            transform="translate(-12, -12)"
                            style={{ cursor: 'pointer' }}
                          >
                            {/* Pulse animation for high severity */}
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
                            {/* Main circle */}
                            <circle
                              cx="12"
                              cy="12"
                              r={isSelected || isHovered ? 14 : 10}
                              fill={color}
                              stroke="#09090b"
                              strokeWidth={2}
                            />
                            {/* Icon placeholder (simple representation) */}
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
                  </ZoomableGroup>
                </ComposableMap>

                {/* Hover Tooltip */}
                {hoveredConflict && !selectedConflict && (
                  <div className="absolute top-4 left-4 bg-zinc-900 border border-zinc-700 rounded-sm p-3 max-w-xs z-10">
                    <h4 className="text-sm font-medium text-white">{hoveredConflict.title}</h4>
                    <p className="text-xs text-zinc-500 mt-1">{hoveredConflict.country}</p>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge className={`${getSeverityBadgeClass(hoveredConflict.severity)} rounded-none text-[10px]`}>
                        Severity: {hoveredConflict.severity}/10
                      </Badge>
                      <span className="text-xs text-zinc-400">
                        Impact: {hoveredConflict.impact_score?.toFixed(0)}
                      </span>
                    </div>
                  </div>
                )}

                {/* Zoom Controls */}
                <div className="absolute bottom-4 right-4 flex flex-col gap-1">
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 w-8 p-0 bg-zinc-900"
                    onClick={() => setZoom(z => Math.min(z * 1.5, 8))}
                  >
                    +
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-8 w-8 p-0 bg-zinc-900"
                    onClick={() => setZoom(z => Math.max(z / 1.5, 1))}
                  >
                    -
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="col-span-4 space-y-4">
          {/* Selected Conflict Detail */}
          {selectedConflict ? (
            <Card className="nexus-card border-orange-500/50">
              <CardHeader className="card-header-terminal">
                <CardTitle className="card-header-title">Event Details</CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0"
                  onClick={() => setSelectedConflict(null)}
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
                    <p className="text-xs text-zinc-500 uppercase mb-2">Transmission Channels</p>
                    <div className="flex flex-wrap gap-1">
                      {selectedConflict.transmission_channels?.map((channel, i) => (
                        <Badge key={i} variant="outline" className="rounded-none text-xs text-blue-400 border-blue-500/30">
                          {channel}
                        </Badge>
                      ))}
                    </div>
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

                  <div>
                    <p className="text-xs text-zinc-500 uppercase mb-2">Sources</p>
                    <div className="flex flex-wrap gap-1">
                      {selectedConflict.sources?.map((source, i) => (
                        <span key={i} className="text-xs text-zinc-400">{source}{i < selectedConflict.sources.length - 1 && ', '}</span>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="nexus-card">
              <CardHeader className="card-header-terminal">
                <CardTitle className="card-header-title flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-orange-500" />
                  Active Events
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <ScrollArea className="h-[400px]">
                  {conflicts.map((conflict, i) => {
                    const Icon = getEventIcon(conflict.event_type);
                    return (
                      <div
                        key={conflict.id || i}
                        className="p-3 border-b border-zinc-800/50 hover:bg-zinc-800/30 cursor-pointer transition-colors duration-75"
                        onClick={() => setSelectedConflict(conflict)}
                        data-testid={`conflict-list-item-${i}`}
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
                              <Badge className={`${getSeverityBadgeClass(conflict.severity)} rounded-none text-[9px] px-1 py-0`}>
                                {conflict.severity}/10
                              </Badge>
                            </div>
                          </div>
                          <ChevronRight className="w-4 h-4 text-zinc-600 flex-shrink-0" />
                        </div>
                      </div>
                    );
                  })}
                </ScrollArea>
              </CardContent>
            </Card>
          )}

          {/* Impact Summary */}
          <Card className="nexus-card">
            <CardHeader className="card-header-terminal">
              <CardTitle className="card-header-title flex items-center gap-2">
                <TrendingDown className="w-4 h-4 text-orange-500" />
                Market Impact Summary
              </CardTitle>
            </CardHeader>
            <CardContent className="p-3">
              <div className="space-y-2">
                {['Energy', 'Agriculture', 'Semiconductors', 'Shipping'].map((sector, i) => {
                  const impactedConflicts = conflicts.filter(c => 
                    c.transmission_channels?.some(ch => ch.toLowerCase().includes(sector.toLowerCase()))
                  );
                  const avgImpact = impactedConflicts.length > 0 
                    ? impactedConflicts.reduce((sum, c) => sum + (c.impact_score || 0), 0) / impactedConflicts.length
                    : 0;
                  
                  return (
                    <div key={sector} className="flex items-center justify-between py-1.5">
                      <span className="text-sm text-zinc-400">{sector}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-orange-500 rounded-full"
                            style={{ width: `${avgImpact}%` }}
                          ></div>
                        </div>
                        <span className="font-mono text-xs text-zinc-400 w-8 text-right">
                          {avgImpact.toFixed(0)}
                        </span>
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

export default WorldMapPage;
