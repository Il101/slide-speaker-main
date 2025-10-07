/**
 * WebSocket Hook for Real-Time Progress Updates
 * 
 * Connects to backend WebSocket endpoint and receives progress updates
 * for lesson processing.
 */
import { useEffect, useRef, useState, useCallback } from 'react';

export interface ProgressMessage {
  type: 'progress' | 'completion' | 'error' | 'slide_update' | 'connected';
  lesson_id: string;
  stage?: string;
  percent?: number;
  message?: string;
  current_slide?: number;
  total_slides?: number;
  eta_seconds?: number;
  eta_formatted?: string;
  success?: boolean;
  result?: any;
  error_type?: string;
  error_message?: string;
  slide_number?: number;
  status?: string;
  timestamp?: string;
}

interface UseWebSocketOptions {
  lessonId: string;
  token?: string;
  onProgress?: (data: ProgressMessage) => void;
  onCompletion?: (data: ProgressMessage) => void;
  onError?: (data: ProgressMessage) => void;
  onSlideUpdate?: (data: ProgressMessage) => void;
  autoConnect?: boolean;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  lastMessage: ProgressMessage | null;
  error: string | null;
  connect: () => void;
  disconnect: () => void;
  sendPing: () => void;
}

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export const useWebSocket = ({
  lessonId,
  token,
  onProgress,
  onCompletion,
  onError,
  onSlideUpdate,
  autoConnect = true,
}: UseWebSocketOptions): UseWebSocketReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<ProgressMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 3000;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    try {
      // Build WebSocket URL
      const url = new URL(`${WS_BASE_URL}/api/ws/progress/${lessonId}`);
      if (token) {
        url.searchParams.append('token', token);
      }

      console.log('Connecting to WebSocket:', url.toString());
      const ws = new WebSocket(url.toString());

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data: ProgressMessage = JSON.parse(event.data);
          console.log('WebSocket message:', data);
          
          setLastMessage(data);

          // Route message to appropriate handler
          switch (data.type) {
            case 'progress':
              onProgress?.(data);
              break;
            case 'completion':
              onCompletion?.(data);
              break;
            case 'error':
              onError?.(data);
              break;
            case 'slide_update':
              onSlideUpdate?.(data);
              break;
            case 'connected':
              console.log('WebSocket connection confirmed');
              break;
            default:
              console.log('Unknown message type:', data.type);
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        setIsConnected(false);

        // Attempt reconnection if not closed intentionally
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1;
          console.log(
            `Reconnecting... (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`
          );
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectDelay);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          setError('Failed to connect after multiple attempts');
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setError('Failed to create WebSocket connection');
    }
  }, [lessonId, token, onProgress, onCompletion, onError, onSlideUpdate]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      console.log('Disconnecting WebSocket');
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }

    setIsConnected(false);
  }, []);

  const sendPing = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('Sending ping');
      wsRef.current.send('ping');
    }
  }, []);

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  // Keepalive ping every 30 seconds
  useEffect(() => {
    if (!isConnected) return;

    const pingInterval = setInterval(() => {
      sendPing();
    }, 30000);

    return () => {
      clearInterval(pingInterval);
    };
  }, [isConnected, sendPing]);

  return {
    isConnected,
    lastMessage,
    error,
    connect,
    disconnect,
    sendPing,
  };
};
