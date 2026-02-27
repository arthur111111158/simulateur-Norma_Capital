import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const WS_URL = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');

export const useWebSocket = (pollingInterval = 10000) => {
  const [isConnected, setIsConnected] = useState(false);
  const [quotes, setQuotes] = useState({});
  const [usePolling, setUsePolling] = useState(true); // Default to polling for reliability
  const wsRef = useRef(null);
  const pollingRef = useRef(null);
  const subscribedSymbolsRef = useRef(new Set());

  // Polling fallback for environments where WebSocket doesn't work
  const fetchQuotes = useCallback(async () => {
    const symbols = Array.from(subscribedSymbolsRef.current);
    if (symbols.length === 0) return;

    try {
      const promises = symbols.map(symbol => 
        axios.get(`${API}/market/quote/${symbol}`).catch(() => null)
      );
      const responses = await Promise.all(promises);
      
      const newQuotes = {};
      responses.forEach((response, index) => {
        if (response?.data) {
          newQuotes[symbols[index]] = response.data;
        }
      });
      
      setQuotes(prev => ({ ...prev, ...newQuotes }));
      setIsConnected(true);
    } catch (error) {
      console.error('Error fetching quotes:', error);
    }
  }, []);

  // Start polling
  const startPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }
    
    // Fetch immediately
    fetchQuotes();
    
    // Then poll at interval
    pollingRef.current = setInterval(fetchQuotes, pollingInterval);
    setIsConnected(true);
  }, [fetchQuotes, pollingInterval]);

  // Stop polling
  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  // Try WebSocket connection (optional, may fail in some environments)
  const tryWebSocket = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return true;
    }

    try {
      const ws = new WebSocket(`${WS_URL}/ws/quotes`);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setUsePolling(false);
        stopPolling();
        
        // Re-subscribe to symbols
        if (subscribedSymbolsRef.current.size > 0) {
          ws.send(JSON.stringify({
            action: 'subscribe',
            symbols: Array.from(subscribedSymbolsRef.current)
          }));
        }
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'quote_update' && message.data) {
            setQuotes(prev => ({
              ...prev,
              [message.data.symbol]: message.data
            }));
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected, falling back to polling');
        wsRef.current = null;
        setUsePolling(true);
        startPolling();
      };

      ws.onerror = () => {
        console.log('WebSocket error, using polling instead');
        setUsePolling(true);
        startPolling();
      };

      wsRef.current = ws;
      
      // Set timeout for WebSocket connection
      setTimeout(() => {
        if (wsRef.current?.readyState !== WebSocket.OPEN) {
          wsRef.current?.close();
          setUsePolling(true);
          startPolling();
        }
      }, 5000);
      
      return true;
    } catch (error) {
      console.log('WebSocket not available, using polling');
      setUsePolling(true);
      startPolling();
      return false;
    }
  }, [startPolling, stopPolling]);

  const subscribe = useCallback((symbols) => {
    const symbolArray = Array.isArray(symbols) ? symbols : [symbols];
    symbolArray.forEach(s => subscribedSymbolsRef.current.add(s.toUpperCase()));
    
    if (!usePolling && wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'subscribe',
        symbols: symbolArray
      }));
    } else if (usePolling) {
      // Fetch immediately when subscribing in polling mode
      fetchQuotes();
    }
  }, [usePolling, fetchQuotes]);

  const unsubscribe = useCallback((symbols) => {
    const symbolArray = Array.isArray(symbols) ? symbols : [symbols];
    symbolArray.forEach(s => subscribedSymbolsRef.current.delete(s.toUpperCase()));
    
    if (!usePolling && wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'unsubscribe',
        symbols: symbolArray
      }));
    }
  }, [usePolling]);

  const getQuote = useCallback((symbol) => {
    return quotes[symbol.toUpperCase()];
  }, [quotes]);

  const disconnect = useCallback(() => {
    stopPolling();
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, [stopPolling]);

  // Initialize - start with polling (more reliable)
  useEffect(() => {
    startPolling();
    
    // Optionally try WebSocket after a delay
    const wsTimeout = setTimeout(() => {
      tryWebSocket();
    }, 2000);
    
    return () => {
      clearTimeout(wsTimeout);
      disconnect();
    };
  }, [startPolling, tryWebSocket, disconnect]);

  return {
    isConnected,
    quotes,
    subscribe,
    unsubscribe,
    getQuote,
    usePolling,
    disconnect
  };
};

export default useWebSocket;
