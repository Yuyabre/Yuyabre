export interface AgentCommandRequest {
  command: string;
  user_id?: string;
}

export interface AgentCommandStreamCallbacks {
  onChunk: (chunk: string) => void;
  onComplete?: () => void;
  onError?: (error: Error) => void;
}

export interface WebSocketMessage {
  type: string;
  messageId?: string;
  content?: string;
  error?: string;
}

