import { streamAgentCommand, type AgentCommandStreamCallbacks } from '@/lib/api';
import type { IMessage } from '@/types/chat';
import { MessageRole, MessageType } from '@/types/chat';

export interface SendMessageCallbacks {
  onStreamStart?: (messageId: string, cleanup: () => void) => void;
  onChunk?: (messageId: string, chunk: string) => void;
  onComplete?: (messageId: string, finalContent: string) => void;
  onError?: (messageId: string, error: Error) => void;
}

export function useActions() {
  const sendMessage = (
    input: string,
    callbacks?: SendMessageCallbacks
  ): void => {
    // Generate unique message ID with timestamp + random to avoid collisions
    const messageId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    // Use the streaming agent command API
    let accumulatedContent = '';

    const streamCallbacks: AgentCommandStreamCallbacks = {
      onChunk: (chunk: string) => {
        accumulatedContent += chunk;
        console.log("Stream chunk received:", chunk, "Total:", accumulatedContent);
        callbacks?.onChunk?.(messageId, chunk);
      },
      onComplete: () => {
        console.log("Stream complete for message:", messageId, "Content:", accumulatedContent);
        callbacks?.onComplete?.(messageId, accumulatedContent);
      },
      onError: (error: Error) => {
        console.error("Stream error:", error);
        callbacks?.onError?.(messageId, error);
      },
    };

    try {
      // streamAgentCommand returns a cleanup function
      // Pass messageId so the WebSocket manager can route responses
      const cleanup = streamAgentCommand(
        {
          command: input,
          user_id: 'user123', // TODO: Get from user session/store
        },
        streamCallbacks,
        messageId
      );
      
      // Call onStreamStart with both messageId and cleanup function
      callbacks?.onStreamStart?.(messageId, cleanup);
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      streamCallbacks.onError?.(err);
    }
  };

  return { sendMessage };
}

