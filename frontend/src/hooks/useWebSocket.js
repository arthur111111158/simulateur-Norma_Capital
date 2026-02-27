import { useState, useEffect, useCallback, useRef } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const WS_URL = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');

export const useWebSocket = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [quotes, setQuotes] = useState({});
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const subscribedSymbolsRef = useRef(new Set());

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const ws = new WebSocket(`${WS_URL}/ws/quotes`);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        
        // Re-subscribe to symbols if any
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
        console.log('WebSocket disconnected');
        setIsConnected(false);
        wsRef.current = null;
        
        // Reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 5000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Error creating WebSocket:', error);
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const subscribe = useCallback((symbols) => {
    const symbolArray = Array.isArray(symbols) ? symbols : [symbols];
    symbolArray.forEach(s => subscribedSymbolsRef.current.add(s.toUpperCase()));
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'subscribe',
        symbols: symbolArray
      }));
    }
  }, []);

  const unsubscribe = useCallback((symbols) => {
    const symbolArray = Array.isArray(symbols) ? symbols : [symbols];
    symbolArray.forEach(s => subscribedSymbolsRef.current.delete(s.toUpperCase()));
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'unsubscribe',
        symbols: symbolArray
      }));
    }
  }, []);

  const getQuote = useCallback((symbol) => {
    return quotes[symbol.toUpperCase()];
  }, [quotes]);

  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    quotes,
    subscribe,
    unsubscribe,
    getQuote,
    connect,
    disconnect
  };
};

export default useWebSocket;
