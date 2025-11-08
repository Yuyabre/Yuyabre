export interface InventoryItem {
  id: string;
  name: string;
  category: string;
  quantity: number;
  unit: string;
  threshold: number;
  expirationDate?: string;
  shared: boolean;
  lastUpdated?: string;
}

export interface Expense {
  id: string;
  description: string;
  amount: number;
  splitAmount: number;
  status: "pending" | "settled";
  orderId: string;
  createdAt: string;
}

import type { Order } from "./orders";

export type StreamChunk =
  | { type: "status"; message: string; progress: number }
  | { type: "order"; data: Order; progress: number }
  | { type: "complete"; order: Order; expense: Expense; progress: number };

export type ViewId = "chat" | "inventory" | "orders" | "expenses";
