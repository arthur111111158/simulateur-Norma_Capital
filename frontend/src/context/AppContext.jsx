import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AppContext = createContext(null);

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used within AppProvider');
  return context;
};

export const AppProvider = ({ children }) => {
  const [watchlist, setWatchlist] = useState([]);
  const [news, setNews] = useState([]);
  const [conflicts, setConflicts] = useState([]);
  const [movers, setMovers] = useState({ gainers: [], losers: [] });
  const [loading, setLoading] = useState(true);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [universe, setUniverse] = useState(null);
  const [earnings, setEarnings] = useState([]);

  // Fetch watchlist
  const fetchWatchlist = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/watchlist`);
      setWatchlist(response.data);
    } catch (error) {
      console.error('Error fetching watchlist:', error);
    }
  }, []);

  // Add to watchlist
  const addToWatchlist = async (symbol, name, assetType) => {
    try {
      await axios.post(`${API}/watchlist`, { symbol, name, asset_type: assetType });
      fetchWatchlist();
    } catch (error) {
      console.error('Error adding to watchlist:', error);
    }
  };

  // Remove from watchlist
  const removeFromWatchlist = async (symbol) => {
    try {
      await axios.delete(`${API}/watchlist/${symbol}`);
      fetchWatchlist();
    } catch (error) {
      console.error('Error removing from watchlist:', error);
    }
  };

  // Fetch news
  const fetchNews = useCallback(async (query = null, country = null) => {
    try {
      const params = new URLSearchParams();
      if (query) params.append('q', query);
      if (country) params.append('country', country);
      const response = await axios.get(`${API}/news?${params.toString()}`);
      setNews(response.data);
    } catch (error) {
      console.error('Error fetching news:', error);
    }
  }, []);

  // Fetch conflicts
  const fetchConflicts = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/conflicts`);
      setConflicts(response.data);
    } catch (error) {
      console.error('Error fetching conflicts:', error);
    }
  }, []);

  // Fetch movers
  const fetchMovers = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/market/movers`);
      setMovers(response.data);
    } catch (error) {
      console.error('Error fetching movers:', error);
    }
  }, []);

  // Get quote
  const getQuote = async (symbol) => {
    try {
      const response = await axios.get(`${API}/market/quote/${symbol}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching quote:', error);
      return null;
    }
  };

  // Get history
  const getHistory = async (symbol, period = '1mo', interval = '1d') => {
    try {
      const response = await axios.get(`${API}/market/history/${symbol}?period=${period}&interval=${interval}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching history:', error);
      return null;
    }
  };

  // Get supply chain
  const getSupplyChain = async (symbol) => {
    try {
      const response = await axios.get(`${API}/supplychain/${symbol}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching supply chain:', error);
      return [];
    }
  };

  // Search assets
  const searchAssets = async (query) => {
    try {
      const response = await axios.get(`${API}/market/search?q=${query}`);
      return response.data.results;
    } catch (error) {
      console.error('Error searching assets:', error);
      return [];
    }
  };

  // Screen assets
  const screenAssets = async (assetType, filters = {}) => {
    try {
      // Only include defined, non-undefined filters
      const cleanFilters = {};
      Object.keys(filters).forEach(key => {
        if (filters[key] !== undefined && filters[key] !== null && filters[key] !== '') {
          cleanFilters[key] = filters[key];
        }
      });
      const params = new URLSearchParams({ asset_type: assetType, ...cleanFilters });
      const response = await axios.get(`${API}/screener?${params.toString()}`);
      return response.data.results || [];
    } catch (error) {
      console.error('Error screening assets:', error);
      return [];
    }
  };

  // Get technical indicators
  const getTechnicalIndicators = async (symbol) => {
    try {
      const response = await axios.get(`${API}/market/technical/${symbol}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching technical indicators:', error);
      return null;
    }
  };

  // Get impact score
  const getImpactScore = async (symbol) => {
    try {
      const response = await axios.get(`${API}/impact/${symbol}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching impact score:', error);
      return null;
    }
  };

  // Get market universe
  const fetchUniverse = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/market/universe`);
      setUniverse(response.data);
      return response.data;
    } catch (error) {
      console.error('Error fetching universe:', error);
      return null;
    }
  }, []);

  // Get indices
  const getIndices = async (region = null) => {
    try {
      const params = region ? `?region=${region}` : '';
      const response = await axios.get(`${API}/market/indices${params}`);
      return response.data.indices || [];
    } catch (error) {
      console.error('Error fetching indices:', error);
      return [];
    }
  };

  // ==================== NEW: SHIPPING DATA ====================
  
  // Get shipping routes
  const getShippingRoutes = async (routeType = 'all') => {
    try {
      const response = await axios.get(`${API}/shipping/routes?route_type=${routeType}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching shipping routes:', error);
      return { routes: [], stats: {} };
    }
  };

  // Get shipping ports
  const getShippingPorts = async () => {
    try {
      const response = await axios.get(`${API}/shipping/ports`);
      return response.data;
    } catch (error) {
      console.error('Error fetching shipping ports:', error);
      return { seaports: [], airports: [] };
    }
  };

  // Get shipping stats
  const getShippingStats = async () => {
    try {
      const response = await axios.get(`${API}/shipping/stats`);
      return response.data;
    } catch (error) {
      console.error('Error fetching shipping stats:', error);
      return null;
    }
  };

  // ==================== NEW: OPTIONS CHAIN ====================
  
  // Get options expirations
  const getOptionsExpirations = async (symbol) => {
    try {
      const response = await axios.get(`${API}/options/expirations/${symbol}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching options expirations:', error);
      return null;
    }
  };

  // Get options chain
  const getOptionsChain = async (symbol, expiration) => {
    try {
      const response = await axios.get(`${API}/options/chain/${symbol}?expiration=${expiration}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching options chain:', error);
      return null;
    }
  };

  // ==================== NEW: EARNINGS CALENDAR ====================
  
  // Fetch earnings calendar
  const fetchEarnings = useCallback(async (days = 30, region = null) => {
    try {
      const params = new URLSearchParams();
      params.append('days', days);
      if (region) params.append('region', region);
      const response = await axios.get(`${API}/earnings/calendar?${params.toString()}`);
      setEarnings(response.data.events || []);
      return response.data;
    } catch (error) {
      console.error('Error fetching earnings:', error);
      return { events: [] };
    }
  }, []);

  // Get earnings for specific symbol
  const getEarningsForSymbol = async (symbol) => {
    try {
      const response = await axios.get(`${API}/earnings/symbol/${symbol}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching earnings for symbol:', error);
      return null;
    }
  };

  // Initial data load
  useEffect(() => {
    const loadInitialData = async () => {
      setLoading(true);
      await Promise.all([
        fetchWatchlist(),
        fetchNews(),
        fetchConflicts(),
        fetchMovers(),
        fetchUniverse()
      ]);
      setLoading(false);
    };
    loadInitialData();
  }, [fetchWatchlist, fetchNews, fetchConflicts, fetchMovers, fetchUniverse]);

  // Auto-refresh data every 60 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchMovers();
      fetchNews();
    }, 60000);
    return () => clearInterval(interval);
  }, [fetchMovers, fetchNews]);

  const value = {
    watchlist,
    news,
    conflicts,
    movers,
    loading,
    selectedAsset,
    universe,
    earnings,
    setSelectedAsset,
    fetchWatchlist,
    addToWatchlist,
    removeFromWatchlist,
    fetchNews,
    fetchConflicts,
    fetchMovers,
    fetchUniverse,
    fetchEarnings,
    getQuote,
    getHistory,
    getSupplyChain,
    searchAssets,
    screenAssets,
    getTechnicalIndicators,
    getImpactScore,
    getIndices,
    getOptionsExpirations,
    getOptionsChain,
    getEarningsForSymbol,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export default AppContext;
