export interface OrderItem {
  product_id: string;
  name: string;
  quantity: number;
  unit: string;
  price: number;
  total_price: number;
  requested_by: string[];
}

export type OrderStatus =
  | "pending"
  | "confirmed"
  | "processing"
  | "out_for_delivery"
  | "delivered"
  | "cancelled"
  | "failed";

export interface Order {
  _id?: string | null;
  order_id: string;
  timestamp: string;
  service: string;
  items: OrderItem[];
  subtotal: number;
  delivery_fee: number;
  total: number;
  delivery_time: string | null;
  delivery_address: string | null;
  status: OrderStatus;
  external_order_id: string | null;
  splitwise_expense_id: string | null;
  notes: string | null;
  created_by: string | null;
  is_group_order: boolean;
  household_id: string | null;
  pending_responses?: Record<string, string[]>;
  response_deadline?: string | null;
  group_responses?: Record<string, Record<string, unknown>>;
  whatsapp_message_sent: boolean;
}

export interface OrderData {
  items: OrderItem[];
  total: number;
}
