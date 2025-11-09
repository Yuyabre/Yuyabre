import { websocketManager } from "./websocket/manager";
import type {
  AgentCommandRequest,
  AgentCommandStreamCallbacks,
} from "./websocket/types";

export type {
  AgentCommandRequest,
  AgentCommandStreamCallbacks,
} from "./websocket/types";
export { websocketManager } from "./websocket/manager";

/**
 * Stream agent command responses from the backend using WebSocket.
 * Uses a shared WebSocket connection that stays open for all messages.
 *
 * @param request - Command request with command text and optional user_id
 * @param callbacks - Callbacks for handling stream chunks, completion, and errors
 * @param messageId - Unique ID for this message (used for routing responses)
 * @returns A function to cleanup this specific request (doesn't close the connection)
 */
export function streamAgentCommand(
  request: AgentCommandRequest,
  callbacks: AgentCommandStreamCallbacks,
  messageId: string
): () => void {
  return websocketManager.sendCommand(request, callbacks, messageId);
}

