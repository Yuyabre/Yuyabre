export interface InventoryItem {
  _id?: string | null;
  item_id: string;
  name: string;
  category: string;
  quantity: number;
  unit: string;
  threshold: number;
  last_updated: string;
  expiration_date?: string | null;
  shared: boolean;
  user_id?: string | null;
  household_id?: string | null;
  brand?: string | null;
  price?: number | null;
  notes?: string | null;
}

export interface InventoryItemCreate {
  name: string;
  category: string;
  quantity: number;
  unit: string;
  threshold?: number;
  shared?: boolean;
  brand?: string | null;
  price?: number | null;
}

export interface InventoryItemUpdate {
  quantity?: number | null;
  threshold?: number | null;
  notes?: string | null;
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
