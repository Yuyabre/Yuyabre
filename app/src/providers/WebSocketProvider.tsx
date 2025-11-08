import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from "react";
import type {
  WebSocketMessage,
  MessageWebSocketData,
  MessageStreamWebSocketData,
  OrderStatusUpdateWebSocketData,
  OrderCreatedWebSocketData,
  ErrorWebSocketData,
} from "@/types/websocket";
import type { IMessage } from "@/types/chat";

interface WebSocketContextType {
  isConnected: boolean;
  sendMessage: (message: string) => void;
  onMessage: (callback: (message: IMessage) => void) => void;
  onMessageStream: (callback: (chunk: string, messageId: string, done: boolean) => void) => void;
  onOrderStatusUpdate: (callback: (orderId: string, status: string) => void) => void;
  onOrderCreated: (callback: (order: any) => void) => void;
  onError: (callback: (error: string) => void) => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

interface WebSocketProviderProps {
  children: ReactNode;
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const [isConnected, setIsConnected] = useState(false);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [messageCallbacks, setMessageCallbacks] = useState<Set<(message: IMessage) => void>>(new Set());
  const [streamCallbacks, setStreamCallbacks] = useState<Set<(chunk: string, messageId: string, done: boolean) => void>>(new Set());
  const [orderStatusCallbacks, setOrderStatusCallbacks] = useState<Set<(orderId: string, status: string) => void>>(new Set());
  const [orderCreatedCallbacks, setOrderCreatedCallbacks] = useState<Set<(order: any) => void>>(new Set());
  const [errorCallbacks, setErrorCallbacks] = useState<Set<(error: string) => void>>(new Set());

  useEffect(() => {
    // Mock WebSocket - in production, this would connect to a real WebSocket server
    // For now, we'll simulate WebSocket behavior with a mock
    const mockWs = {
      readyState: WebSocket.OPEN,
      send: (data: string) => {
        // Mock sending - in production, this would send to the server
        console.log("Mock WebSocket send:", data);
      },
      close: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
    } as unknown as WebSocket;

    setWs(mockWs);
    setIsConnected(true);

    // Simulate receiving messages (mock)
    // In production, this would be handled by real WebSocket events

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  const sendMessage = useCallback((message: string) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "message", content: message }));
    }
  }, [ws]);

  const onMessage = useCallback((callback: (message: IMessage) => void) => {
    setMessageCallbacks((prev) => new Set([...prev, callback]));
    return () => {
      setMessageCallbacks((prev) => {
        const next = new Set(prev);
        next.delete(callback);
        return next;
      });
    };
  }, []);

  const onMessageStream = useCallback((callback: (chunk: string, messageId: string, done: boolean) => void) => {
    setStreamCallbacks((prev) => new Set([...prev, callback]));
    return () => {
      setStreamCallbacks((prev) => {
        const next = new Set(prev);
        next.delete(callback);
        return next;
      });
    };
  }, []);

  const onOrderStatusUpdate = useCallback((callback: (orderId: string, status: string) => void) => {
    setOrderStatusCallbacks((prev) => new Set([...prev, callback]));
    return () => {
      setOrderStatusCallbacks((prev) => {
        const next = new Set(prev);
        next.delete(callback);
        return next;
      });
    };
  }, []);

  const onOrderCreated = useCallback((callback: (order: any) => void) => {
    setOrderCreatedCallbacks((prev) => new Set([...prev, callback]));
    return () => {
      setOrderCreatedCallbacks((prev) => {
        const next = new Set(prev);
        next.delete(callback);
        return next;
      });
    };
  }, []);

  const onError = useCallback((callback: (error: string) => void) => {
    setErrorCallbacks((prev) => new Set([...prev, callback]));
    return () => {
      setErrorCallbacks((prev) => {
        const next = new Set(prev);
        next.delete(callback);
        return next;
      });
    };
  }, []);

  // Expose a method to simulate receiving messages (for mock)
  useEffect(() => {
    // This is a mock - in production, WebSocket would handle this
    (window as any).__mockWebSocketReceive = (message: WebSocketMessage) => {
      switch (message.type) {
        case "message":
          messageCallbacks.forEach((cb) => cb((message.data as MessageWebSocketData).message));
          break;
        case "message_stream":
          const streamData = message.data as MessageStreamWebSocketData;
          streamCallbacks.forEach((cb) => cb(streamData.chunk, streamData.messageId, streamData.done));
          break;
        case "order_status_update":
          const statusData = message.data as OrderStatusUpdateWebSocketData;
          orderStatusCallbacks.forEach((cb) => cb(statusData.orderId, statusData.status));
          break;
        case "order_created":
          const orderData = message.data as OrderCreatedWebSocketData;
          orderCreatedCallbacks.forEach((cb) => cb(orderData.order));
          break;
        case "error":
          const errorData = message.data as ErrorWebSocketData;
          errorCallbacks.forEach((cb) => cb(errorData.error));
          break;
      }
    };
  }, [messageCallbacks, streamCallbacks, orderStatusCallbacks, orderCreatedCallbacks, errorCallbacks]);

  return (
    <WebSocketContext.Provider
      value={{
        isConnected,
        sendMessage,
        onMessage,
        onMessageStream,
        onOrderStatusUpdate,
        onOrderCreated,
        onError,
      }}
    >
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error("useWebSocket must be used within WebSocketProvider");
  }
  return context;
}

