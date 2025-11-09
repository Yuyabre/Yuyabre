/**
 * Main API exports
 * 
 * This file re-exports all API modules for convenient importing.
 * Import from here: import { inventoryApi, ordersApi, streamAgentCommand } from '@/lib/api'
 */

// WebSocket/Streaming API
export {
  streamAgentCommand,
  type AgentCommandRequest,
  type AgentCommandStreamCallbacks,
} from "./websocket";

// Inventory API
export { inventoryApi } from "./inventory";

// Orders API
export { ordersApi } from "./orders";

// Expenses API
export { expensesApi } from "./expenses";

// Authentication API
export { authApi } from "./auth";

// Splitwise API
export { splitwiseApi } from "./splitwise";

// Legacy Chat API (kept for compatibility)
import { delay } from "./mocks";

export const chatApi = {
  sendMessage: async (
    _message: string
  ): Promise<{ success: boolean; messageId: string }> => {
    await delay(200);
    // In production, this would send the message to the server
    // The server will process it and send responses via WebSocket
    return {
      success: true,
      messageId: `msg-${Date.now()}`,
    };
  },
};

