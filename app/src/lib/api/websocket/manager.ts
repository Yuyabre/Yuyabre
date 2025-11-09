import { delay, buildWebSocketUrl } from "./utils";
import type {
  AgentCommandRequest,
  AgentCommandStreamCallbacks,
  WebSocketMessage,
} from "./types";

interface PendingRequest {
  request: AgentCommandRequest;
  callbacks: AgentCommandStreamCallbacks;
  messageId: string;
  lastChunkTime?: number;
  chunkQueue?: string[];
  processingQueue?: boolean;
  isComplete?: boolean;
}

const DEFAULT_MIN_CHUNK_DELAY = 30;
const DEFAULT_RECONNECT_DELAY = 1000;
const MAX_RECONNECT_ATTEMPTS = 5;
const COMMAND_STREAM_PATH = "/agent/command/stream";

/**
 * WebSocket Manager - maintains a single persistent WebSocket connection
 * for all agent command requests
 */
export class WebSocketManager {
  private ws: WebSocket | null = null;
  private readonly wsUrl: string;
  private readonly pendingRequests = new Map<string, PendingRequest>();
  private reconnectAttempts = 0;
  private readonly reconnectDelay = DEFAULT_RECONNECT_DELAY;
  private isConnecting = false;
  private readonly minChunkDelay = DEFAULT_MIN_CHUNK_DELAY;

  constructor(path: string = COMMAND_STREAM_PATH) {
    this.wsUrl = buildWebSocketUrl(path);
  }

  /**
   * Get or create WebSocket connection
   */
  private async getConnection(): Promise<WebSocket> {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      return this.ws;
    }

    if (
      this.isConnecting &&
      this.ws &&
      this.ws.readyState === WebSocket.CONNECTING
    ) {
      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error("WebSocket connection timeout"));
        }, 10_000);

        const checkConnection = () => {
          if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            clearTimeout(timeout);
            resolve(this.ws);
          } else if (this.ws && this.ws.readyState === WebSocket.CLOSED) {
            clearTimeout(timeout);
            reject(new Error("WebSocket connection failed"));
          } else {
            setTimeout(checkConnection, 100);
          }
        };

        checkConnection();
      });
    }

    return this.connect();
  }

  /**
   * Connect to WebSocket
   */
  private connect(): Promise<WebSocket> {
    return new Promise((resolve, reject) => {
      this.isConnecting = true;
      this.reconnectAttempts = 0;

      try {
        const ws = new WebSocket(this.wsUrl);
        this.ws = ws;

        ws.onopen = () => {
          console.log("WebSocket connected");
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          resolve(ws);
        };

        ws.onmessage = (event) => {
          this.handleMessage(event);
        };

        ws.onerror = (error) => {
          console.error("WebSocket error:", error);
          this.isConnecting = false;
          if (this.reconnectAttempts === 0) {
            reject(new Error("WebSocket connection error"));
          }
        };

        ws.onclose = (event) => {
          console.log("WebSocket closed", event.code, event.reason);
          this.isConnecting = false;
          this.ws = null;

          if (
            this.pendingRequests.size > 0 &&
            this.reconnectAttempts < MAX_RECONNECT_ATTEMPTS
          ) {
            this.reconnectAttempts++;
            console.log(
              `Attempting to reconnect (${this.reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`,
            );
            setTimeout(() => {
              this.connect().catch((err) => {
                console.error("Reconnection failed:", err);
                this.failAllPendingRequests(
                  new Error("WebSocket reconnection failed"),
                );
              });
            }, this.reconnectDelay * this.reconnectAttempts);
          } else if (this.pendingRequests.size > 0) {
            this.failAllPendingRequests(
              new Error("WebSocket connection lost"),
            );
          }
        };
      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(event: MessageEvent) {
    const rawData = event.data as string;
    const data = this.parseMessage(rawData);

    if (!data) {
      return;
    }

    const targetRequest = this.resolveTargetRequest(data);

    if (!targetRequest) {
      console.warn("Received message but no pending request found", data);
      return;
    }

    if (data.type === "chunk") {
      this.handleChunkMessage(targetRequest, data);
    } else if (data.type === "done") {
      this.handleDoneMessage(targetRequest);
    } else if (data.type === "error") {
      this.handleErrorMessage(targetRequest, data.error);
    } else {
      console.warn("Unknown message type:", data);
      this.handleTextChunk(rawData);
    }
  }

  /**
   * Parse a raw WebSocket message into a structured object.
   */
  private parseMessage(rawData: string): WebSocketMessage | null {
    try {
      const data = JSON.parse(rawData) as WebSocketMessage;
      return data;
    } catch {
      const trimmed = rawData.trim();

      if (trimmed === '{"type":"done"}' || trimmed === "[DONE]") {
        return { type: "done" };
      }

      if (trimmed.startsWith('{"type":"error"')) {
        try {
          return JSON.parse(trimmed) as WebSocketMessage;
        } catch {
          return { type: "error", error: "Unknown error" };
        }
      }

      this.handleTextChunk(rawData);
      return null;
    }
  }

  private resolveTargetRequest(
    data: WebSocketMessage,
  ): PendingRequest | undefined {
    if (data.messageId && this.pendingRequests.has(data.messageId)) {
      return this.pendingRequests.get(data.messageId);
    }

    if (this.pendingRequests.size > 0) {
      const firstKey = this.pendingRequests.keys().next().value;
      if (firstKey) {
        return this.pendingRequests.get(firstKey);
      }
    }

    return undefined;
  }

  private handleChunkMessage(
    targetRequest: PendingRequest,
    data: WebSocketMessage,
  ) {
    if (targetRequest.isComplete) {
      console.warn(
        "Ignoring chunk for completed message:",
        targetRequest.messageId,
      );
      return;
    }

    const content = data.content || "";

    if (content.length === 0) {
      return;
    }

    this.sendChunkWithDelay(targetRequest, content);
  }

  private handleDoneMessage(targetRequest: PendingRequest) {
    targetRequest.isComplete = true;

    this.flushChunkQueue(targetRequest.messageId).then(() => {
      console.log("Stream complete for message:", targetRequest.messageId);
      targetRequest.callbacks.onComplete?.();
      this.pendingRequests.delete(targetRequest.messageId);
    });
  }

  private handleErrorMessage(
    targetRequest: PendingRequest,
    errorMessage?: string,
  ) {
    const err = new Error(errorMessage || "Unknown error occurred");
    targetRequest.callbacks.onError?.(err);
    this.pendingRequests.delete(targetRequest.messageId);
  }

  /**
   * Handle plain text chunks
   */
  private handleTextChunk(text: string) {
    if (!text || !text.trim()) {
      return;
    }

    const trimmed = text.trim();
    if (trimmed === '{"type":"done"}' || trimmed === "[DONE]") {
      const firstKey = this.pendingRequests.keys().next().value;
      if (firstKey) {
        const targetRequest = this.pendingRequests.get(firstKey);
        if (targetRequest) {
          console.log("Stream complete for message:", targetRequest.messageId);
          targetRequest.callbacks.onComplete?.();
          this.pendingRequests.delete(targetRequest.messageId);
        }
      }
      return;
    }

    if (trimmed.startsWith('{"type":"chunk"')) {
      const parsed = this.parseMessage(trimmed);
      if (parsed) {
        const targetRequest = this.resolveTargetRequest(parsed);
        if (targetRequest) {
          this.handleChunkMessage(targetRequest, parsed);
        }
      }
      return;
    }

    if (this.pendingRequests.size > 0) {
      const firstKey = this.pendingRequests.keys().next().value;
      if (firstKey) {
        const targetRequest = this.pendingRequests.get(firstKey);
        if (targetRequest) {
          this.sendChunkWithDelay(targetRequest, text);
        }
      }
    }
  }

  /**
   * Send a chunk with minimum delay between chunks for realistic streaming
   */
  private sendChunkWithDelay(request: PendingRequest, chunk: string) {
    if (request.isComplete) {
      console.warn("Ignoring chunk for completed message:", request.messageId);
      return;
    }

    const now = Date.now();
    const lastChunkTime = request.lastChunkTime || 0;
    const timeSinceLastChunk = now - lastChunkTime;
    const delayNeeded = Math.max(0, this.minChunkDelay - timeSinceLastChunk);

    if (!request.chunkQueue) {
      request.chunkQueue = [];
    }

    request.chunkQueue.push(chunk);

    if (!request.processingQueue) {
      request.processingQueue = true;
      this.processChunkQueue(request, delayNeeded);
    }
  }

  /**
   * Process the chunk queue with delays
   */
  private async processChunkQueue(
    request: PendingRequest,
    initialDelay: number = 0,
  ) {
    if (initialDelay > 0) {
      await delay(initialDelay);
    }

    while (
      request.chunkQueue &&
      request.chunkQueue.length > 0 &&
      !request.isComplete
    ) {
      const chunk = request.chunkQueue.shift();
      if (chunk && !request.isComplete) {
        request.callbacks.onChunk(chunk);
        request.lastChunkTime = Date.now();
      }

      if (
        request.chunkQueue &&
        request.chunkQueue.length > 0 &&
        !request.isComplete
      ) {
        await delay(this.minChunkDelay);
      }
    }

    request.processingQueue = false;
  }

  /**
   * Flush any remaining chunks in the queue for a message
   */
  private async flushChunkQueue(messageId: string): Promise<void> {
    const request = this.pendingRequests.get(messageId);
    if (!request || !request.chunkQueue || request.chunkQueue.length === 0) {
      return;
    }

    while (request.processingQueue) {
      await delay(10);
    }

    while (request.chunkQueue.length > 0) {
      const chunk = request.chunkQueue.shift();
      if (chunk) {
        request.callbacks.onChunk(chunk);
      }
    }
  }

  /**
   * Send a command through the WebSocket connection
   */
  sendCommand(
    request: AgentCommandRequest,
    callbacks: AgentCommandStreamCallbacks,
    messageId: string,
  ): () => void {
    this.pendingRequests.set(messageId, { request, callbacks, messageId });

    this.getConnection()
      .then((ws) => {
        ws.send(
          JSON.stringify({
            command: request.command,
            user_id: request.user_id || "user123",
            messageId,
          }),
        );
      })
      .catch((error) => {
        const err = error instanceof Error ? error : new Error(String(error));
        callbacks.onError?.(err);
        this.pendingRequests.delete(messageId);
      });

    return () => {
      const pending = this.pendingRequests.get(messageId);
      if (pending) {
        pending.isComplete = true;
        if (pending.chunkQueue) {
          pending.chunkQueue = [];
        }
        this.pendingRequests.delete(messageId);
      }
    };
  }

  /**
   * Close the WebSocket connection
   */
  close() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.pendingRequests.clear();
    this.isConnecting = false;
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  private failAllPendingRequests(error: Error) {
    this.pendingRequests.forEach((pending) => {
      pending.callbacks.onError?.(error);
    });
    this.pendingRequests.clear();
  }
}

// Singleton instance
export const websocketManager = new WebSocketManager();

