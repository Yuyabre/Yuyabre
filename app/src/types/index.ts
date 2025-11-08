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

export interface OrderItem {
  name: string;
  quantity: number;
  price: number;
}

export interface Order {
  id: string;
  timestamp: string;
  service: string;
  items: OrderItem[];
  total: number;
  deliveryTime: string | null;
  status: "pending" | "preparing" | "delivering" | "delivered";
  splitwiseExpenseId: string | null;
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

export interface OrderData {
  items: OrderItem[];
  total: number;
}

export type StreamChunk =
  | { type: "status"; message: string; progress: number }
  | { type: "order"; data: Order; progress: number }
  | { type: "complete"; order: Order; expense: Expense; progress: number };

export type ViewId = "chat" | "inventory" | "orders" | "expenses";
